from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

class CrawlStatus(str, Enum):
    PENDING = "pending"
    QUEUED = "queued"
    CRAWLING = "crawling"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"

class LinkType(str, Enum):
    TOC_CHILD = "child"
    RELATED_DOCUMENT = "related"
    REFERENCE = "reference"
    NAVIGATION = "next"
    EXTERNAL = "external"
    LEGAL = "external"
    UNKNOWN = "reference"

class DocumentType(str, Enum):
    ROOT = "root"
    SECTION = "section"
    ARTICLE = "article"
    REFERENCE = "reference"

class DiscoveredLink(BaseModel):
    target_url: str
    canonical_url: str
    link_text: Optional[str] = None
    link_type: LinkType = LinkType.UNKNOWN
    is_internal: bool = True
    title: Optional[str] = None

class TOCNode(BaseModel):
    title: str
    url: str
    canonical_url: str
    level: int = 1
    parent_title: Optional[str] = None
    parent_canonical_url: Optional[str] = None
    link_type: LinkType = LinkType.TOC_CHILD

class ParsedTOC(BaseModel):
    root_title: str
    root_canonical_url: str
    nodes: List[TOCNode] = Field(default_factory=list)
    total_nodes: int = 0
    unique_urls: int = 0
    duplicate_urls_removed: int = 0
    ignored_navigation_links: int = 0
    external_links: int = 0
    unknown_links: int = 0

class ParsedSection(BaseModel):
    heading: str
    content: Optional[str] = None
    level: int = 1
    section_order: int = 0
    parent_section_index: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ParsedDocument(BaseModel):
    title: str
    url: str
    canonical_url: str
    content: str
    content_hash: str
    breadcrumbs: List[str] = Field(default_factory=list)
    sections: List[ParsedSection] = Field(default_factory=list)
    discovered_links: List[DiscoveredLink] = Field(default_factory=list)
    parsed_toc: Optional[ParsedTOC] = None
    toc_children: List[DiscoveredLink] = Field(default_factory=list)
    requires_browser: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)

class CrawlJobItem(BaseModel):
    id: int
    source_id: Optional[int] = None
    document_id: Optional[int] = None
    url: str
    parent_document_id: Optional[int] = None
    depth: int = 0
    status: CrawlStatus = CrawlStatus.PENDING
    priority: int = 10
    attempts: int = 0
    max_attempts: int = 3
    last_error: Optional[str] = None
    scheduled_at: datetime
    created_at: datetime
    updated_at: datetime
