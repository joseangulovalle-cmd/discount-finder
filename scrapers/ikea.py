import re
from playwright.sync_api import sync_playwright
from .base import BaseScraper


class IkeaScraper(BaseScraper):
    store_name = "IKEA"

    def search(self, keyword: str) -> list:
        deals = []
        url = f"https://www.ikea.com/ca/en/search/?q={keyword.replace(' ', '%20')}"
        try:
            with sync_playwright() as p:
                browser, context = self.get_browser_context(p)
                page = context.new_page()
                page.goto(url, timeout=30000, wait_until="domcontentloaded")
                self.random_delay(2, 4)
                page.wait_for_selector("[class*='plp-fragment-wrapper'], [class*='search-results']", timeout=15000)

                items = page.query_selector_all("[class*='pip-product-compact'], [class*='product-card']")
                for item in items:
                    # IKEA's discount signal: "New lower price" label
                    label_el = item.query_selector("[class*='pip-price-package__previous-price'], [class*='new-lower']")
                    prev_price_el = item.query_selector("[class*='pip-price-package__previous-price'] [class*='pip-price__integer'], [class*='previous-price']")

                    if not label_el and not prev_price_el:
                        # check for any "new lower price" text
                        text_content = item.inner_text()
                        if "new lower price" not in text_content.lower():
                            continue

                    name_el = item.query_selector("[class*='pip-header-section__title'], h3, [class*='product-name']")
                    desc_el = item.query_selector("[class*='pip-header-section__description'], [class*='product-description']")
                    price_int = item.query_selector("[class*='pip-price__integer']")
                    link_el = item.query_selector("a[href*='/ca/en/p/']")
                    img_el = item.query_selector("img")

                    if not name_el or not price_int:
                        continue

                    full_name = name_el.inner_text().strip()
                    if desc_el:
                        full_name += " - " + desc_el.inner_text().strip()

                    current = self._parse_price(price_int.inner_text())
                    original = self._parse_price(prev_price_el.inner_text()) if prev_price_el else None
                    label = "New lower price"
                    href = link_el.get_attribute("href") if link_el else ""
                    if href and not href.startswith("http"):
                        href = "https://www.ikea.com" + href
                    img = img_el.get_attribute("src") if img_el else ""

                    if current:
                        deals.append(self.make_deal(keyword, full_name, current, original, label, href, img))

                browser.close()
        except Exception as e:
            print(f"[IKEA] Error for '{keyword}': {e}")
        return deals

    def _parse_price(self, text: str) -> float:
        if not text:
            return None
        match = re.search(r"[\d,]+\.?\d*", text.replace(",", ""))
        return float(match.group()) if match else None
