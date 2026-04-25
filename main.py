import json
import os
from datetime import datetime

from config import PRODUCTS_FILE, RESULTS_FILE
from scrapers.google_shopping import GoogleShoppingScraper
from notifier import send_notification
from generator import generate_html


def load_products():
    with open(PRODUCTS_FILE, "r") as f:
        return json.load(f)["products"]


def run():
    products = load_products()
    print(f"Searching for {len(products)} product(s) via Google Shopping...")

    scraper = GoogleShoppingScraper()
    all_deals = []

    for keyword in products:
        print(f"  Searching: '{keyword}'")
        deals = scraper.search(keyword)
        print(f"  Found {len(deals)} deal(s) for '{keyword}'")
        all_deals.extend(deals)
        scraper.random_delay(3, 6)

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
