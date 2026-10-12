import re
from urllib.parse import urlparse, urlunparse, urljoin, parse_qsl, urlencode
import tldextract

class URLNormalizer:
    """
    URL Normalizer and Domain Filtering Validator for SAP Help Portal.
    """

    ALLOWED_DOMAINS = {"help.sap.com"}
    REJECT_PATH_PREFIXES = (
        "/legal",
        "/privacy",
        "/terms",
        "/cookie",
        "/search",
        "/login",
        "/logout",
        "/user",
        "/feedback",
        "/support",
        "/api",
    )

    @classmethod
    def normalize(cls, raw_url: str, base_url: str = None) -> str:
        """
        Normalize a raw URL by resolving relative links, removing fragments,
        standardizing protocol/host, stripping trailing slashes, and sorting query parameters.
        """
        if not raw_url:
            return ""

        # Resolve relative URL against base_url if provided
        if base_url:
            full_url = urljoin(base_url, raw_url.strip())
        else:
            full_url = raw_url.strip()

        # Parse URL
        parsed = urlparse(full_url)
        
        # Ensure scheme is https
        scheme = parsed.scheme.lower() if parsed.scheme in ("http", "https") else "https"
        netloc = parsed.netloc.lower()

        # Normalize path: remove redundant slashes, strip fragment
        path = parsed.path
        path = re.sub(r"/{2,}", "/", path)
        if len(path) > 1 and path.endswith("/"):
            path = path[:-1]

        # Filter & sort query parameters
        # Preserve version or key parameters while stripping tracking/session noise
        query_params = parse_qsl(parsed.query)
        cleaned_params = []
        for key, val in query_params:
            key_lower = key.lower()
            if key_lower in ("utm_source", "utm_medium", "utm_campaign", "sessionid", "phpsessid", "gclid"):
                continue
            cleaned_params.append((key, val))
        
        cleaned_params.sort(key=lambda x: (x[0], x[1]))
        query_string = urlencode(cleaned_params)

        # Reconstruct canonical URL (fragment is completely stripped)
        canonical = urlunparse((scheme, netloc, path, "", query_string, ""))
        return canonical

    @classmethod
    def get_canonical_url(cls, raw_url: str, base_url: str = None) -> str:
        """
        Extract canonical identity URL for deduplication.
        """
        return cls.normalize(raw_url, base_url)

    @classmethod
    def is_sap_help_domain(cls, url: str) -> bool:
        """
        Check if URL belongs strictly to allowed SAP Help domains (e.g. help.sap.com).
        """
        if not url:
            return False
        parsed = urlparse(url)
        netloc = parsed.netloc.lower()
        if netloc in cls.ALLOWED_DOMAINS:
            return True
        extracted = tldextract.extract(url)
        registered_domain = f"{extracted.domain}.{extracted.suffix}".lower()
        return netloc == "help.sap.com" or registered_domain == "sap.com" and netloc.startswith("help.")

    @classmethod
    def is_crawlable_sap_url(cls, url: str) -> bool:
        """
        Check whether the URL is a valid SAP Help documentation topic page and not a legal, login, or search URL.
        """
        if not cls.is_sap_help_domain(url):
            return False

        parsed = urlparse(url)
        path = parsed.path.lower()

        # Reject legal, login, feedback, privacy pages
        for prefix in cls.REJECT_PATH_PREFIXES:
            if path.startswith(prefix) or f"/{prefix.strip('/')}/" in path:
                return False

        # Reject non-HTML assets (.pdf, .zip, .png, .jpg, .css, .js)
        if re.search(r"\.(pdf|zip|png|jpg|jpeg|gif|svg|css|js|json|xml|exe)$", path):
            return False

        return True
