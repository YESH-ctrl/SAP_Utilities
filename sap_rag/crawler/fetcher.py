import asyncio
import logging
from typing import Tuple, Optional
import httpx
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from sap_rag.crawler.config import settings
from sap_rag.crawler.exceptions import FetchException, RateLimitException

logger = logging.getLogger(__name__)

# Lazy import Playwright if needed
_playwright_instance = None
_browser_instance = None

async def get_browser():
    """
    Get or initialize global Playwright browser instance.
    """
    global _playwright_instance, _browser_instance
    if _browser_instance is None:
        try:
            from playwright.async_api import async_playwright
            _playwright_instance = await async_playwright().start()
            _browser_instance = await _playwright_instance.chromium.launch(headless=True)
            logger.info("Playwright browser instance initialized successfully.")
        except Exception as e:
            logger.warning(f"Failed to launch Playwright browser: {e}. Fallback to browser rendering disabled.")
            return None
    return _browser_instance

async def close_browser():
    """
    Gracefully close Playwright browser instance on shutdown.
    """
    global _playwright_instance, _browser_instance
    if _browser_instance:
        await _browser_instance.close()
        _browser_instance = None
    if _playwright_instance:
        await _playwright_instance.stop()
        _playwright_instance = None
    logger.info("Playwright browser closed.")


class HTTPFetcher:
    """
    Async HTTP fetcher using httpx with exponential backoff retries & Playwright browser fallback.
    """
    def __init__(self, user_agent: str = None, timeout: float = 30.0):
        self.user_agent = user_agent or settings.CRAWLER_USER_AGENT
        self.timeout = timeout
        self.headers = {
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }

    async def fetch(self, url: str, client: Optional[httpx.AsyncClient] = None) -> Tuple[str, str, bool]:
        """
        Fetch HTML content for a URL.
        Returns: Tuple[html_content, final_url, used_playwright_fallback]
        """
        if client:
            return await self._fetch_with_client(url, client)

        async with httpx.AsyncClient(headers=self.headers, follow_redirects=True, timeout=self.timeout) as new_client:
            return await self._fetch_with_client(url, new_client)

    async def _fetch_with_client(self, url: str, client: httpx.AsyncClient) -> Tuple[str, str, bool]:
        logger.info(f"Fetching URL via httpx: {url}")
        try:
            response = await client.get(url, headers=self.headers)
        except httpx.HTTPError as e:
            logger.error(f"HTTP connection error for {url}: {e}")
            raise FetchException(f"Connection failed: {e}", url=url)

        # Handle HTTP 429 Rate Limiting
        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            wait_sec = int(retry_after) if retry_after and retry_after.isdigit() else 5
            logger.warning(f"HTTP 429 Rate limited for {url}. Waiting {wait_sec}s...")
            await asyncio.sleep(wait_sec)
            raise RateLimitException(url=url, retry_after=wait_sec)

        # Handle server errors (5xx)
        if response.status_code >= 500:
            logger.warning(f"Server error HTTP {response.status_code} for {url}")
            raise FetchException(f"HTTP {response.status_code}", http_status=response.status_code, url=url)

        # Handle 4xx client errors
        if response.status_code in (403, 404):
            logger.warning(f"HTTP {response.status_code} for {url}")
            raise FetchException(f"HTTP {response.status_code}", http_status=response.status_code, url=url)

        html_content = response.text
        final_url = str(response.url)

        # Check if page requires dynamic browser rendering fallback
        if self._is_dynamic_spa_page(html_content):
            logger.info(f"Page content indicates dynamic client-side rendering. Triggering Playwright fallback for {url}...")
            rendered_html = await self._fetch_with_playwright(url)
            if rendered_html:
                return rendered_html, final_url, True

        return html_content, final_url, False

    def _is_dynamic_spa_page(self, html: str) -> bool:
        """
        Detect whether page body is an unrendered single-page app shell.
        """
        if not html or len(html.strip()) < 500:
            return True

        soup = BeautifulSoup(html, "lxml")
        
        # Check if main documentation text is present
        main_text = soup.find("main") or soup.find("article") or soup.find(class_=lambda c: c and ("topic" in c or "content" in c or "help" in c))
        if not main_text or len(main_text.get_text(strip=True)) < 50:
            return True

        return False

    async def _fetch_with_playwright(self, url: str) -> Optional[str]:
        """
        Render page DOM completely using Playwright headless browser with retries.
        """
        browser = await get_browser()
        if not browser:
            return None

        for attempt in range(1, 3):
            context = await browser.new_context(user_agent=self.user_agent)
            page = await context.new_page()
            try:
                logger.info(f"Playwright loading page (attempt {attempt}/2): {url}")
                await page.goto(url, wait_until="networkidle", timeout=30000)

                # Wait for TOC or content containers if present
                await page.wait_for_timeout(2000)
                content = await page.content()
                await context.close()
                return content
            except Exception as e:
                logger.warning(f"Playwright rendering attempt {attempt}/2 failed for {url}: {e}")
                await context.close()
                if attempt < 2:
                    await asyncio.sleep(1.0)
        return None
