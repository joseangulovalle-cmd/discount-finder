import re
from playwright.sync_api import sync_playwright
from .base import BaseScraper
from config import ZARA_SALE_URLS


class ZaraScraper(BaseScraper):
    store_name = "Zara"

    def search(self, keyword: str) -> list:
        deals = []
        kw_lower = keyword.lower()
        for section, url in ZARA_SALE_URLS.items():
            try:
                with sync_playwright() as p:
                    browser, context = self.get_browser_context(p)
                    page = context.new_page()
                    page.goto(url, timeout=30000, wait_until="domcontentloaded")
                    self.random_delay(2, 4)
                    page.wait_for_selector("[class*='product-grid']", timeout=15000)

                    # scroll to load more items
                    for _ in range(3):
                        page.keyboard.press("End")
                        self.random_delay(1, 2)

                    items = page.query_selector_all("[class*='product-grid-product']")
                    for item in items:
                        name_el = item.query_selector("[class*='product-name'], [class*='product-grid-product-info__name']")
                        if not name_el:
                            continue
                        name = name_el.inner_text().strip()

                        # only include items matching the keyword
                        if not any(word in name.lower() for word in kw_lower.split()):
                            continue

                        # Zara discount signals: "-X%" badge + strikethrough price
                        badge_el = item.query_selector("[class*='sale-discount'], [class*='discount-promotion-label'], [class*='percent']")
                        orig_el = item.query_selector("s, del, [class*='line-through'], [class*='original-price']")

                        if not badge_el and not orig_el:
                            continue

                        price_el = item.query_selector("[class*='price__amount']:not(s):not(del), [data-qa-qualifier='price']")
                        link_el = item.query_selector("a")
                        img_el = item.query_selector("img")

                        current = self._parse_price(price_el.inner_text()) if price_el else None
                        original = self._parse_price(orig_el.inner_text()) if orig_el else None
                        label = badge_el.inner_text().strip() if badge_el else "Sale"
                        href = link_el.get_attribute("href") if link_el else ""
                        if href and not href.startswith("http"):
                            href = "https://www.zara.com" + href
                        img = img_el.get_attribute("src") if img_el else ""

                        if current:
                            deals.append(self.make_deal(keyword, name, current, original, label, href, img))

                    browser.close()
            except Exception as e:
                print(f"[Zara/{section}] Error for '{keyword}': {e}")
        return deals

    def _parse_price(self, text: str) -> float:
        if not text:
            return None
        match = re.search(r"[\d,]+\.?\d*", text.replace(",", ""))
        return float(match.group()) if match else None
