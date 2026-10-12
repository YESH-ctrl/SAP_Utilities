from sap_rag.crawler.toc_parser import TOCParser

with open("tests/fixtures/source_11_invoicing.html", "r", encoding="utf-8") as f:
    html = f.read()

toc = TOCParser.parse_toc(html, "https://help.sap.com/docs/SAP_S4HANA_ON-PREMISE/ed84b70c199d4470ae2e5ccb93b2e45b/147bce53118d4308e10000000a174cb4.html")
print(f"Parsed TOC node count: {len(toc.nodes)}")
print(f"Unique URLs: {toc.unique_urls}")
print(f"Duplicates removed: {toc.duplicate_urls_removed}")
print("First 10 nodes:")
for n in toc.nodes[:10]:
    print(f"  [{n.level}] {n.title} -> {n.url}")
