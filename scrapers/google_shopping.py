import re
import os
from playwright.sync_api import sync_playwright
from .base import BaseScraper

SCRAPER_API_KEY = os.environ.get("SCRAPER_API_KEY", "")


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
                page.goto(url, timeout=60000, wait_until="domcontentloaded")
                self.wait_for_page(page)

                os.makedirs("data/screenshots", exist_ok=True)
                page.screenshot(path=f"data/screenshots/{keyword.replace(' ', '_')}.png", full_page=False)
                print(f"    [Google Shopping] Page title: {page.title()}")

                items = page.evaluate("""
                    () => {
                        const results = [];

                        // Strategy: find all elements that contain "% OFF" text
                        // then walk up to find the product card container
                        const allElements = Array.from(document.querySelectorAll('*'));
                        const offBadges = allElements.filter(el => {
                            const t = el.innerText || '';
                            return /^\\d+%\\s*OFF$/i.test(t.trim()) && el.children.length === 0;
                        });

                        console.log('OFF badges found:', offBadges.length);

                        offBadges.forEach(badge => {
                            // walk up to find the product card (has image, name, price)
                            let card = badge.parentElement;
                            for (let i = 0; i < 8; i++) {
                                if (!card) break;
                                const hasImg = card.querySelector('img');
                                const text = card.innerText || '';
                                const hasPrices = (text.match(/\\$[\\d.]+/g) || []).length >= 2;
                                if (hasImg && hasPrices) break;
                                card = card.parentElement;
                            }
                            if (!card) return;

                            const text = card.innerText || '';
                            const prices = text.match(/\\$[\\d,]+\\.?\\d*/g) || [];
                            if (prices.length < 1) return;

                            // product name: first meaningful text line
                            const lines = text.split('\\n').map(l => l.trim()).filter(l =>
                                l.length > 5 && !/^\\$|^\\d+%|^\\d\\.\\d|free|delivery|return/i.test(l)
                            );
                            const name = lines[0] || '';

                            // store name: look for known patterns
                            const storeEl = card.querySelector('[class*="merchant"], [class*="store"], [class*="seller"]');
                            const storeText = storeEl ? storeEl.innerText.trim() : '';

                            // link
                            const link = card.querySelector('a[href]');
                            const href = link ? link.href : '';

                            // image
                            const img = card.querySelector('img');
                            const image = img ? img.src : '';

                            // discount label
                            const label = badge.innerText.trim();

                            results.push({ name, store: storeText, prices, label, url: href, image });
                        });

                        return results;
                    }
                """)

                print(f"    [Google Shopping] Discounted items for '{keyword}': {len(items)}")

                seen = set()
                for item in items:
                    name = item.get("name", "").strip()
                    store = item.get("store", "").strip() or self._detect_store(item.get("url", ""))
                    prices = item.get("prices", [])
                    if not name or not prices:
                        continue

                    # deduplicate
                    key = f"{name}_{prices[0]}"
                    if key in seen:
                        continue
                    seen.add(key)

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
        stores = ["potterybarn", "etsy", "amazon", "ikea", "hm", "zara",
                  "westelm", "cb2", "structube", "wayfair", "walmart",
                  "crateandbarrel", "homesense", "chapters", "indigo"]
        url_lower = url.lower().replace("-", "").replace(".", "")
        for store in stores:
            if store in url_lower:
                return store.title()
        return ""

    def _parse_price(self, text: str) -> float:
        if not text:
            return None
        match = re.search(r"[\d,]+\.?\d*", str(text).replace(",", ""))
        return float(match.group()) if match else None
