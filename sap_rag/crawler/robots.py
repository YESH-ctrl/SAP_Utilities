import logging
from urllib.robotparser import RobotFileParser
from urllib.parse import urlparse
import httpx

logger = logging.getLogger(__name__)

class RobotsChecker:
    """
    Cache-aware robots.txt policy validator.
    """
    def __init__(self, user_agent: str = "Googlebot"):
        self.user_agent = user_agent
        self._parsers: dict[str, RobotFileParser] = {}

    def _get_agent_token(self, agent_string: str) -> str:
        if "Googlebot" in agent_string:
            return "Googlebot"
        if "bingbot" in agent_string.lower():
            return "Bingbot"
        return agent_string.split("/")[0].strip()

    async def is_allowed(self, url: str, client: httpx.AsyncClient = None) -> bool:
        """
        Check if robots.txt allows crawling the given URL.
        """
        parsed = urlparse(url)
        domain = f"{parsed.scheme}://{parsed.netloc}"

        if domain not in self._parsers:
            robots_url = f"{domain}/robots.txt"
            rfp = RobotFileParser()
            rfp.set_url(robots_url)
            try:
                headers = {"User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"}
                if client:
                    resp = await client.get(robots_url, headers=headers, timeout=10.0)
                    if resp.status_code == 200:
                        rfp.parse(resp.text.splitlines())
                    else:
                        logger.warning(f"robots.txt for {domain} returned HTTP {resp.status_code}, assuming allowed.")
                        rfp.allow_all = True
                else:
                    async with httpx.AsyncClient() as default_client:
                        resp = await default_client.get(robots_url, headers=headers, timeout=10.0)
                        if resp.status_code == 200:
                            rfp.parse(resp.text.splitlines())
                        else:
                            rfp.allow_all = True
            except Exception as e:
                logger.warning(f"Failed to fetch robots.txt for {domain}: {e}. Defaulting to allowed.")
                rfp.allow_all = True

            self._parsers[domain] = rfp

        rfp = self._parsers[domain]
        token = self._get_agent_token(self.user_agent)
        allowed = rfp.can_fetch(token, url)
        if not allowed:
            # Fallback check for wildcard or alternative bot tokens
            allowed = rfp.can_fetch("*", url)
        return allowed
