from bs4 import BeautifulSoup

with open("tests/fixtures/source_11_invoicing.html", "r", encoding="utf-8") as f:
    html = f.read()

soup = BeautifulSoup(html, "lxml")
sidebar = soup.select_one("div.sidebar")

print("--- Top Level <li> children of div.sidebar ---")
top_ul = sidebar.find("ul")
if top_ul:
    top_lis = top_ul.find_all("li", recursive=False)
    print(f"Top <ul> has {len(top_lis)} direct <li> children:")
    for idx, li in enumerate(top_lis):
        a = li.find("a")
        text = a.get_text(strip=True) if a else li.get_text(strip=True)[:40]
        has_active = bool(li.find(class_=lambda c: c and any(k in str(c).lower() for k in ["active", "selected", "current"])))
        print(f"  [{idx}] '{text}' (has_active={has_active}, class={li.get('class')})")

print("\n--- Inspecting active or current node in TOC ---")
active_in_sidebar = sidebar.find_all(class_=lambda c: c and any(k in str(c).lower() for k in ["active", "selected", "current", "expanded", "open"]))
for item in active_in_sidebar[:20]:
    a = item.find("a") if item.name != "a" else item
    href = a.get("href") if a else None
    print(f"  Tag={item.name}, class={item.get('class')}, text='{item.get_text(strip=True)[:60]}', href={href}")
