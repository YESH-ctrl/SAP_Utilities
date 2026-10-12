from bs4 import BeautifulSoup

with open("tests/fixtures/source_11_invoicing.html", "r", encoding="utf-8") as f:
    html = f.read()

soup = BeautifulSoup(html, "lxml")
sidebar = soup.select_one("div.sidebar")

top_ul = sidebar.find("ul")
top_lis = top_ul.find_all("li", recursive=False)

for idx, li in enumerate(top_lis):
    a = li.find("a", href=True)
    title = a.get_text(strip=True) if a else "No link"
    href = a.get("href") if a else "No href"
    sub_items = li.find_all("li", class_=lambda c: c and "toc-item" in str(c).lower())
    has_active = bool(li.find(class_=lambda c: c and any(k in str(c).lower() for k in ["active", "selected", "current"])))
    print(f"Top Node #{idx}: '{title}' | Sub-items count: {len(sub_items)} | has_active: {has_active} | URL: {href}")
