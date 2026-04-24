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
                page.goto(url, timeout=40000, wait_until="domcontentloaded")
                self.random_delay(3, 5)
                try:
                    page.wait_for_load_state("networkidle", timeout=20000)
                except:
                    pass

                items = page.evaluate("""
                    () => {
                        const results = [];
                        const cards = document.querySelectorAll('[class*="product-item"], article, li[class*="item"]');
                        cards.forEach(card => {
                            const text = card.innerText || '';
                            // H&M discount signals: "Final Sale", "-X%", red price
                            const hasDiscount = /final sale|\\-\\d+%/i.test(text);
                            const hasStrike = card.querySelector('s, del');
                            if (!hasDiscount && !hasStrike) return;

                            const link = card.querySelector('a');
                            const img = card.querySelector('img');
                            const prices = text.match(/\\$[\\d,]+\\.?\\d*/g) || [];
                            const badgeEl = card.querySelector('[class*="badge"], [class*="flag"], [class*="sale"]');
                            const nameEl = card.querySelector('[class*="title"], [class*="name"], h2, h3');

                            results.push({
                                name: nameEl ? nameEl.innerText : '',
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
                    if not name or len(prices) < 1:
                        continue
                    current = self._parse_price(prices[0])
                    original = self._parse_price(prices[1]) if len(prices) > 1 else None
                    if original and original < current:
                        current, original = original, current
                    label = item.get("label", "Sale").strip() or "Sale"
                    href = item.get("url", "")
                    if href and not href.startswith("http"):
                        href = "https://www2.hm.com" + href
                    if current:
                        deals.append(self.make_deal(keyword, name, current, original, label,
                                                     href, item.get("image", "")))
                browser.close()
        except Exception as e:
            print(f"[H&M] Error for '{keyword}': {e}")
        return deals

    def _parse_price(self, text: str) -> float:
        if not text:
            return None
        match = re.search(r"[\d,]+\.?\d*", str(text).replace(",", ""))
        return float(match.group()) if match else None
