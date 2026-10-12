from bs4 import BeautifulSoup

with open("tests/fixtures/source_1_master_data.html", "r", encoding="utf-8") as f:
    html1 = f.read()

soup1 = BeautifulSoup(html1, "lxml")
sb1 = soup1.select_one("div.sidebar-wrapper, div.sidebar")
top_ul1 = sb1.find("ul")
top_lis1 = top_ul1.find_all("li", recursive=False)
print(f"Source 1 sidebar top <ul> direct <li> count: {len(top_lis1)}")
for idx, li in enumerate(top_lis1):
    a = li.find("a")
    text = a.get_text(strip=True) if a else li.get_text(strip=True)[:40]
    has_act = bool(li.find(class_=lambda c: c and any(k in str(c).lower() for k in ["active", "selected", "w-current-page"])))
    print(f"  [{idx}] '{text}' has_active={has_act}")
