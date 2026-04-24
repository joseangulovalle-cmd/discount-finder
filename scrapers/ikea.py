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
                page.goto(url, timeout=40000, wait_until="domcontentloaded")
                self.random_delay(3, 5)
                try:
                    page.wait_for_load_state("networkidle", timeout=20000)
                except:
                    pass

                items = page.evaluate("""
                    () => {
                        const results = [];
                        // IKEA uses web components - look broadly
                        const cards = document.querySelectorAll('[class*="pip-product"], [class*="plp-product"], [class*="search-result"]');
                        cards.forEach(card => {
                            const text = card.innerText || '';
                            // IKEA discount signal: "New lower price" + "Previous price"
                            const hasDiscount = /new lower price|previous price/i.test(text);
                            if (!hasDiscount) return;

                            const link = card.querySelector('a');
                            const img = card.querySelector('img');
                            const prices = text.match(/\\$[\\d,]+\\.?\\d*/g) || [];
                            const nameEl = card.querySelector('[class*="title"], [class*="name"], h3');

                            results.push({
                                name: nameEl ? nameEl.innerText : text.split('\\n')[0],
                                label: 'New lower price',
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
                    if not name or len(prices) < 1:
                        continue
                    current = self._parse_price(prices[0])
                    original = self._parse_price(prices[1]) if len(prices) > 1 else None
                    if original and original < current:
                        current, original = original, current
                    if current:
                        deals.append(self.make_deal(keyword, name, current, original, "New lower price",
                                                     item.get("url", ""), item.get("image", "")))
                browser.close()
        except Exception as e:
            print(f"[IKEA] Error for '{keyword}': {e}")
        return deals

    def _parse_price(self, text: str) -> float:
        if not text:
            return None
        match = re.search(r"[\d,]+\.?\d*", str(text).replace(",", ""))
        return float(match.group()) if match else None
