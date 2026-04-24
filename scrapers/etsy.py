import re
from playwright.sync_api import sync_playwright
from .base import BaseScraper


class EtsyScraper(BaseScraper):
    store_name = "Etsy"

    def search(self, keyword: str) -> list:
        deals = []
        url = f"https://www.etsy.com/ca/search?q={keyword.replace(' ', '+')}&ship_to=CA&explicit_scope=1"
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
                        const cards = document.querySelectorAll('li[class*="wt-list"], div[data-search-result], li[data-search-result]');
                        cards.forEach(card => {
                            const text = card.innerText || '';
                            const hasOff = /\\d+%\\s*off|off\\s*\\d+%/i.test(text);
                            const hasStrike = card.querySelector('s, del');
                            if (!hasOff && !hasStrike) return;

                            const link = card.querySelector('a[href*="/listing/"]');
                            const img = card.querySelector('img');
                            const prices = text.match(/CA\\$[\\d,]+\\.?\\d*/g) || [];
                            const offMatch = text.match(/(\\d+)%\\s*off/i);

                            results.push({
                                name: (card.querySelector('h3, [class*="listing"]') || {}).innerText || '',
                                label: offMatch ? offMatch[0] : 'Sale',
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
                    if current:
                        deals.append(self.make_deal(keyword, name, current, original, label,
                                                     item.get("url", ""), item.get("image", "")))
                browser.close()
        except Exception as e:
            print(f"[Etsy] Error for '{keyword}': {e}")
        return deals

    def _parse_price(self, text: str) -> float:
        if not text:
            return None
        match = re.search(r"[\d,]+\.?\d*", str(text).replace(",", ""))
        return float(match.group()) if match else None
