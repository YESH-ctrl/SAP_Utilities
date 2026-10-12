import hashlib
import re
import logging
from typing import List, Tuple, Optional
from bs4 import BeautifulSoup, Tag

from sap_rag.crawler.models import ParsedDocument, ParsedSection
from sap_rag.crawler.url_normalizer import URLNormalizer

logger = logging.getLogger(__name__)

class ContentParser:
    """
    Parses main documentation content, page title, breadcrumbs, semantic sections,
    and HTML tables from SAP Help Portal pages.
    """

    NOISE_SELECTORS = [
        "header",
        "footer",
        "nav.breadcrumb",
        "nav.breadcrumbs",
        "div.cookie-banner",
        "div.cookie-consent",
        "div.feedback-widget",
        "div.social-share",
        "div.sap-header",
        "div.sap-footer",
        "aside",
        "script",
        "style",
        "iframe",
        ".noprint",
    ]

    MAIN_CONTENT_SELECTORS = [
        "main",
        "article",
        "div.topic",
        "div.help-content",
        "div.body",
        "div.content",
        "div#content",
        "div.page-content",
    ]

    @classmethod
    def parse_document(cls, html: str, url: str) -> ParsedDocument:
        soup = BeautifulSoup(html, "lxml")
        canonical_url = URLNormalizer.get_canonical_url(url)

        # 1. Extract Title BEFORE cleaning noise
        title = cls._extract_title(soup)

        # 2. Extract Breadcrumbs
        breadcrumbs = cls._extract_breadcrumbs(soup)

        # 3. Clean Noise DOM elements
        cls._clean_noise(soup)

        # 4. Extract Main Content Container
        content_container = cls._extract_main_container(soup)

        # 5. Convert Tables to Markdown before text extraction
        cls._convert_tables_to_markdown(content_container)

        # 6. Extract Semantic Sections (Headings + Body Text)
        sections, clean_text = cls._extract_sections_and_clean_text(content_container)

        # 7. Compute Content SHA-256 Hash
        content_hash = hashlib.sha256(clean_text.encode("utf-8")).hexdigest()

        return ParsedDocument(
            title=title,
            url=url,
            canonical_url=canonical_url,
            content=clean_text,
            content_hash=content_hash,
            breadcrumbs=breadcrumbs,
            sections=sections,
        )

    @classmethod
    def _extract_title(cls, soup: BeautifulSoup) -> str:
        # Priority 1: Page <title> tag if valid and specific
        title_tag = soup.find("title")
        if title_tag and title_tag.get_text(strip=True):
            raw_title = title_tag.get_text(strip=True)
            clean_title = re.sub(r"\s*\|\s*SAP\s+Help\s+Portal.*$", "", raw_title, flags=re.IGNORECASE).strip()
            clean_title = re.sub(r"\s*\|\s*SAP\s+Online\s+Help.*$", "", clean_title, flags=re.IGNORECASE).strip()
            if clean_title and clean_title.lower() not in ("sap help portal", "sap online help"):
                return clean_title

        # Priority 2: h1 inside main/article (excluding header product title)
        main = soup.find(["main", "article", "div.topic", "div.help-content"])
        if main:
            for h1 in main.find_all("h1"):
                text = h1.get_text(strip=True)
                classes = [c.lower() for c in h1.get("class", [])]
                if text and not any(k in classes for k in ("header", "product", "banner")):
                    return text

        # Priority 3: First h1 not inside header/nav
        for h1 in soup.find_all("h1"):
            if not h1.find_parent(["header", "nav"]):
                text = h1.get_text(strip=True)
                if text:
                    return text

        return "SAP Documentation Topic"

    @classmethod
    def _extract_breadcrumbs(cls, soup: BeautifulSoup) -> List[str]:
        breadcrumbs = []
        bc_nav = soup.find("nav", class_=lambda c: c and "breadcrumb" in c.lower()) or soup.find(class_="breadcrumbs")
        if bc_nav:
            for item in bc_nav.find_all(["a", "li", "span"]):
                text = item.get_text(strip=True)
                if text and text not in breadcrumbs and text not in (">", "/", "→", "|"):
                    breadcrumbs.append(text)
        return breadcrumbs

    @classmethod
    def _clean_noise(cls, soup: BeautifulSoup):
        for selector in cls.NOISE_SELECTORS:
            for node in soup.select(selector):
                node.decompose()

    @classmethod
    def _extract_main_container(cls, soup: BeautifulSoup) -> Tag:
        for selector in cls.MAIN_CONTENT_SELECTORS:
            container = soup.select_one(selector)
            if container:
                return container
        return soup.body or soup

    @classmethod
    def _convert_tables_to_markdown(cls, container: Tag):
        for table in container.find_all("table"):
            rows = table.find_all("tr")
            if not rows:
                table.decompose()
                continue

            md_rows = []
            headers_extracted = False

            for tr in rows:
                headers = [th.get_text(strip=True) for th in tr.find_all("th")]
                if headers:
                    md_rows.append("| " + " | ".join(headers) + " |")
                    md_rows.append("| " + " | ".join(["---"] * len(headers)) + " |")
                    headers_extracted = True
                else:
                    cells = [td.get_text(strip=True) for td in tr.find_all("td")]
                    if cells:
                        if not headers_extracted and len(md_rows) == 0:
                            md_rows.append("| " + " | ".join([f"Col {i+1}" for i in range(len(cells))]) + " |")
                            md_rows.append("| " + " | ".join(["---"] * len(cells)) + " |")
                            headers_extracted = True
                        md_rows.append("| " + " | ".join(cells) + " |")

            if md_rows:
                markdown_table_text = "\n\n" + "\n".join(md_rows) + "\n\n"
                table.replace_with(BeautifulSoup(f"<pre class='md-table'>{markdown_table_text}</pre>", "html.parser"))

    @classmethod
    def _extract_sections_and_clean_text(cls, container: Tag) -> Tuple[List[ParsedSection], str]:
        sections: List[ParsedSection] = []
        full_text_blocks: List[str] = []

        current_heading = "Overview"
        current_level = 1
        current_text_lines: List[str] = []
        section_order = 0

        headings = container.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])

        if not headings:
            text = container.get_text(separator="\n", strip=True)
            sections.append(
                ParsedSection(
                    heading="Main Content",
                    content=text,
                    level=1,
                    section_order=0,
                )
            )
            return sections, text

        for elem in container.descendants:
            if isinstance(elem, Tag) and elem.name in ("h1", "h2", "h3", "h4", "h5", "h6"):
                if current_text_lines:
                    sec_text = "\n".join(current_text_lines).strip()
                    if sec_text:
                        sections.append(
                            ParsedSection(
                                heading=current_heading,
                                content=sec_text,
                                level=current_level,
                                section_order=section_order,
                            )
                        )
                        full_text_blocks.append(f"## {current_heading}\n{sec_text}")
                        section_order += 1
                        current_text_lines = []

                current_heading = elem.get_text(strip=True)
                current_level = int(elem.name[1])
            elif isinstance(elem, Tag) and elem.name in ("p", "ul", "ol", "li", "div", "pre"):
                if not elem.find(["p", "ul", "ol", "div", "pre"]):
                    txt = elem.get_text(strip=True)
                    if txt:
                        current_text_lines.append(txt)

        if current_text_lines:
            sec_text = "\n".join(current_text_lines).strip()
            if sec_text:
                sections.append(
                    ParsedSection(
                        heading=current_heading,
                        content=sec_text,
                        level=current_level,
                        section_order=section_order,
                    )
                )
                full_text_blocks.append(f"## {current_heading}\n{sec_text}")

        clean_full_text = "\n\n".join(full_text_blocks)
        return sections, clean_full_text
