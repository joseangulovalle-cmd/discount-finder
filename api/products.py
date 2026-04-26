from http.server import BaseHTTPRequestHandler
import json
import os
import urllib.request
import urllib.error
import base64

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
REPO = "joseangulovalle-cmd/discount-finder"
FILE_PATH = "products.json"
API_BASE = "https://api.github.com"


def _github_request(method: str, path: str, body: dict = None):
    url = f"{API_BASE}/repos/{REPO}/contents/{path}"
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"token {GITHUB_TOKEN}")
    req.add_header("Accept", "application/vnd.github.v3+json")
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def get_products():
    resp = _github_request("GET", FILE_PATH)
    content = base64.b64decode(resp["content"]).decode()
    data = json.loads(content)
    return data["products"], resp["sha"]


def save_products(products: list, sha: str):
    content = json.dumps({"products": products}, indent=2)
    encoded = base64.b64encode(content.encode()).decode()
    _github_request("PUT", FILE_PATH, {
        "message": "chore: update products list",
        "content": encoded,
        "sha": sha
    })


class handler(BaseHTTPRequestHandler):

    def _send(self, status: int, body: dict):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(json.dumps(body).encode())

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        try:
            products, _ = get_products()
            self._send(200, {"products": products})
        except Exception as e:
            self._send(500, {"error": str(e)})

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length))
            action = body.get("action")
            product = body.get("product", "").strip().lower()

            if not product:
                self._send(400, {"error": "product is required"})
                return

            products, sha = get_products()

            if action == "add":
                if len(products) >= 6:
                    self._send(400, {"error": "limit of 6 products reached"})
                    return
                if product not in products:
                    products.append(product)
                    save_products(products, sha)
                self._send(200, {"products": products})

            elif action == "remove":
                if product in products:
                    products.remove(product)
                    save_products(products, sha)
                self._send(200, {"products": products})

            else:
                self._send(400, {"error": "action must be 'add' or 'remove'"})

        except Exception as e:
            self._send(500, {"error": str(e)})
