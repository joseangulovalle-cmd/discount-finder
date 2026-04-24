import re
from playwright.sync_api import sync_playwright
from .base import BaseScraper


class PotteryBarnScraper(BaseScraper):
    store_name = "Pottery Barn"

    def search(self, keyword: str) -> list:
        deals = []
        url = f"https://www.potterybarn.ca/search/results.html?words={keyword.replace(' ', '+')}"
        try:
            with sync_playwright() as p:
                browser, context = self.get_browser_context(p)
                page = context.new_page()
                page.goto(url, timeout=30000, wait_until="domcontentloaded")
                self.random_delay()
                page.wait_for_selector(".grid-catalog", timeout=15000)

                items = page.query_selector_all(".product-grid-container .product-tile")
                for item in items:
                    sale_label_el = item.query_selector(".price-special, .sale-flag, [class*='special'], [class*='sale-label']")
                    if not sale_label_el:
                        # look for strikethrough price as fallback signal
                        if not item.query_selector(".product-price s, .price s, del"):
                            continue

                    name_el = item.query_selector(".product-name a, h2 a, .name a")
                    price_el = item.query_selector(".price-special, .sale-price, [class*='special-price']")
                    orig_el = item.query_selector(".price-regular s, del, s")
                    img_el = item.query_selector("img")
                    link_el = item.query_selector("a")

                    if not name_el or not price_el:
                        continue

                    name = name_el.inner_text().strip()
                    label = sale_label_el.inner_text().strip() if sale_label_el else "Sale"
                    current = self._parse_price(price_el.inner_text())
                    original = self._parse_price(orig_el.inner_text()) if orig_el else None
                    href = link_el.get_attribute("href") if link_el else ""
                    if href and not href.startswith("http"):
                        href = "https://www.potterybarn.ca" + href
                    img = img_el.get_attribute("src") if img_el else ""

                    if current:
                        deals.append(self.make_deal(keyword, name, current, original, label, href, img))

                browser.close()
        except Exception as e:
            print(f"[PotteryBarn] Error for '{keyword}': {e}")
        return deals

    def _parse_price(self, text: str) -> float:
        if not text:
            return None
        match = re.search(r"[\d,]+\.?\d*", text.replace(",", ""))
        return float(match.group()) if match else None
