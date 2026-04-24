import re
from playwright.sync_api import sync_playwright
from .base import BaseScraper


class AmazonScraper(BaseScraper):
    store_name = "Amazon"

    def search(self, keyword: str) -> list:
        deals = []
        # rh=p_n_deal_type%3A23566065011 filters for "Today's Deals" on amazon.ca
        url = (
            f"https://www.amazon.ca/s?k={keyword.replace(' ', '+')}"
            f"&rh=p_n_deal_type%3A23566065011&i=garden"
        )
        try:
            with sync_playwright() as p:
                browser, context = self.get_browser_context(p)
                page = context.new_page()
                page.goto(url, timeout=30000, wait_until="domcontentloaded")
                self.random_delay(2, 5)

                items = page.query_selector_all("[data-component-type='s-search-result']")
                for item in items:
                    # discount signals: savings badge, list price, or countdown
                    savings_el = item.query_selector(".savingsPercentage, [class*='savings'], .a-badge-text")
                    list_price_el = item.query_selector(".a-text-price span[aria-hidden='true'], .a-price.a-text-price")
                    countdown_el = item.query_selector("[class*='deal-badge'], [id*='deal-badge']")

                    if not savings_el and not list_price_el and not countdown_el:
                        continue

                    name_el = item.query_selector("h2 span, h2 a span")
                    price_whole = item.query_selector(".a-price-whole")
                    price_frac = item.query_selector(".a-price-fraction")
                    link_el = item.query_selector("h2 a")
                    img_el = item.query_selector("img.s-image")

                    if not name_el or not price_whole:
                        continue

                    name = name_el.inner_text().strip()
                    frac = price_frac.inner_text().strip() if price_frac else "00"
                    current = self._parse_price(f"{price_whole.inner_text()}.{frac}")
                    original = self._parse_price(list_price_el.inner_text()) if list_price_el else None

                    if savings_el:
                        label = savings_el.inner_text().strip()
                    elif countdown_el:
                        label = countdown_el.inner_text().strip()
                    else:
                        label = "Deal"

                    href = link_el.get_attribute("href") if link_el else ""
                    if href and not href.startswith("http"):
                        href = "https://www.amazon.ca" + href
                    img = img_el.get_attribute("src") if img_el else ""

                    if current:
                        deals.append(self.make_deal(keyword, name, current, original, label, href, img))

                browser.close()
        except Exception as e:
            print(f"[Amazon] Error for '{keyword}': {e}")
        return deals

    def _parse_price(self, text: str) -> float:
        if not text:
            return None
        match = re.search(r"[\d,]+\.?\d*", text.replace(",", ""))
        return float(match.group()) if match else None
