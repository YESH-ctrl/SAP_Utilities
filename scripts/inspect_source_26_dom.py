from bs4 import BeautifulSoup

with open("tests/fixtures/source_26_fi_ca_dunning.html", "r", encoding="utf-8") as f:
    html = f.read()

soup = BeautifulSoup(html, "lxml")

h1 = soup.find("h1")
print(f"H1 Title: '{h1.get_text(strip=True) if h1 else 'N/A'}'")

breadcrumbs = soup.select_one("ul.breadcrumbs, nav.breadcrumbs, .breadcrumb")
print(f"Breadcrumbs: '{breadcrumbs.get_text(strip=True) if breadcrumbs else 'N/A'}'")

sidebar = soup.select_one("div.sidebar-wrapper, div.sidebar")
print(f"Sidebar tag: {sidebar.name if sidebar else 'N/A'}")

top_ul = sidebar.find("ul") if sidebar else None
top_lis = top_ul.find_all("li", recursive=False) if top_ul else []
print(f"\nTop <ul> has {len(top_lis)} top <li> items:")
for idx, li in enumerate(top_lis):
    a = li.find("a")
    text = a.get_text(strip=True) if a else li.get_text(strip=True)[:40]
    has_active = bool(li.find(class_=lambda c: c and any(k in str(c).lower() for k in ["active", "selected", "current"])))
    sub_count = len(li.find_all("li", class_=lambda c: c and "toc-item" in str(c).lower()))
    print(f"  [{idx}] '{text}' | sub_items={sub_count} | has_active={has_active} | class={li.get('class')}")

print("\nActive/Selected elements in sidebar:")
active_items = sidebar.find_all(class_=lambda c: c and any(k in str(c).lower() for k in ["active", "selected", "current", "expanded", "open"])) if sidebar else []
for item in active_items[:20]:
    a = item.find("a") if item.name != "a" else item
    href = a.get("href") if a else None
    print(f"  Tag={item.name}, class={item.get('class')}, text='{item.get_text(strip=True)[:60]}', href={href}")
