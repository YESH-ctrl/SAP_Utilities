from bs4 import BeautifulSoup

with open("tests/fixtures/source_26_fi_ca_dunning.html", "r", encoding="utf-8") as f:
    html = f.read()

soup = BeautifulSoup(html, "lxml")
sidebar = soup.select_one("div.sidebar-wrapper, div.sidebar")

# Find active link
active_a = sidebar.find("a", class_=lambda c: c and "active" in str(c).lower())
print(f"Active link text: '{active_a.get_text(strip=True)}' -> {active_a.get('href')}")

active_li = active_a.find_parent("li", class_=lambda c: c and "toc-item" in str(c).lower())
print(f"Active <li>: '{active_li.find('a').get_text(strip=True) if active_li.find('a') else 'N/A'}'")
sub_items = active_li.find_all("li", class_=lambda c: c and "toc-item" in str(c).lower())
print(f"Sub-items inside active <li> ('Dunning'): {len(sub_items)}")

for idx, child in enumerate(sub_items):
    a = child.find("a")
    t = a.get_text(strip=True) if a else child.get_text(strip=True)[:40]
    print(f"  [{idx}] '{t}'")

# Trace ancestor <li> items
print("\nAncestor <li> chain from active link to top:")
ancestors = [p for p in active_a.parents if p.name == "li" and "toc-item" in str(p.get("class", []))]
for idx, p in enumerate(ancestors):
    a = p.find("a")
    t = a.get_text(strip=True) if a else "No link"
    cnt = len(p.find_all("li", class_=lambda c: c and "toc-item" in str(c).lower()))
    print(f"  Level {idx}: '{t}' | sub_items={cnt}")
