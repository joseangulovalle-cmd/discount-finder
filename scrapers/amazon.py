import re
from playwright.sync_api import sync_playwright
from .base import BaseScraper


class AmazonScraper(BaseScraper):
    store_name = "Amazon"

    def search(self, keyword: str) -> list:
        deals = []
        url = f"https://www.amazon.ca/s?k={keyword.replace(' ', '+')}"
        try:
            with sync_playwright() as p:
                browser, context = self.get_browser_context(p)
                page = context.new_page()
                page.goto(url, timeout=40000, wait_until="domcontentloaded")
                self.wait_for_page(page)

                total_cards = page.evaluate(
                    "() => document.querySelectorAll('[data-component-type=\"s-search-result\"]').length"
                )
                print(f"    [Amazon] Total product cards found: {total_cards}")

                items = page.evaluate("""
                    () => {
                        const results = [];
                        document.querySelectorAll('[data-component-type="s-search-result"]').forEach(card => {
                            const text = card.innerText || '';
                            // discount signals
                            const hasListPrice = card.querySelector('.a-price.a-text-price');
                            const hasSavings = /save \\d+%|\\d+%\\s*off|list:|typical:/i.test(text);
                            if (!hasListPrice && !hasSavings) return;

                            const link = card.querySelector('h2 a');
                            const img = card.querySelector('img.s-image');
                            const nameEl = card.querySelector('h2 span');
                            const priceWhole = card.querySelector('.a-price-whole');
                            const priceFrac = card.querySelector('.a-price-fraction');
                            const listPriceEl = card.querySelector('.a-price.a-text-price .a-offscreen');
                            const savingEl = card.querySelector('.savingsPercentage');

                            const whole = priceWhole ? priceWhole.innerText.replace(/[^\\d]/g,'') : '';
                            const frac  = priceFrac  ? priceFrac.innerText.replace(/[^\\d]/g,'') : '00';

                            results.push({
                                name: nameEl ? nameEl.innerText.trim() : '',
                                label: savingEl ? savingEl.innerText.trim() : 'Deal',
                                currentPrice: whole ? `${whole}.${frac}` : '',
                                originalPrice: listPriceEl ? listPriceEl.innerText.trim() : '',
                                url: link ? link.href : '',
                                image: img ? img.src : ''
                            });
                        });
                        return results.slice(0, 20);
                    }
                """)

                print(f"    [Amazon] Discounted items found: {len(items)}")
                for item in items:
                    name = item.get("name", "").strip()
                    if not name:
                        continue
                    current = self._parse_price(item.get("currentPrice", ""))
                    original = self._parse_price(item.get("originalPrice", ""))
                    label = item.get("label", "Deal").strip() or "Deal"
                    href = item.get("url", "")
                    if href and not href.startswith("http"):
                        href = "https://www.amazon.ca" + href
                    if current:
                        deals.append(self.make_deal(keyword, name, current, original, label,
                                                     href, item.get("image", "")))
                browser.close()
        except Exception as e:
            print(f"[Amazon] Error for '{keyword}': {e}")
        return deals

    def _parse_price(self, text: str) -> float:
        if not text:
            return None
        match = re.search(r"[\d,]+\.?\d*", str(text).replace(",", ""))
        return float(match.group()) if match else None
