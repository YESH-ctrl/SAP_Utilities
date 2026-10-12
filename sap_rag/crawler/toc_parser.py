import logging
from typing import List, Optional, Set, Tuple
from bs4 import BeautifulSoup, Tag

from sap_rag.crawler.models import TOCNode, ParsedTOC, LinkType, DiscoveredLink
from sap_rag.crawler.url_normalizer import URLNormalizer

logger = logging.getLogger(__name__)

class TOCParser:
    """
    Production-grade SAP Help Portal TOC & Hierarchy Parser.
    Targets DOM sidebar containers (`div.sidebar`, `li.toc-item`) and preserves nesting levels.
    """

    FALSE_POSITIVE_TITLES = {
        "sap help portal",
        "sap online help",
        "home",
        "log on",
        "login",
        "sign in",
        "search",
        "feedback",
        "privacy",
        "legal",
        "cookie",
        "terms of use",
        "copyright",
        "trademarks",
        "contact us",
        "help",
    }

    TOC_SIDEBAR_SELECTORS = [
        "div.sidebar-wrapper",
        "div.sidebar",
        "nav.sap-toc",
        "div[role='tree']",
        "aside.toc",
        ".toc-container",
    ]

    @classmethod
    def parse_toc(cls, html: str, base_url: str) -> ParsedTOC:
        """
        Extract structured ParsedTOC tree representation from SAP Help Portal HTML.
        """
        if not html:
            return ParsedTOC(root_title="Documentation Root", root_canonical_url=URLNormalizer.get_canonical_url(base_url))

        soup = BeautifulSoup(html, "lxml")
        root_canonical = URLNormalizer.get_canonical_url(base_url)

        # 1. Extract Root Page Title
        h1 = soup.find("h1")
        root_title = h1.get_text(strip=True) if h1 and h1.get_text(strip=True) else "Documentation Root"

        # 2. Locate Sidebar Container
        sidebar: Optional[Tag] = None
        for selector in cls.TOC_SIDEBAR_SELECTORS:
            sidebar = soup.select_one(selector)
            if sidebar and sidebar.find_all("li", class_=lambda c: c and "toc-item" in str(c).lower()):
                break

        # Fallback to entire soup if no specific sidebar container found
        search_root: Tag = sidebar or soup

        # 2b. Active Container Scoping Strategy
        if sidebar:
            active_a = sidebar.find("a", class_=lambda c: c and any(k in str(c).lower() for k in ["active", "w-current-page", "current"]))
            if not active_a:
                active_el = sidebar.find(class_=lambda c: c and any(k in str(c).lower() for k in ["active", "selected", "w-current-page"]))
                if active_el:
                    active_a = active_el if active_el.name == "a" else active_el.find("a")

            if active_a:
                active_li = active_a.find_parent("li", class_=lambda c: c and "toc-item" in str(c).lower())
                if active_li:
                    sub_items_in_active = active_li.find_all("li", class_=lambda c: c and "toc-item" in str(c).lower())
                    if len(sub_items_in_active) > 0:
                        # Case A: Active <li> contains sub-items (e.g., Source 26 'Dunning' -> 31 nodes)
                        search_root = active_li
                    else:
                        # Case B: Active <li> has no sub-items inside itself; check closest ancestor <li> with sub-items <= 300
                        parent_lis = active_li.find_parents("li", class_=lambda c: c and "toc-item" in str(c).lower())
                        chosen_ancestor = None
                        for p_li in parent_lis:
                            subs = p_li.find_all("li", class_=lambda c: c and "toc-item" in str(c).lower())
                            if 0 < len(subs) <= 300:
                                chosen_ancestor = p_li
                                break

                        if chosen_ancestor:
                            search_root = chosen_ancestor
                        else:
                            # Case C: Check multi-module top_lis (Source 11 vs Source 1)
                            top_ul = sidebar.find("ul")
                            if top_ul:
                                top_lis = top_ul.find_all("li", recursive=False)
                                if len(top_lis) > 1:
                                    target_top_li = None
                                    for li in top_lis:
                                        if active_a in li.descendants or active_a == li:
                                            target_top_li = li
                                            break
                                    if target_top_li:
                                        sub_in_top = target_top_li.find_all("li", class_=lambda c: c and "toc-item" in str(c).lower())
                                        if len(sub_in_top) > 0:
                                            search_root = target_top_li

        search_root_ul_parents = len([p for p in search_root.parents if p.name in ("ul", "ol")]) if search_root not in (sidebar, soup) else 0

        # 3. Locate all TOC Items (`<li class="toc-item">`)
        toc_items = search_root.find_all("li", class_=lambda c: c and "toc-item" in str(c).lower())

        nodes: List[TOCNode] = []
        seen_urls: Set[str] = set()

        ignored_nav_count = 0
        duplicate_count = 0
        external_count = 0
        unknown_count = 0

        # Stack tracking recent parent node at each level: level_parents[level_number] = (title, url)
        level_parents: dict[int, Tuple[str, str]] = {}

        for item in toc_items:
            a = item.find("a", href=True)
            if not a:
                continue

            raw_href = a["href"].strip()
            link_text = a.get_text(strip=True)

            if not raw_href or raw_href.startswith("#") or raw_href.startswith("javascript:"):
                ignored_nav_count += 1
                continue

            # Check False Positive Title
            if link_text.lower() in cls.FALSE_POSITIVE_TITLES:
                ignored_nav_count += 1
                continue

            canonical_url = URLNormalizer.get_canonical_url(raw_href, base_url)

            # Skip root URL or non-crawlable domains
            if not URLNormalizer.is_sap_help_domain(canonical_url):
                external_count += 1
                continue

            if not URLNormalizer.is_crawlable_sap_url(canonical_url):
                ignored_nav_count += 1
                continue

            # Calculate level relative to search_root
            ul_parents_count = len([p for p in item.parents if p.name in ("ul", "ol")])
            relative_level = ul_parents_count - search_root_ul_parents
            level = max(1, relative_level)

            # Handle root page duplicate in TOC list
            if canonical_url == root_canonical:
                ignored_nav_count += 1
                continue

            # Deduplication Check
            if canonical_url in seen_urls:
                duplicate_count += 1
                continue

            seen_urls.add(canonical_url)

            # Resolve Parent Node Context
            parent_title: Optional[str] = None
            parent_canonical: Optional[str] = None

            if level == 1:
                parent_title = root_title
                parent_canonical = root_canonical
            else:
                # Find closest parent at level - 1
                parent_info = level_parents.get(level - 1)
                if parent_info:
                    parent_title, parent_canonical = parent_info
                else:
                    # Fallback to root if parent level not found
                    parent_title = root_title
                    parent_canonical = root_canonical

            # Record this node as parent for subsequent deeper levels
            level_parents[level] = (link_text, canonical_url)

            node = TOCNode(
                title=link_text,
                url=canonical_url,
                canonical_url=canonical_url,
                level=level,
                parent_title=parent_title,
                parent_canonical_url=parent_canonical,
                link_type=LinkType.TOC_CHILD,
            )
            nodes.append(node)

        logger.info(f"Parsed TOC for '{root_title}': {len(nodes)} valid nodes, {duplicate_count} duplicates removed.")

        return ParsedTOC(
            root_title=root_title,
            root_canonical_url=root_canonical,
            nodes=nodes,
            total_nodes=len(nodes) + duplicate_count,
            unique_urls=len(nodes),
            duplicate_urls_removed=duplicate_count,
            ignored_navigation_links=ignored_nav_count,
            external_links=external_count,
            unknown_links=unknown_count,
        )

    @classmethod
    def extract_toc_children(cls, html: str, base_url: str) -> List[DiscoveredLink]:
        """
        Legacy interface wrapper: convert ParsedTOC nodes to List[DiscoveredLink].
        """
        parsed_toc = cls.parse_toc(html, base_url)
        discovered = []
        for node in parsed_toc.nodes:
            discovered.append(
                DiscoveredLink(
                    target_url=node.canonical_url,
                    canonical_url=node.canonical_url,
                    link_text=node.title,
                    link_type=LinkType.TOC_CHILD,
                    is_internal=True,
                    title=node.title,
                )
            )
        return discovered
