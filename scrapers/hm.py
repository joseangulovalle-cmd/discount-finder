import re
from playwright.sync_api import sync_playwright
from .base import BaseScraper


class HMScraper(BaseScraper):
    store_name = "H&M"

    def search(self, keyword: str) -> list:
        deals = []
        url = f"https://www2.hm.com/en_ca/search-results.html?q={keyword.replace(' ', '+')}"
        try:
            with sync_playwright() as p:
                browser, context = self.get_browser_context(p)
                page = context.new_page()
                page.goto(url, timeout=30000, wait_until="domcontentloaded")
                self.random_delay(2, 4)
                page.wait_for_selector(".products-listing", timeout=15000)

                items = page.query_selector_all(".product-item")
                for item in items:
                    # H&M discount signals: "Final Sale" badge or "-X%" badge or red price
                    sale_badge = item.query_selector(".sale-flag, [class*='sale-flag'], [class*='percent-off'], [class*='final-sale']")
                    red_price = item.query_selector(".sale-price, [class*='sale'], [style*='color: red'], [style*='color:red']")

                    if not sale_badge and not red_price:
                        continue

                    name_el = item.query_selector(".item-heading a, h2 a, .product-name")
                    price_el = item.query_selector(".sale-price, .price-value [data-value]")
                    orig_el = item.query_selector(".regular-price, s.price-value, del")
                    link_el = item.query_selector("a")
                    img_el = item.query_selector("img")

                    if not name_el:
                        continue

                    name = name_el.inner_text().strip()
                    label = sale_badge.inner_text().strip() if sale_badge else "Sale"
                    current_text = price_el.inner_text() if price_el else ""
                    current = self._parse_price(current_text)
                    original = self._parse_price(orig_el.inner_text()) if orig_el else None
                    href = link_el.get_attribute("href") if link_el else ""
                    if href and not href.startswith("http"):
                        href = "https://www2.hm.com" + href
                    img = img_el.get_attribute("src") if img_el else ""

                    if current:
                        deals.append(self.make_deal(keyword, name, current, original, label, href, img))

                browser.close()
        except Exception as e:
            print(f"[H&M] Error for '{keyword}': {e}")
        return deals

    def _parse_price(self, text: str) -> float:
        if not text:
            return None
        match = re.search(r"[\d,]+\.?\d*", text.replace(",", ""))
        return float(match.group()) if match else None
