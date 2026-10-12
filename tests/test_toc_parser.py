import os
import pytest
from sap_rag.crawler.toc_parser import TOCParser
from sap_rag.crawler.models import ParsedTOC, LinkType

FIXTURE_PATH = os.path.join(os.path.dirname(__file__), "fixtures", "source_1_master_data.html")

def test_toc_parser_source_1():
    assert os.path.exists(FIXTURE_PATH), f"Fixture file not found: {FIXTURE_PATH}"

    with open(FIXTURE_PATH, "r", encoding="utf-8") as f:
        html = f.read()

    base_url = "https://help.sap.com/docs/SAP_S4HANA_ON-PREMISE/021b182b0c47416c8fafed67ebfd78a9/0a6ace53118d4308e10000000a174cb4.html"

    parsed_toc: ParsedTOC = TOCParser.parse_toc(html, base_url)

    # 1. Assert Root Title
    assert parsed_toc.root_title == "Master Data"

    # 2. Assert valid node count and non-zero extraction
    assert len(parsed_toc.nodes) > 0

    # 3. Assert Major Expected Topics are Present
    node_titles = [node.title for node in parsed_toc.nodes]
    assert "SAP Business Partner" in node_titles
    assert any("Contract Account" in t for t in node_titles)
    assert any("Utilities Contract" in t or "Contract" in t for t in node_titles)
    assert any("Connection" in t for t in node_titles)

    # 4. Assert False Positive Navigation & Portal Links Ignored
    assert "SAP Help Portal" not in node_titles
    assert "SAP Online Help" not in node_titles
    assert "Log On" not in node_titles
    assert "Sign In" not in node_titles
    assert "Privacy" not in node_titles

    # 5. Assert Deduplication & Level Preservation
    canonical_urls = [node.canonical_url for node in parsed_toc.nodes]
    assert len(canonical_urls) == len(set(canonical_urls)), "TOC nodes contain duplicate canonical URLs!"

    # Assert levels are positive integers
    assert all(node.level >= 1 for node in parsed_toc.nodes)


FIXTURE_11_PATH = os.path.join(os.path.dirname(__file__), "fixtures", "source_11_invoicing.html")

def test_toc_parser_source_11():
    assert os.path.exists(FIXTURE_11_PATH), f"Fixture file not found: {FIXTURE_11_PATH}"

    with open(FIXTURE_11_PATH, "r", encoding="utf-8") as f:
        html = f.read()

    base_url = "https://help.sap.com/docs/SAP_S4HANA_ON-PREMISE/ed84b70c199d4470ae2e5ccb93b2e45b/147bce53118d4308e10000000a174cb4.html"

    parsed_toc: ParsedTOC = TOCParser.parse_toc(html, base_url)

    # 1. Assert Node Count is scoped and bounded (< 300 instead of 1000+)
    assert 0 < len(parsed_toc.nodes) < 300, f"Source 11 TOC count implausible: {len(parsed_toc.nodes)}"

    node_titles = [node.title for node in parsed_toc.nodes]

    # 2. Assert Genuine Invoicing/Billing Descendants Are Present
    assert any("Billing" in t or "Invoicing" in t or "DPC" in t for t in node_titles)

    # 3. Assert Unrelated Global SAP Modules Are Excluded
    unrelated_modules = [
        "Flexible Real Estate Management (RE-FX)",
        "Sales and Distribution (SD)",
        "Materials Management (MM)",
        "Hungary",
        "RE Navigator",
        "Commercial Real Estate Management",
        "Third-Party Management",
        "General Ledger Accounting",
        "Accounts Receivable",
        "Bank Accounting",
    ]
    for module in unrelated_modules:
        assert module not in node_titles, f"Unrelated module '{module}' incorrectly included in Source 11 TOC!"

    # 4. Assert False Positives & Deduplication
    assert "SAP Help Portal" not in node_titles
    assert "Privacy" not in node_titles

    canonical_urls = [node.canonical_url for node in parsed_toc.nodes]
    assert len(canonical_urls) == len(set(canonical_urls)), "Source 11 contains duplicate canonical URLs!"
    assert all(node.level >= 1 for node in parsed_toc.nodes)


FIXTURE_26_PATH = os.path.join(os.path.dirname(__file__), "fixtures", "source_26_fi_ca_dunning.html")

def test_toc_parser_source_26():
    assert os.path.exists(FIXTURE_26_PATH), f"Fixture file not found: {FIXTURE_26_PATH}"

    with open(FIXTURE_26_PATH, "r", encoding="utf-8") as f:
        html = f.read()

    base_url = "https://help.sap.com/docs/SAP_S4HANA_ON-PREMISE/9442486404b54071b4ebeab6a16628e7/b1ffc5536a51204be10000000a174cb4.html"

    parsed_toc: ParsedTOC = TOCParser.parse_toc(html, base_url)

    # 1. Assert Node Count is accurately scoped (31 nodes instead of 1482)
    assert 0 < len(parsed_toc.nodes) < 100, f"Source 26 TOC node count implausible: {len(parsed_toc.nodes)}"
    assert len(parsed_toc.nodes) == 31

    node_titles = [node.title for node in parsed_toc.nodes]

    # 2. Assert Genuine Dunning Sub-Topics Are Present
    assert "Configuration of the Dunning Process Flows" in node_titles
    assert "Dunning Procedure" in node_titles
    assert "Dunning Levels" in node_titles
    assert "Dunning Activities" in node_titles
    assert "Dunning Run" in node_titles
    assert "Creditworthiness" in node_titles

    # 3. Assert Unrelated FI-CA Sub-Modules Are Excluded
    unrelated_fi_ca_modules = [
        "Cash Desk",
        "Security Deposits",
        "Disconnection",
        "Deferred Revenue",
        "Returns",
        "General Ledger Accounting",
    ]
    for module in unrelated_fi_ca_modules:
        assert module not in node_titles, f"Unrelated FI-CA sub-module '{module}' incorrectly included in Source 26 TOC!"

    # 4. Assert False Positives, URL Uniqueness & Level Structure
    assert "SAP Help Portal" not in node_titles
    assert "Privacy" not in node_titles

    canonical_urls = [node.canonical_url for node in parsed_toc.nodes]
    assert len(canonical_urls) == len(set(canonical_urls)), "Source 26 contains duplicate canonical URLs!"
    assert all(node.level >= 1 for node in parsed_toc.nodes)
