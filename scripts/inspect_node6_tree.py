from bs4 import BeautifulSoup

with open("tests/fixtures/source_11_invoicing.html", "r", encoding="utf-8") as f:
    html = f.read()

soup = BeautifulSoup(html, "lxml")
sidebar = soup.select_one("div.sidebar")

top_ul = sidebar.find("ul")
top_lis = top_ul.find_all("li", recursive=False)
node6 = top_lis[6] # IS-U Invoicing

print(f"Top Node #6 Title: {node6.find('a').get_text(strip=True)}")

# Direct child <ul> inside Node #6
node6_ul = node6.find("ul")
if node6_ul:
    direct_children = node6_ul.find_all("li", recursive=False)
    print(f"Direct sub-topics under IS-U Invoicing ({len(direct_children)} topics):")
    for idx, child in enumerate(direct_children):
        a = child.find("a")
        title = a.get_text(strip=True) if a else child.get_text(strip=True)[:40]
        has_active = bool(child.find(class_=lambda c: c and any(k in str(c).lower() for k in ["active", "selected", "current"])))
        print(f"  [{idx}] '{title}' (has_active={has_active})")

print("\nActive link in Node #6:")
active_a = node6.find("a", class_=lambda c: c and "active" in str(c).lower())
if active_a:
    print(f"  Active link text: '{active_a.get_text(strip=True)}' -> {active_a.get('href')}")
