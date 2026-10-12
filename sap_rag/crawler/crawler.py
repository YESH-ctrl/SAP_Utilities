import os
import logging
from typing import Dict, Any, Optional, List
import asyncpg

from sap_rag.crawler.config import settings
from sap_rag.crawler.fetcher import HTTPFetcher
from sap_rag.crawler.robots import RobotsChecker
from sap_rag.crawler.url_normalizer import URLNormalizer
from sap_rag.crawler.toc_parser import TOCParser
from sap_rag.crawler.content_parser import ContentParser
from sap_rag.crawler.link_classifier import LinkClassifier
from sap_rag.crawler.models import ParsedDocument, ParsedTOC, DiscoveredLink, LinkType
from sap_rag.crawler.exceptions import FetchException, RobotsDisallowedException, RateLimitException

from sap_rag.database.repositories.source_repository import SourceRepository
from sap_rag.database.repositories.document_repository import DocumentRepository
from sap_rag.database.repositories.document_link_repository import DocumentLinkRepository
from sap_rag.database.repositories.crawl_job_repository import CrawlJobRepository
from sap_rag.database.repositories.section_repository import SectionRepository
from sap_rag.database.repositories.error_repository import ErrorRepository

logger = logging.getLogger(__name__)

class CrawlProcessor:
    """
    Core deterministic page crawler implementing the 17-step processing pipeline.
    """
    def __init__(self, fetcher: Optional[HTTPFetcher] = None, robots_checker: Optional[RobotsChecker] = None):
        self.fetcher = fetcher or HTTPFetcher()
        self.robots_checker = robots_checker or RobotsChecker()

        os.makedirs(settings.STORAGE_RAW_DIR, exist_ok=True)
        os.makedirs(settings.STORAGE_CLEANED_DIR, exist_ok=True)

    async def process_job(
        self,
        conn: asyncpg.Connection,
        job: Dict[str, Any],
        dry_run: bool = False
    ) -> Dict[str, Any]:
        job_id = job["id"]
        source_id = job.get("source_id")
        url = job["url"]
        parent_document_id = job.get("parent_document_id")
        depth = job.get("depth", 0)

        logger.info(f"Processing CrawlJob #{job_id} [depth={depth}]: {url}")

        if not await self.robots_checker.is_allowed(url):
            logger.warning(f"Robots.txt disallowed URL: {url}")
            if not dry_run:
                await CrawlJobRepository.mark_failed_or_retry(conn, job_id, "Robots.txt disallowed", max_attempts=1)
                await ErrorRepository.log_error(conn, job_id, url, "RobotsDisallowed", "Crawling forbidden by robots.txt")
            raise RobotsDisallowedException(url)

        try:
            raw_html, final_url, used_playwright = await self.fetcher.fetch(url)
        except Exception as e:
            logger.error(f"Fetch failed for job #{job_id} ({url}): {e}")
            if not dry_run:
                http_status = getattr(e, "http_status", None)
                await CrawlJobRepository.mark_failed_or_retry(conn, job_id, str(e), max_attempts=job.get("max_attempts", 3))
                await ErrorRepository.log_error(conn, job_id, url, type(e).__name__, str(e), http_status=http_status, attempt_number=job.get("attempts", 0) + 1)
            raise e

        canonical_url = URLNormalizer.get_canonical_url(final_url or url)
        parsed_doc: ParsedDocument = ContentParser.parse_document(raw_html, canonical_url)

        # Extract Structured TOC ONLY for Root Document (depth == 0)
        if depth == 0:
            parsed_toc: ParsedTOC = TOCParser.parse_toc(raw_html, canonical_url)
            if len(parsed_toc.nodes) > settings.CRAWLER_MAX_ROOT_TOC_NODES:
                sample_titles = [n.title for n in parsed_toc.nodes[:5]]
                logger.warning(
                    f"ROOT_TOC_SUSPICIOUS: source_id={source_id}, root_url={canonical_url}, "
                    f"node_count={len(parsed_toc.nodes)}, sample_titles={sample_titles}"
                )
        else:
            parsed_toc = ParsedTOC(root_title=parsed_doc.title, root_canonical_url=canonical_url)

        parsed_doc.parsed_toc = parsed_toc

        toc_children_links = [
            DiscoveredLink(
                target_url=node.canonical_url,
                canonical_url=node.canonical_url,
                link_text=node.title,
                link_type=LinkType.TOC_CHILD,
                is_internal=True,
                title=node.title,
            )
            for node in parsed_toc.nodes
        ]
        parsed_doc.toc_children = toc_children_links

        classified_links: List[DiscoveredLink] = LinkClassifier.classify_and_extract_links(raw_html, canonical_url, toc_links=toc_children_links)
        parsed_doc.discovered_links = classified_links

        source_pdf = None
        root_document_id = None
        if source_id and not dry_run:
            source = await SourceRepository.get_by_id(conn, source_id)
            if source:
                source_pdf = source.get("source_file")

        if parent_document_id and not dry_run:
            parent_doc = await DocumentRepository.get_by_id(conn, parent_document_id)
            if parent_doc:
                root_document_id = parent_doc.get("root_document_id") or parent_doc.get("id")

        # Save local storage snapshots
        doc_filename_base = f"doc_job_{job_id}"
        raw_path = os.path.join(settings.STORAGE_RAW_DIR, f"{doc_filename_base}.html")
        cleaned_path = os.path.join(settings.STORAGE_CLEANED_DIR, f"{doc_filename_base}.md")

        with open(raw_path, "w", encoding="utf-8") as f:
            f.write(raw_html)

        with open(cleaned_path, "w", encoding="utf-8") as f:
            f.write(f"# {parsed_doc.title}\n\nURL: {canonical_url}\n\n{parsed_doc.content}")

        # DRY RUN EXIT (Zero DB Writes)
        if dry_run:
            logger.info(f"DRY RUN completed for {url}. No database writes performed.")
            return {
                "dry_run": True,
                "job_id": job_id,
                "title": parsed_doc.title,
                "canonical_url": canonical_url,
                "content_length": len(parsed_doc.content),
                "sections_count": len(parsed_doc.sections),
                "parsed_toc": parsed_toc,
                "used_playwright": used_playwright,
                "classified_links_count": len(classified_links),
            }

        # Single Database Transaction for Ingestion
        async with conn.transaction():
            doc_type = "root" if depth == 0 else ("section" if len(parsed_toc.nodes) > 0 else "article")

            saved_doc = await DocumentRepository.upsert_document(
                conn,
                source_id=source_id,
                parent_id=parent_document_id,
                root_document_id=root_document_id,
                title=parsed_doc.title,
                url=url,
                canonical_url=canonical_url,
                source_pdf=source_pdf,
                depth=depth,
                document_type=doc_type,
                content=parsed_doc.content,
                content_hash=parsed_doc.content_hash,
                status="crawled",
                metadata={
                    "breadcrumbs": parsed_doc.breadcrumbs,
                    "used_playwright": used_playwright,
                    "toc_nodes_count": len(parsed_toc.nodes),
                }
            )

            document_id = saved_doc["id"]

            if depth == 0 and not root_document_id:
                await conn.execute("UPDATE documents SET root_document_id = $1 WHERE id = $1;", document_id)
                root_document_id = document_id

            sections_data = [
                {
                    "heading": sec.heading,
                    "content": sec.content,
                    "level": sec.level,
                    "section_order": sec.section_order,
                    "metadata": sec.metadata,
                }
                for sec in parsed_doc.sections
            ]
            await SectionRepository.replace_sections_for_document(conn, document_id, sections_data)

            db_links = [
                {
                    "source_document_id": document_id,
                    "target_url": link.canonical_url,
                    "link_text": link.link_text,
                    "link_type": link.link_type.value,
                    "is_internal": link.is_internal,
                    "is_crawled": False,
                }
                for link in classified_links
            ]
            await DocumentLinkRepository.bulk_insert_links(conn, db_links)

            # Schedule Child Jobs & Pre-upsert Child Documents with Clean Titles from TOC (Root Page Only)
            child_jobs_created = 0
            if depth == 0 and parsed_toc.nodes and len(parsed_toc.nodes) <= settings.CRAWLER_MAX_ROOT_TOC_NODES:
                url_to_doc_id = {canonical_url: document_id}
                url_to_doc_depth = {canonical_url: 0}

                for node in parsed_toc.nodes:
                    parent_doc_id = url_to_doc_id.get(node.parent_canonical_url, document_id)
                    parent_doc_depth = url_to_doc_depth.get(node.parent_canonical_url, 0)
                    child_depth = parent_doc_depth + 1

                    # Pre-create child document shell with title from TOC
                    child_doc = await DocumentRepository.upsert_document(
                        conn,
                        source_id=source_id,
                        parent_id=parent_doc_id,
                        root_document_id=root_document_id or document_id,
                        title=node.title,
                        url=node.canonical_url,
                        canonical_url=node.canonical_url,
                        source_pdf=source_pdf,
                        depth=child_depth,
                        document_type="section" if child_depth == 1 else "article",
                        status="pending",
                    )

                    if child_doc:
                        url_to_doc_id[node.canonical_url] = child_doc["id"]
                        url_to_doc_depth[node.canonical_url] = child_depth

                    child_job_id = await CrawlJobRepository.schedule_child_job(
                        conn,
                        source_id=source_id,
                        url=node.canonical_url,
                        parent_document_id=parent_doc_id,
                        depth=child_depth,
                        priority=max(1, 10 - child_depth),
                    )
                    if child_job_id:
                        child_jobs_created += 1

            await CrawlJobRepository.mark_success(conn, job_id, document_id=document_id)

        logger.info(f"Successfully processed CrawlJob #{job_id} -> Doc ID #{document_id} ({parsed_doc.title}). Created {child_jobs_created} child jobs.")
        return {
            "dry_run": False,
            "job_id": job_id,
            "document_id": document_id,
            "title": parsed_doc.title,
            "canonical_url": canonical_url,
            "depth": depth,
            "child_jobs_created": child_jobs_created,
        }
