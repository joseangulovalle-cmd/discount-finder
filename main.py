import json
import os
from datetime import datetime

from config import PRODUCTS_FILE, RESULTS_FILE, STORES
from scrapers.pottery_barn import PotteryBarnScraper
from scrapers.etsy import EtsyScraper
from scrapers.amazon import AmazonScraper
from scrapers.ikea import IkeaScraper
from scrapers.hm import HMScraper
from scrapers.zara import ZaraScraper
from notifier import send_notification
from generator import generate_html

SCRAPER_MAP = {
    "pottery_barn": PotteryBarnScraper,
    "etsy": EtsyScraper,
    "amazon": AmazonScraper,
    "ikea": IkeaScraper,
    "hm": HMScraper,
    "zara": ZaraScraper,
}


def load_products():
    with open(PRODUCTS_FILE, "r") as f:
        return json.load(f)["products"]


def run():
    products = load_products()
    print(f"Searching for {len(products)} product(s) across {len(STORES)} store(s)...")

    all_deals = []
    for store_key in STORES:
        scraper_class = SCRAPER_MAP.get(store_key)
        if not scraper_class:
            continue
        scraper = scraper_class()
        for keyword in products:
            print(f"  [{scraper.store_name}] Searching: '{keyword}'")
            deals = scraper.search(keyword)
            print(f"    Found {len(deals)} deal(s)")
            all_deals.extend(deals)

    results = {
        "last_updated": datetime.utcnow().isoformat() + "Z",
        "total_deals": len(all_deals),
        "deals": all_deals,
    }

    os.makedirs("data", exist_ok=True)
    with open(RESULTS_FILE, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved {len(all_deals)} deal(s) to {RESULTS_FILE}")

    generate_html(results, products)
    print("HTML UI generated.")

    if all_deals:
        send_notification(results, products)
        print("Email notification sent.")
    else:
        print("No deals found — email skipped.")


if __name__ == "__main__":
    run()
