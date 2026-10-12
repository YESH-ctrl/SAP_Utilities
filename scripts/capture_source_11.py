import asyncio
from pathlib import Path
from sap_rag.crawler.fetcher import HTTPFetcher, close_browser, get_browser

async def main():
    url = "https://help.sap.com/docs/SAP_S4HANA_ON-PREMISE/ed84b70c199d4470ae2e5ccb93b2e45b/875dd0531d8b4208e10000000a174cb4.html"
    print(f"Fetching {url} with Playwright...")
    browser = await get_browser()
    context = await browser.new_context(user_agent="Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)")
    page = await context.new_page()
    await page.goto(url, wait_until="networkidle", timeout=30000)
    await page.wait_for_timeout(2000)
    
    out_dir = Path("storage/debug")
    out_dir.mkdir(parents=True, exist_ok=True)
    screenshot_path = out_dir / "source_11_invoicing.png"
    await page.screenshot(path=str(screenshot_path))
    
    html = await page.content()
    await context.close()
    
    html_path = out_dir / "source_11_invoicing.html"
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
        
    fix_dir = Path("tests/fixtures")
    fix_dir.mkdir(parents=True, exist_ok=True)
    with open(fix_dir / "source_11_invoicing.html", "w", encoding="utf-8") as f:
        f.write(html)
        
    print(f"Saved screenshot to {screenshot_path}, HTML ({len(html)} bytes) to {html_path} and fixture.")
    await close_browser()

if __name__ == "__main__":
    asyncio.run(main())
