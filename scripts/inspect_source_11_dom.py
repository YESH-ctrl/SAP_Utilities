from bs4 import BeautifulSoup

with open("tests/fixtures/source_11_invoicing.html", "r", encoding="utf-8") as f:
    html = f.read()

soup = BeautifulSoup(html, "lxml")

print("Checking sidebar selectors...")
sidebars = soup.select("div.sidebar-wrapper, div.sidebar, nav.sap-toc, div[role='tree'], aside.toc")
print(f"Found {len(sidebars)} sidebar elements.")

for idx, sb in enumerate(sidebars):
    items = sb.find_all("li", class_=lambda c: c and "toc-item" in str(c).lower())
    print(f"Sidebar #{idx} tag={sb.name} id={sb.get('id')} class={sb.get('class')}: {len(items)} toc-item <li> elements")

all_items = soup.find_all("li", class_=lambda c: c and "toc-item" in str(c).lower())
print(f"Total toc-item <li> elements in whole document: {len(all_items)}")

# Let's inspect active/selected node or tree structure
active_items = soup.find_all(class_=lambda c: c and any(k in str(c).lower() for k in ["active", "selected", "current"]))
print(f"\nActive/selected elements count: {len(active_items)}")
for item in active_items[:10]:
    print(f"  Tag: {item.name}, class: {item.get('class')}, text: {item.get_text(strip=True)[:50]}")
