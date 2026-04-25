import re
import os
from playwright.sync_api import sync_playwright
from .base import BaseScraper

SCRAPER_API_KEY = os.environ.get("SCRAPER_API_KEY", "")

STORE_KEYWORDS = [
    "pottery barn", "etsy", "amazon", "ikea", "h&m", "zara",
    "west elm", "cb2", "structube", "wayfair", "homesense"
]


class GoogleShoppingScraper(BaseScraper):
    store_name = "Google Shopping"

    def search(self, keyword: str) -> list:
        deals = []
        google_url = (
            f"https://www.google.com/search?q={keyword.replace(' ', '+')}"
            f"+sale+discount&tbm=shop&gl=ca&hl=en"
        )
        url = (
            f"http://api.scraperapi.com?api_key={SCRAPER_API_KEY}"
            f"&url={google_url}&render=true&country_code=ca"
        )
        try:
            with sync_playwright() as p:
                browser, context = self.get_browser_context(p)
                page = context.new_page()
                page.goto(url, timeout=40000, wait_until="domcontentloaded")
                self.wait_for_page(page)

                import os
                os.makedirs("data/screenshots", exist_ok=True)
                screenshot_path = f"data/screenshots/{keyword.replace(' ', '_')}.png"
                page.screenshot(path=screenshot_path, full_page=False)
                print(f"    [Google Shopping] Screenshot saved: {screenshot_path}")

                page_title = page.title()
                print(f"    [Google Shopping] Page title: {page_title}")

                total = page.evaluate("() => document.querySelectorAll('div[class*=\"sh-dgr\"], .sh-pr__product-results-grid > div').length")
                print(f"    [Google Shopping] Total product cards: {total}")

                items = page.evaluate("""
                    () => {
                        const results = [];

                        // Google Shopping product cards
                        const selectors = [
                            '.sh-dgr__grid-result',
                            '.sh-pr__product-results-grid > div',
                            '[data-docid]',
                            '.KZmu8e',
                            '.i0X6df'
                        ];

                        let cards = [];
                        for (const sel of selectors) {
                            cards = Array.from(document.querySelectorAll(sel));
                            if (cards.length > 0) break;
                        }

                        console.log('Cards found with selector:', cards.length);

                        cards.forEach(card => {
                            const text = card.innerText || '';
                            if (text.length < 10) return;

                            // discount signals: strikethrough price OR % off text
                            const hasStrike = card.querySelector('s, del, [style*="line-through"]');
                            const hasOff = /\\d+%\\s*off|was\\s+\\$|save\\s+\\$/i.test(text);
                            if (!hasStrike && !hasOff) return;

                            // extract name
                            const nameEl = card.querySelector('h3, [class*="title"], [class*="name"]');
                            const name = nameEl ? nameEl.innerText.trim() : text.split('\\n')[0].trim();

                            // extract store
                            const storeEl = card.querySelector('[class*="merchant"], [class*="store"], .aULzUe, .E5ocAb');
                            const store = storeEl ? storeEl.innerText.trim() : '';

                            // extract prices
                            const prices = text.match(/\\$[\\d,]+\\.?\\d*/g) || [];

                            // extract discount label
                            const offMatch = text.match(/(\\d+%\\s*off|save\\s+\\$[\\d.]+)/i);
                            const label = offMatch ? offMatch[0] : 'Sale';

                            // extract link
                            const link = card.querySelector('a[href]');
                            const href = link ? link.href : '';

                            // extract image
                            const img = card.querySelector('img');
                            const image = img ? img.src : '';

                            if (name && prices.length > 0) {
                                results.push({ name, store, prices, label, url: href, image });
                            }
                        });
                        return results;
                    }
                """)

                print(f"    [Google Shopping] Discounted items for '{keyword}': {len(items)}")

                for item in items:
                    name = item.get("name", "").strip()
                    store = item.get("store", "").strip() or self._detect_store(item.get("url", ""))
                    prices = item.get("prices", [])
                    if not name or not prices:
                        continue

                    current = self._parse_price(prices[0])
                    original = self._parse_price(prices[1]) if len(prices) > 1 else None
                    if original and original < current:
                        current, original = original, current

                    label = item.get("label", "Sale").strip() or "Sale"
                    href = item.get("url", "")
                    image = item.get("image", "")

                    if current:
                        deal = self.make_deal(keyword, name, current, original, label, href, image)
                        deal["store"] = store if store else "Online Store"
                        deals.append(deal)

                browser.close()
        except Exception as e:
            print(f"[Google Shopping] Error for '{keyword}': {e}")
        return deals

    def _detect_store(self, url: str) -> str:
        url_lower = url.lower()
        for store in STORE_KEYWORDS:
            if store.replace("&", "").replace(" ", "") in url_lower.replace("&", "").replace(" ", ""):
                return store.title()
        return ""

    def _parse_price(self, text: str) -> float:
        if not text:
            return None
        match = re.search(r"[\d,]+\.?\d*", str(text).replace(",", ""))
        return float(match.group()) if match else None
