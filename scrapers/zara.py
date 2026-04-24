import re
from playwright.sync_api import sync_playwright
from .base import BaseScraper
from config import ZARA_SALE_URLS


class ZaraScraper(BaseScraper):
    store_name = "Zara"

    def search(self, keyword: str) -> list:
        deals = []
        kw_words = keyword.lower().split()
        for section, url in ZARA_SALE_URLS.items():
            try:
                with sync_playwright() as p:
                    browser, context = self.get_browser_context(p)
                    page = context.new_page()
                    page.goto(url, timeout=40000, wait_until="domcontentloaded")
                    self.random_delay(3, 5)
                    try:
                        page.wait_for_load_state("networkidle", timeout=20000)
                    except:
                        pass

                    # scroll to load more items
                    for _ in range(3):
                        page.keyboard.press("End")
                        self.random_delay(1, 2)

                    items = page.evaluate("""
                        () => {
                            const results = [];
                            const cards = document.querySelectorAll('li[class*="product"], article[class*="product"], [class*="product-grid-product"]');
                            cards.forEach(card => {
                                const text = card.innerText || '';
                                // Zara discount: "-X%" badge + strikethrough price
                                const hasDiscount = /\\-\\d+%/.test(text);
                                const hasStrike = card.querySelector('s, del, [class*="line-through"]');
                                if (!hasDiscount && !hasStrike) return;

                                const link = card.querySelector('a');
                                const img = card.querySelector('img');
                                const prices = text.match(/\\$[\\d,]+\\.?\\d*/g) || [];
                                const badgeEl = card.querySelector('[class*="discount"], [class*="sale"], [class*="percent"]');
                                const nameEl = card.querySelector('[class*="name"], [class*="title"], h2, h3');

                                results.push({
                                    name: nameEl ? nameEl.innerText : text.split('\\n')[0],
                                    label: badgeEl ? badgeEl.innerText : 'Sale',
                                    prices: prices,
                                    url: link ? link.href : '',
                                    image: img ? (img.src || img.dataset.src || '') : ''
                                });
                            });
                            return results;
                        }
                    """)

                    for item in items:
                        name = item.get("name", "").strip()
                        prices = item.get("prices", [])
                        # filter: only items whose name contains at least one keyword word
                        if not name or not any(w in name.lower() for w in kw_words):
                            continue
                        if len(prices) < 1:
                            continue
                        current = self._parse_price(prices[0])
                        original = self._parse_price(prices[1]) if len(prices) > 1 else None
                        if original and original < current:
                            current, original = original, current
                        label = item.get("label", "Sale").strip() or "Sale"
                        href = item.get("url", "")
                        if href and not href.startswith("http"):
                            href = "https://www.zara.com" + href
                        if current:
                            deals.append(self.make_deal(keyword, name, current, original, label,
                                                         href, item.get("image", "")))
                    browser.close()
            except Exception as e:
                print(f"[Zara/{section}] Error for '{keyword}': {e}")
        return deals

    def _parse_price(self, text: str) -> float:
        if not text:
            return None
        match = re.search(r"[\d,]+\.?\d*", str(text).replace(",", ""))
        return float(match.group()) if match else None
