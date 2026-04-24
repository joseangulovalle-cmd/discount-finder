import re
from playwright.sync_api import sync_playwright
from .base import BaseScraper


class EtsyScraper(BaseScraper):
    store_name = "Etsy"

    def search(self, keyword: str) -> list:
        deals = []
        # ship_to=CA filters to Canada, explicit_scope=physical_items
        url = (
            f"https://www.etsy.com/ca/search?q={keyword.replace(' ', '+')}"
            f"&ship_to=CA&explicit_scope=1&min_price=1"
        )
        try:
            with sync_playwright() as p:
                browser, context = self.get_browser_context(p)
                page = context.new_page()
                page.goto(url, timeout=30000, wait_until="domcontentloaded")
                self.random_delay(2, 4)
                page.wait_for_selector("[data-search-results]", timeout=15000)

                items = page.query_selector_all("li.wt-list-unstyled")
                for item in items:
                    sale_el = item.query_selector("[class*='sale-badge'], [class*='percent-off'], .sale-percent")
                    orig_el = item.query_selector("[class*='currency-base'] s, s[class*='price'], .currency-value ~ s")
                    if not sale_el and not orig_el:
                        continue

                    name_el = item.query_selector("h3, [class*='listing-link']")
                    price_el = item.query_selector("[class*='currency-value']:not(s)")
                    link_el = item.query_selector("a[href*='/listing/']")
                    img_el = item.query_selector("img")

                    if not name_el or not price_el:
                        continue

                    name = name_el.inner_text().strip()
                    label_text = sale_el.inner_text().strip() if sale_el else "Sale"
                    current = self._parse_price(price_el.inner_text())
                    original = self._parse_price(orig_el.inner_text()) if orig_el else None
                    href = link_el.get_attribute("href") if link_el else ""
                    img = img_el.get_attribute("src") if img_el else ""

                    if current:
                        deals.append(self.make_deal(keyword, name, current, original, label_text, href, img))

                browser.close()
        except Exception as e:
            print(f"[Etsy] Error for '{keyword}': {e}")
        return deals

    def _parse_price(self, text: str) -> float:
        if not text:
            return None
        match = re.search(r"[\d,]+\.?\d*", text.replace(",", ""))
        return float(match.group()) if match else None
