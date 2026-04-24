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
                page.goto(url, timeout=40000, wait_until="domcontentloaded")
                self.wait_for_page(page)

                total = page.evaluate("() => document.querySelectorAll('li, article').length")
                print(f"    [PotteryBarn] Total li/article elements: {total}")

                items = page.evaluate("""
                    () => {
                        const results = [];
                        document.querySelectorAll('li, article').forEach(card => {
                            const text = card.innerText || '';
                            if (text.length < 15) return;
                            const hasSale = /limited time|sale|special offer/i.test(text);
                            const hasStrike = card.querySelector('s, del, [style*="line-through"]');
                            if (!hasSale && !hasStrike) return;

                            const link = card.querySelector('a[href*="potterybarn"]');
                            const img = card.querySelector('img');
                            const prices = text.match(/\\$[\\d,]+\\.?\\d*/g) || [];
                            const nameEl = card.querySelector('a, h2, h3');
                            const labelEl = card.querySelector('[class*="sale"], [class*="badge"], [class*="promo"]');

                            if (prices.length < 1) return;
                            results.push({
                                name: nameEl ? nameEl.innerText.trim().substring(0, 100) : '',
                                label: labelEl ? labelEl.innerText.trim() : 'Sale',
                                prices: prices,
                                url: link ? link.href : '',
                                image: img ? (img.src || '') : ''
                            });
                        });
                        return results.slice(0, 20);
                    }
                """)

                print(f"    [PotteryBarn] Discounted items found: {len(items)}")
                for item in items:
                    name = item.get("name", "").strip()
                    prices = item.get("prices", [])
                    if not name or not prices:
                        continue
                    current = self._parse_price(prices[0])
                    original = self._parse_price(prices[1]) if len(prices) > 1 else None
                    if original and original < current:
                        current, original = original, current
                    label = item.get("label", "Sale").strip() or "Sale"
                    if current:
                        deals.append(self.make_deal(keyword, name, current, original, label,
                                                     item.get("url", ""), item.get("image", "")))
                browser.close()
        except Exception as e:
            print(f"[PotteryBarn] Error for '{keyword}': {e}")
        return deals

    def _parse_price(self, text: str) -> float:
        if not text:
            return None
        match = re.search(r"[\d,]+\.?\d*", str(text).replace(",", ""))
        return float(match.group()) if match else None
