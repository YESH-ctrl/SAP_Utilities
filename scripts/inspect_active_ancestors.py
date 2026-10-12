from bs4 import BeautifulSoup

with open("tests/fixtures/source_11_invoicing.html", "r", encoding="utf-8") as f:
    html = f.read()

soup = BeautifulSoup(html, "lxml")
sidebar = soup.select_one("div.sidebar")

# Find the active link 'Billing Procedure'
active_a = sidebar.find("a", class_=lambda c: c and "active" in str(c).lower())
print(f"Active link: {active_a.get_text(strip=True)} -> {active_a.get('href')}")

# Find the closest top-level container or active sub-tree
active_li = active_a.find_parent("li", class_=lambda c: c and "toc-item" in str(c).lower())
print(f"Active <li>: {active_li.find('a').get_text(strip=True) if active_li.find('a') else 'N/A'}")

# Trace up ancestor <li> items inside sidebar
parents_lis = [p for p in active_a.parents if p.name == "li" and "toc-item" in str(p.get("class", []))]
print("Ancestor <li> items from active link to top:")
for idx, p in enumerate(parents_lis):
    a = p.find("a")
    title = a.get_text(strip=True) if a else "No link"
    sub_count = len(p.find_all("li", class_=lambda c: c and "toc-item" in str(c).lower()))
    print(f"  [{idx}] '{title}' (sub_items={sub_count})")
