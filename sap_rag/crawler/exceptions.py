class CrawlerException(Exception):
    """Base exception for all SAP Help Crawler operations."""
    pass

class FetchException(CrawlerException):
    """Raised when HTTP request or Playwright rendering fails."""
    def __init__(self, message: str, http_status: int = None, url: str = None):
        super().__init__(message)
        self.http_status = http_status
        self.url = url

class RobotsDisallowedException(CrawlerException):
    """Raised when robots.txt forbids crawling a URL."""
    def __init__(self, url: str):
        super().__init__(f"Crawling disallowed by robots.txt for URL: {url}")
        self.url = url

class RateLimitException(FetchException):
    """Raised when HTTP 429 Too Many Requests is encountered."""
    def __init__(self, url: str, retry_after: int = None):
        super().__init__(f"Rate limited (429) for URL: {url}", http_status=429, url=url)
        self.retry_after = retry_after

class ParsingException(CrawlerException):
    """Raised when page content or TOC parsing fails."""
    pass

class DatabaseException(CrawlerException):
    """Raised when a Supabase database query or transaction fails."""
    pass
