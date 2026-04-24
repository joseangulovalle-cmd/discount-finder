import re
from playwright.sync_api import sync_playwright
from .base import BaseScraper


class AmazonScraper(BaseScraper):
    store_name = "Amazon"

    def search(self, keyword: str) -> list:
        deals = []
        url = f"https://www.amazon.ca/s?k={keyword.replace(' ', '+')}&i=garden"
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
                        const cards = document.querySelectorAll('[data-component-type="s-search-result"]');
                        cards.forEach(card => {
                            const text = card.innerText || '';
                            // discount signals: List price, savings %, countdown, "Typical"
                            const hasDeal = /list:|save \\d+%|typical:|ends in|\\d+%\\s*off/i.test(text);
                            const hasListPrice = card.querySelector('.a-price.a-text-price, [data-a-strike]');
                            if (!hasDeal && !hasListPrice) return;

                            const link = card.querySelector('h2 a, a[href*="/dp/"]');
                            const img = card.querySelector('img.s-image');
                            const nameEl = card.querySelector('h2 span');
                            const priceWhole = card.querySelector('.a-price-whole');
                            const priceFrac = card.querySelector('.a-price-fraction');
                            const listPrice = card.querySelector('.a-price.a-text-price .a-offscreen, .a-text-price .a-offscreen');
                            const savingEl = card.querySelector('.savingsPercentage, [class*="savings"]');

                            const whole = priceWhole ? priceWhole.innerText.replace(/[^\\d]/g, '') : '';
                            const frac = priceFrac ? priceFrac.innerText.replace(/[^\\d]/g, '') : '00';

                            results.push({
                                name: nameEl ? nameEl.innerText : '',
                                label: savingEl ? savingEl.innerText : (hasDeal ? 'Deal' : 'Sale'),
                                currentPrice: whole ? `${whole}.${frac}` : '',
                                originalPrice: listPrice ? listPrice.innerText : '',
                                url: link ? link.href : '',
                                image: img ? img.src : ''
                            });
                        });
                        return results;
                    }
                """)

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
