import pytest
from sap_rag.crawler.link_classifier import LinkClassifier
from sap_rag.crawler.models import LinkType

def test_link_classification():
    type_ext, is_int = LinkClassifier.classify_single_link("https://google.com", "Google")
    assert type_ext == LinkType.EXTERNAL
    assert is_int is False

    type_legal, is_int = LinkClassifier.classify_single_link("https://help.sap.com/legal/privacy", "Privacy")
    assert type_legal == LinkType.LEGAL
    assert is_int is True

    type_ref, is_int = LinkClassifier.classify_single_link("https://help.sap.com/docs/SAP_S4HANA/topic.html", "Topic")
    assert type_ref == LinkType.REFERENCE
    assert is_int is True
