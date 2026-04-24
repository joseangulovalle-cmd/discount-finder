import json
from datetime import datetime


STORE_COLORS = {
    "Pottery Barn": "#8B4513",
    "Etsy": "#F56400",
    "Amazon": "#FF9900",
    "IKEA": "#0058A3",
    "H&M": "#E50010",
    "Zara": "#000000",
}

STORE_LOGOS = {
    "Pottery Barn": "PB",
    "Etsy": "Etsy",
    "Amazon": "amzn",
    "IKEA": "IKEA",
    "H&M": "H&M",
    "Zara": "ZARA",
}


def render_card(deal: dict) -> str:
    store_color = STORE_COLORS.get(deal["store"], "#333")
    store_abbr = STORE_LOGOS.get(deal["store"], deal["store"])
    discount_badge = f'<span class="discount-badge">{deal["discount_pct"]}% OFF</span>' if deal["discount_pct"] else ""
    original_price = f'<span class="original-price">CA${deal["original_price"]:.2f}</span>' if deal["original_price"] else ""
    img_html = f'<img src="{deal["image_url"]}" alt="{deal["product_name"]}" class="product-img" />' if deal["image_url"] else '<div class="product-img no-img"></div>'

    return f"""
    <div class="deal-card" data-keyword="{deal['keyword']}">
      {img_html}
      <div class="card-body">
        <div class="store-badge" style="background:{store_color};">{store_abbr}</div>
        <h3 class="product-name">{deal['product_name']}</h3>
        <div class="price-row">
          {original_price}
          <span class="current-price">CA${deal['current_price']:.2f}</span>
          {discount_badge}
        </div>
        <div class="sale-label">{deal['discount_label']}</div>
        <a href="{deal['url']}" target="_blank" class="buy-btn">Buy Now →</a>
      </div>
    </div>"""


def generate_html(results: dict, products: list):
    deals = results["deals"]
    last_updated = results["last_updated"][:10]
    total = results["total_deals"]

    # build filter tabs
    tabs_html = '<button class="tab active" onclick="filterDeals(\'all\')">All Deals</button>'
    for kw in products:
        count = sum(1 for d in deals if d["keyword"] == kw)
        tabs_html += f'<button class="tab" onclick="filterDeals(\'{kw}\')">{kw.title()} ({count})</button>'

    # build all cards
    cards_html = "".join(render_card(d) for d in deals) if deals else '<p class="no-deals">No deals found today. Check back tomorrow!</p>'

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Deal Finder</title>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #f0f4f8; color: #2d3748; }}

    header {{ background: #2b6cb0; color: white; padding: 24px 32px; }}
    header h1 {{ font-size: 28px; font-weight: 700; }}
    header p {{ font-size: 14px; opacity: 0.8; margin-top: 4px; }}

    .summary-bar {{ background: white; padding: 12px 32px; border-bottom: 1px solid #e2e8f0; font-size: 14px; color: #718096; }}
    .summary-bar strong {{ color: #2b6cb0; }}

    .filters {{ padding: 20px 32px 0; display: flex; gap: 10px; flex-wrap: wrap; }}
    .tab {{ padding: 8px 18px; border: 2px solid #2b6cb0; background: white; color: #2b6cb0;
             border-radius: 20px; cursor: pointer; font-size: 14px; font-weight: 500; transition: all .2s; }}
    .tab:hover, .tab.active {{ background: #2b6cb0; color: white; }}

    .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
             gap: 20px; padding: 24px 32px; }}

    .deal-card {{ background: white; border-radius: 12px; overflow: hidden;
                  box-shadow: 0 2px 8px rgba(0,0,0,.08); transition: transform .2s, box-shadow .2s; }}
    .deal-card:hover {{ transform: translateY(-4px); box-shadow: 0 8px 24px rgba(0,0,0,.12); }}
    .deal-card.hidden {{ display: none; }}

    .product-img {{ width: 100%; height: 200px; object-fit: cover; }}
    .no-img {{ width: 100%; height: 200px; background: #e2e8f0; }}

    .card-body {{ padding: 16px; }}
    .store-badge {{ display: inline-block; color: white; font-size: 11px; font-weight: 700;
                    padding: 3px 10px; border-radius: 12px; margin-bottom: 8px; }}
    .product-name {{ font-size: 14px; font-weight: 600; margin-bottom: 10px; line-height: 1.4;
                     display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }}
    .price-row {{ display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin-bottom: 6px; }}
    .original-price {{ text-decoration: line-through; color: #a0aec0; font-size: 13px; }}
    .current-price {{ font-size: 20px; font-weight: 700; color: #2d3748; }}
    .discount-badge {{ background: #e53e3e; color: white; font-size: 12px; font-weight: 700;
                       padding: 2px 8px; border-radius: 12px; }}
    .sale-label {{ font-size: 12px; color: #718096; margin-bottom: 12px; }}
    .buy-btn {{ display: inline-block; background: #2b6cb0; color: white; padding: 8px 18px;
                border-radius: 6px; text-decoration: none; font-size: 14px; font-weight: 500;
                transition: background .2s; }}
    .buy-btn:hover {{ background: #2c5282; }}

    .no-deals {{ text-align: center; padding: 60px; color: #a0aec0; font-size: 16px; grid-column: 1/-1; }}

    footer {{ text-align: center; padding: 24px; font-size: 13px; color: #a0aec0; }}
  </style>
</head>
<body>
  <header>
    <h1>Deal Finder</h1>
    <p>Automated discount tracker across Canadian online stores</p>
  </header>
  <div class="summary-bar">
    <strong>{total} deal(s)</strong> found across {len(products)} product(s) &nbsp;|&nbsp; Last updated: <strong>{last_updated}</strong>
  </div>
  <div class="filters">{tabs_html}</div>
  <div class="grid" id="deals-grid">{cards_html}</div>
  <footer>Deal Finder — runs daily at 5am ET</footer>

  <script>
    function filterDeals(keyword) {{
      document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
      event.target.classList.add('active');
      document.querySelectorAll('.deal-card').forEach(card => {{
        const match = keyword === 'all' || card.dataset.keyword === keyword;
        card.classList.toggle('hidden', !match);
      }});
    }}
  </script>
</body>
</html>"""

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)
