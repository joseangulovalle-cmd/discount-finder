import os

PRODUCTS_FILE = "products.json"
RESULTS_FILE = "data/results.json"

GMAIL_USER = os.environ.get("GMAIL_USER", "")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")
NOTIFY_EMAILS = os.environ.get("NOTIFY_EMAILS", "").split(",")
