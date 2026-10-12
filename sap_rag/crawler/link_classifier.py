import logging
from typing import List
from bs4 import BeautifulSoup

from sap_rag.crawler.models import DiscoveredLink, LinkType
from sap_rag.crawler.url_normalizer import URLNormalizer

logger = logging.getLogger(__name__)

class LinkClassifier:
    """
    Classifies page links into structured LinkTypes (toc_child, related_document, reference, external, legal, navigation).
    Guarantees that ONLY relevant TOC child links are scheduled as hierarchy children.
    """

    LEGAL_PRIVACY_KEYWORDS = (
        "privacy",
        "legal",
        "terms-of-use",
        "cookie",
        "impressum",
        "copyright",
        "trademarks",
    )

    @classmethod
    def classify_and_extract_links(cls, html: str, base_url: str, toc_links: List[DiscoveredLink] = None) -> List[DiscoveredLink]:
        """
        Extract all links from page and classify each link into an explicit LinkType.
        """
        if not html:
            return []

        soup = BeautifulSoup(html, "lxml")
        discovered: List[DiscoveredLink] = []
        seen_urls = set()

        # Add existing TOC links
        toc_canonical_set = set()
        if toc_links:
            for link in toc_links:
                toc_canonical_set.add(link.canonical_url)
                seen_urls.add(link.canonical_url)
                discovered.append(link)

        current_canonical = URLNormalizer.get_canonical_url(base_url)

        # Scan page body links
        for a in soup.find_all("a", href=True):
            raw_href = a["href"].strip()
            link_text = a.get_text(strip=True)

            if not raw_href or raw_href.startswith("#") or raw_href.startswith("javascript:"):
                continue

            canonical_url = URLNormalizer.get_canonical_url(raw_href, base_url)

            if canonical_url == current_canonical or canonical_url in seen_urls:
                continue

            seen_urls.add(canonical_url)

            # Classify link
            link_type, is_internal = cls.classify_single_link(canonical_url, link_text, a)

            discovered.append(
                DiscoveredLink(
                    target_url=canonical_url,
                    canonical_url=canonical_url,
                    link_text=link_text or "SAP Reference",
                    link_type=link_type,
                    is_internal=is_internal,
                    title=link_text,
                )
            )

        return discovered

    @classmethod
    def classify_single_link(cls, url: str, link_text: str, tag: BeautifulSoup = None) -> tuple[LinkType, bool]:
        """
        Classify a single normalized URL and DOM element context.
        Returns: (LinkType, is_internal)
        """
        is_internal = URLNormalizer.is_sap_help_domain(url)

        if not is_internal:
            return LinkType.EXTERNAL, False

        url_lower = url.lower()
        text_lower = link_text.lower() if link_text else ""

        # Check Legal / Privacy
        if any(k in url_lower or k in text_lower for k in cls.LEGAL_PRIVACY_KEYWORDS):
            return LinkType.LEGAL, True

        # Check Navigation / Login / Search
        if any(k in url_lower for k in ("/search", "/login", "/user", "/feedback", "/support")):
            return LinkType.NAVIGATION, True

        # Check if parent section is "Related Information" or "See Also"
        if tag:
            parent_section = tag.find_parent(["section", "div", "aside"])
            if parent_section:
                heading = parent_section.find(["h1", "h2", "h3", "h4", "h5", "h6"])
                if heading and any(kw in heading.get_text(strip=True).lower() for kw in ("related", "see also", "reference")):
                    return LinkType.RELATED_DOCUMENT, True

        if URLNormalizer.is_crawlable_sap_url(url):
            return LinkType.REFERENCE, True

        return LinkType.UNKNOWN, True
