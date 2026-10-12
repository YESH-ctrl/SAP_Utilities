import pytest
from sap_rag.crawler.url_normalizer import URLNormalizer

def test_url_normalization_basic():
    url = "HTTPS://HELP.SAP.COM/docs/SAP_S4HANA_ON-PREMISE/123/page.html#section-1"
    normalized = URLNormalizer.normalize(url)
    assert normalized == "https://help.sap.com/docs/SAP_S4HANA_ON-PREMISE/123/page.html"

def test_relative_url_resolution():
    base = "https://help.sap.com/docs/SAP_S4HANA_ON-PREMISE/123/page.html"
    relative = "child_topic.html"
    resolved = URLNormalizer.normalize(relative, base_url=base)
    assert resolved == "https://help.sap.com/docs/SAP_S4HANA_ON-PREMISE/123/child_topic.html"

def test_sap_domain_filtering():
    assert URLNormalizer.is_sap_help_domain("https://help.sap.com/docs/foo") is True
    assert URLNormalizer.is_sap_help_domain("https://google.com") is False
    assert URLNormalizer.is_sap_help_domain("https://evil.com/help.sap.com") is False

def test_crawlable_url_validation():
    assert URLNormalizer.is_crawlable_sap_url("https://help.sap.com/docs/SAP_S4HANA/123/topic.html") is True
    assert URLNormalizer.is_crawlable_sap_url("https://help.sap.com/legal/terms") is False
    assert URLNormalizer.is_crawlable_sap_url("https://help.sap.com/docs/file.pdf") is False
