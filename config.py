import os

PRODUCTS_FILE = "products.json"
RESULTS_FILE = "data/results.json"

STORES = [
    "pottery_barn",
    "etsy",
    "amazon",
    "ikea",
    "hm",
    "zara",
]

GMAIL_USER = os.environ.get("GMAIL_USER", "")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")
NOTIFY_EMAILS = os.environ.get("NOTIFY_EMAILS", "").split(",")

# Zara dedicated sale section URLs (Canada)
ZARA_SALE_URLS = {
    "women": "https://www.zara.com/ca/en/woman-special-prices-l1314.html",
    "men":   "https://www.zara.com/ca/en/man-special-prices-l1314.html",
    "kids":  "https://www.zara.com/ca/en/kids-special-prices-l1314.html",
}
