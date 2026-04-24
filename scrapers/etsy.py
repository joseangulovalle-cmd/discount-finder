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
                self.wait_for_page(page)

                total_cards = page.evaluate("() => document.querySelectorAll('li').length")
                print(f"    [Etsy] Total <li> elements found: {total_cards}")

                items = page.evaluate("""
                    () => {
                        const results = [];
                        // Etsy uses <li> for product grid items
                        document.querySelectorAll('li').forEach(card => {
                            const text = card.innerText || '';
                            if (text.length < 10) return;
                            const hasOff = /\\d+%\\s*off|off\\s*\\d+%/i.test(text);
                            const hasStrike = card.querySelector('s, del');
                            if (!hasOff && !hasStrike) return;

                            const link = card.querySelector('a[href*="etsy.com"], a[href*="/listing/"]');
                            const img = card.querySelector('img');
                            const prices = text.match(/CA\\$[\\d,]+\\.?\\d*/g) || text.match(/\\$[\\d,]+\\.?\\d*/g) || [];
                            const offMatch = text.match(/(\\d+)%\\s*off/i);
                            const nameMatch = text.split('\\n').find(l => l.length > 5 && !/\\$|%|off|CA/i.test(l));

                            results.push({
                                name: nameMatch || text.substring(0, 60),
                                label: offMatch ? offMatch[0] : 'Sale',
                                prices: prices,
                                url: link ? link.href : '',
                                image: img ? (img.src || '') : ''
                            });
                        });
                        return results.slice(0, 20);
                    }
                """)

                print(f"    [Etsy] Discounted items found: {len(items)}")
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
