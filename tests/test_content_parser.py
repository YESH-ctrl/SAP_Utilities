import pytest
from sap_rag.crawler.content_parser import ContentParser

SAMPLE_CONTENT_HTML = """
<html>
<head><title>Move-In Process | SAP Help Portal</title></head>
<body>
    <header><nav>Header Menu</nav></header>
    <main>
        <h1>Move-In Process Flow</h1>
        <p>This document details the Move-In Process in SAP Utilities.</p>
        
        <h2>Prerequisites</h2>
        <p>Ensure Business Partner exists.</p>

        <h2>Procedure</h2>
        <table>
            <tr><th>Step</th><th>Description</th></tr>
            <tr><td>1</td><td>Create Move-In Document</td></tr>
            <tr><td>2</td><td>Enter Meter Reading</td></tr>
        </table>
    </main>
    <footer>Footer Legal</footer>
</body>
</html>
"""

def test_content_parsing_and_table_conversion():
        url = "https://help.sap.com/docs/move_in.html"
        parsed = ContentParser.parse_document(SAMPLE_CONTENT_HTML, url)

        assert parsed.title == "Move-In Process"
        assert len(parsed.sections) >= 2
        assert "Step" in parsed.content
        assert "Create Move-In Document" in parsed.content
        assert parsed.content_hash is not None
        assert len(parsed.content_hash) == 64
