import random
import time
from playwright.sync_api import sync_playwright

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
]

STEALTH_SCRIPT = """
    Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
    Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3] });
    Object.defineProperty(navigator, 'languages', { get: () => ['en-CA', 'en'] });
    window.chrome = { runtime: {} };
"""


class BaseScraper:
    store_name = ""

    def __init__(self):
        self.results = []

    def random_delay(self, min_s=1.5, max_s=3.5):
        time.sleep(random.uniform(min_s, max_s))

    def get_browser_context(self, playwright):
        browser = playwright.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
        )
        context = browser.new_context(
            user_agent=random.choice(USER_AGENTS),
            locale="en-CA",
            timezone_id="America/Toronto",
            viewport={"width": 1280, "height": 900},
            extra_http_headers={"Accept-Language": "en-CA,en;q=0.9"}
        )
        context.add_init_script(STEALTH_SCRIPT)
        return browser, context

    def wait_for_page(self, page, timeout=25000):
        try:
            page.wait_for_load_state("networkidle", timeout=timeout)
        except:
            pass
        page.wait_for_timeout(4000)

    def search(self, keyword: str) -> list:
        raise NotImplementedError

    def make_deal(self, keyword, product_name, current_price, original_price,
                  discount_label, url, image_url=""):
        discount_pct = 0
        if original_price and original_price > current_price:
            discount_pct = round((1 - current_price / original_price) * 100)
        return {
            "keyword": keyword,
            "store": self.store_name,
            "product_name": product_name,
            "current_price": current_price,
            "original_price": original_price,
            "discount_pct": discount_pct,
            "discount_label": discount_label,
            "url": url,
            "image_url": image_url,
        }
