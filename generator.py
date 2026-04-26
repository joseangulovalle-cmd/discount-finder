from datetime import datetime

STORE_BANNER_COLORS = {
    "amazon":          "#1E5C3A",
    "walmart":         "#2E7D52",
    "crate and barrel": "#5C3A1E",
    "pottery barn":    "#6B3A2E",
    "west elm":        "#2E4A5C",
    "westelm":         "#2E4A5C",
    "etsy":            "#D4581A",
    "ikea":            "#0058A3",
    "h&m":             "#B0002A",
    "zara":            "#1A1A1A",
    "wayfair":         "#7B2281",
    "structube":       "#3A3A3A",
}

STORE_BANNER_TEXT = {
    "ikea": "#ffffff",
}


def _banner_color(store: str) -> tuple:
    key = store.lower().replace(" ", "").replace("&", "and")
    for k, v in STORE_BANNER_COLORS.items():
        if k.replace(" ", "").replace("&", "and") in key or key in k.replace(" ", "").replace("&", "and"):
            return v, "#ffffff"
    return "#1E5C3A", "#ffffff"


def render_card(deal: dict, idx: int) -> str:
    store = deal.get("store", "Online Store")
    bg_color, text_color = _banner_color(store)

    img_html = (
        f'<img src="{deal["image_url"]}" alt="{deal["product_name"]}" '
        f'style="width:100%;height:185px;object-fit:cover;display:block;" />'
        if deal.get("image_url")
        else '<div class="card-img-placeholder">No image available</div>'
    )

    original_price = (
        f'<span class="original-price">CA${deal["original_price"]:.2f}</span>'
        if deal.get("original_price") else ""
    )

    discount_badge = (
        f'<span class="discount-badge">{deal["discount_pct"]}% OFF</span>'
        if deal.get("discount_pct")
        else f'<span class="discount-badge">{deal.get("discount_label","Sale")}</span>'
    )

    sale_label = deal.get("discount_label", "Sale")
    discount_val = deal.get("discount_pct") or 0
    price = deal.get("current_price", 0)
    keyword = deal.get("keyword", "")
    store_key = store.lower()

    return f"""
  <div class="deal-card" data-keyword="{keyword}" data-store="{store_key}" data-discount="{discount_val}" data-price="{price}" data-id="{idx}">
    <div class="card-img-wrap">
      {img_html}
      <button class="heart-btn" onclick="toggleHeart(this,'{idx}')">🤍</button>
    </div>
    <div class="store-banner" style="background:{bg_color};color:{text_color};">
      <span class="store-dot"></span> {store}
    </div>
    <div class="card-body">
      <div class="product-name">{deal["product_name"]}</div>
      <div class="price-row">
        {original_price}
        <span class="current-price">CA${price:.2f}</span>
        {discount_badge}
      </div>
      <div class="sale-label">{sale_label}</div>
      <a href="{deal.get('url','#')}" target="_blank" class="buy-btn">Buy Now →</a>
    </div>
  </div>"""


def generate_html(results: dict, products: list):
    deals = results["deals"]
    last_updated_raw = results["last_updated"][:10]
    try:
        dt = datetime.strptime(last_updated_raw, "%Y-%m-%d")
        last_updated = dt.strftime("%b %d, %Y")
    except Exception:
        last_updated = last_updated_raw
    total = results["total_deals"]

    # product tags
    tags_html = ""
    for kw in products:
        tags_html += (
            f'<span class="product-tag" data-keyword="{kw}">'
            f'{kw} <button onclick="removeProduct(\'{kw}\')">×</button></span>\n      '
        )
    pm_count = len(products)

    # product filter options
    product_opts = '<option value="all">All Products</option>\n'
    for kw in products:
        count = sum(1 for d in deals if d.get("keyword") == kw)
        product_opts += f'      <option value="{kw}">{kw.title()} ({count})</option>\n'

    # store filter options
    unique_stores = sorted({d.get("store", "Online Store") for d in deals})
    store_opts = '<option value="all">All Stores</option>\n'
    for s in unique_stores:
        store_opts += f'      <option value="{s.lower()}">{s}</option>\n'

    # cards
    cards_html = (
        "".join(render_card(d, i + 1) for i, d in enumerate(deals))
        if deals
        else '<p class="no-deals">No deals found today. Check back tomorrow!</p>'
    )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Deal Finder</title>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #FAF0EB; color: #2d3748; }}

    /* HEADER */
    header {{
      background: linear-gradient(135deg, #C96B50 0%, #B85A40 100%);
      color: white;
      padding: 22px 36px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}
    .header-left h1 {{ font-size: 27px; font-weight: 700; letter-spacing: -.3px; }}
    .header-left p {{ font-size: 13px; opacity: 0.7; margin-top: 3px; }}
    .header-stats {{ text-align: right; font-size: 13px; opacity: 0.9; line-height: 1.7; }}
    .header-stats strong {{ color: #ffffff; }}

    /* PRODUCT MANAGER */
    .product-manager {{
      background: white;
      border-bottom: 1px solid #f0e6e0;
      padding: 16px 36px;
    }}
    .pm-title {{
      font-size: 11px;
      font-weight: 700;
      color: #2E7D52;
      text-transform: uppercase;
      letter-spacing: .09em;
      margin-bottom: 10px;
      display: flex;
      align-items: center;
      gap: 8px;
    }}
    .pm-title::after {{
      content: '';
      flex: 1;
      height: 1px;
      background: linear-gradient(to right, #C9A84C33, transparent);
    }}
    .pm-counter {{
      background: #f5f0ff;
      color: #B8A9C9;
      font-size: 11px;
      padding: 2px 8px;
      border-radius: 10px;
      font-weight: 600;
    }}
    .pm-row {{ display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }}
    .product-tag {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      background: #f0faf4;
      border: 1.5px solid #7EC8A4;
      color: #1E5C3A;
      padding: 5px 12px;
      border-radius: 20px;
      font-size: 13px;
      font-weight: 500;
    }}
    .product-tag button {{
      background: none;
      border: none;
      color: #E8735A;
      cursor: pointer;
      font-size: 16px;
      line-height: 1;
      padding: 0;
      font-weight: 700;
    }}
    .product-tag button:hover {{ color: #c0392b; }}
    .pm-input-group {{ display: flex; gap: 8px; }}
    .pm-input {{
      border: 1.5px solid #d4c5be;
      border-radius: 8px;
      padding: 7px 14px;
      font-size: 13px;
      width: 230px;
      outline: none;
      background: #fdf8f6;
      color: #2d3748;
    }}
    .pm-input:focus {{ border-color: #7EC8A4; box-shadow: 0 0 0 2px rgba(126,200,164,.18); }}
    .pm-input::placeholder {{ color: #c4b0a8; }}
    .pm-add-btn {{
      background: #1E5C3A;
      color: white;
      border: none;
      border-radius: 8px;
      padding: 7px 18px;
      font-size: 13px;
      font-weight: 600;
      cursor: pointer;
      transition: background .2s;
    }}
    .pm-add-btn:hover {{ background: #2E7D52; }}

    /* FILTERS BAR */
    .filters-bar {{
      background: white;
      border-bottom: 1px solid #f0e6e0;
      padding: 11px 36px;
      display: flex;
      align-items: center;
      gap: 14px;
      flex-wrap: wrap;
    }}
    .summary-text {{ font-size: 13px; color: #918080; flex: 1; }}
    .summary-text strong {{ color: #1E5C3A; }}
    .heart-legend {{
      display: flex;
      gap: 14px;
      font-size: 12px;
      color: #B8A9C9;
      align-items: center;
      background: #f8f4ff;
      padding: 5px 14px;
      border-radius: 20px;
      border: 1px solid #e8e0f0;
    }}
    .heart-legend span {{ display: flex; align-items: center; gap: 4px; }}
    .filter-controls {{ display: flex; gap: 10px; align-items: center; }}
    select {{
      border: 1.5px solid #d4c5be;
      border-radius: 8px;
      padding: 7px 14px;
      font-size: 13px;
      color: #2d3748;
      background: #fdf8f6;
      cursor: pointer;
      outline: none;
    }}
    select:focus {{ border-color: #7EC8A4; }}

    /* GRID */
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
      gap: 20px;
      padding: 24px 36px;
    }}

    /* DEAL CARD */
    .deal-card {{
      background: white;
      border-radius: 14px;
      overflow: hidden;
      box-shadow: 0 2px 12px rgba(30,92,58,.07);
      transition: transform .2s, box-shadow .2s;
      display: flex;
      flex-direction: column;
      position: relative;
      border: 1px solid #f0ece8;
    }}
    .deal-card:hover {{
      transform: translateY(-4px);
      box-shadow: 0 10px 28px rgba(30,92,58,.13);
      border-color: #C9A84C44;
    }}
    .deal-card.hidden {{ display: none; }}
    .deal-card::before {{
      content: '';
      position: absolute;
      top: 0; left: 0; right: 0;
      height: 3px;
      background: linear-gradient(to right, #C9A84C, #E8C97A);
      opacity: 0;
      transition: opacity .2s;
    }}
    .deal-card:hover::before {{ opacity: 1; }}

    .card-img-wrap {{ position: relative; }}
    .card-img-placeholder {{
      width: 100%;
      height: 185px;
      background: linear-gradient(135deg, #f5ede8 0%, #e8f5ee 100%);
      display: flex;
      align-items: center;
      justify-content: center;
      color: #c4a89a;
      font-size: 12px;
    }}
    .heart-btn {{
      position: absolute;
      top: 10px; right: 10px;
      background: rgba(255,255,255,.88);
      border: none;
      border-radius: 50%;
      width: 34px; height: 34px;
      font-size: 18px;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 2px 8px rgba(0,0,0,.12);
      transition: transform .15s;
    }}
    .heart-btn:hover {{ transform: scale(1.18); }}
    .store-banner {{
      font-size: 11px;
      font-weight: 700;
      padding: 5px 14px;
      letter-spacing: .05em;
      display: flex;
      align-items: center;
      gap: 6px;
    }}
    .store-dot {{
      width: 5px; height: 5px;
      background: #C9A84C;
      border-radius: 50%;
      display: inline-block;
    }}
    .card-body {{ padding: 14px; flex: 1; display: flex; flex-direction: column; }}
    .product-name {{
      font-size: 14px;
      font-weight: 600;
      margin-bottom: 10px;
      line-height: 1.4;
      display: -webkit-box;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;
      overflow: hidden;
      flex: 1;
    }}
    .price-row {{ display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin-bottom: 4px; }}
    .original-price {{ text-decoration: line-through; color: #b8a8a0; font-size: 13px; }}
    .current-price {{ font-size: 20px; font-weight: 700; color: #1E5C3A; }}
    .discount-badge {{
      background: #E8735A;
      color: white;
      font-size: 11px;
      font-weight: 700;
      padding: 3px 9px;
      border-radius: 12px;
    }}
    .sale-label {{ font-size: 12px; color: #B8A9C9; margin-bottom: 12px; font-style: italic; }}
    .buy-btn {{
      display: block;
      background: linear-gradient(135deg, #E8735A, #c95f48);
      color: white;
      padding: 10px;
      border-radius: 8px;
      text-decoration: none;
      font-size: 13px;
      font-weight: 600;
      text-align: center;
      transition: opacity .2s;
      margin-top: auto;
    }}
    .buy-btn:hover {{ opacity: .88; }}
    .no-deals {{ text-align: center; padding: 60px; color: #b8a8a0; font-size: 16px; grid-column: 1/-1; }}

    /* POPUP */
    .popup-overlay {{
      display: none;
      position: fixed;
      inset: 0;
      background: rgba(30,30,30,.45);
      z-index: 100;
      align-items: center;
      justify-content: center;
    }}
    .popup-overlay.show {{ display: flex; }}
    .popup {{
      background: white;
      border-radius: 18px;
      padding: 34px;
      max-width: 370px;
      width: 90%;
      text-align: center;
      box-shadow: 0 24px 60px rgba(0,0,0,.18);
      border-top: 4px solid #C9A84C;
    }}
    .popup-icon {{ font-size: 40px; margin-bottom: 12px; }}
    .popup h3 {{ font-size: 18px; font-weight: 700; margin-bottom: 8px; color: #1E5C3A; }}
    .popup p {{ font-size: 14px; color: #918080; margin-bottom: 22px; line-height: 1.6; }}
    .popup-btn {{
      background: linear-gradient(135deg, #E8735A, #c95f48);
      color: white;
      border: none;
      border-radius: 8px;
      padding: 11px 28px;
      font-size: 14px;
      font-weight: 600;
      cursor: pointer;
    }}

    footer {{
      text-align: center;
      padding: 22px;
      font-size: 12px;
      color: #B8A9C9;
      border-top: 1px solid #f0e6e0;
      background: white;
      margin-top: 12px;
    }}
  </style>
</head>
<body>

<!-- HEADER -->
<header>
  <div class="header-left">
    <h1>Deal Finder</h1>
    <p>Automated discount tracker across Canadian online stores</p>
  </div>
  <div class="header-stats">
    <div><strong>{total}</strong> deals found today</div>
    <div>Last updated: <strong>{last_updated}</strong></div>
  </div>
</header>

<!-- PRODUCT MANAGER -->
<div class="product-manager">
  <div class="pm-title">
    My Product List &nbsp;<span class="pm-counter" id="pm-counter">{pm_count} of 6</span>
  </div>
  <div class="pm-row">
    <div id="tags-container">
      {tags_html}
    </div>
    <div class="pm-input-group">
      <input class="pm-input" id="new-product-input" type="text" placeholder="e.g. wooden dining chair" />
      <button class="pm-add-btn" id="pm-add-btn" onclick="addProduct()">+ Add</button>
    </div>
  </div>
</div>

<!-- FILTERS BAR -->
<div class="filters-bar">
  <div class="summary-text">
    <strong id="visible-count">{total}</strong> deals found across <strong>{len(products)}</strong> products
  </div>
  <div class="heart-legend">
    <span>❤️ Like</span>
    <span>🖤 Don't like</span>
    <span>🤍 Not seen</span>
  </div>
  <div class="filter-controls">
    <select id="product-filter" onchange="applyFilters()">
      {product_opts}
    </select>
    <select id="store-filter" onchange="applyFilters()">
      {store_opts}
    </select>
    <select id="sort-filter" onchange="applyFilters()">
      <option value="discount">Biggest Discount</option>
      <option value="price-asc">Lowest Price</option>
      <option value="price-desc">Highest Price</option>
    </select>
  </div>
</div>

<!-- DEAL CARDS GRID -->
<div class="grid" id="deals-grid">
{cards_html}
</div>

<footer>
  Deal Finder &nbsp;·&nbsp; Runs daily at 5am ET &nbsp;·&nbsp; Powered by ScraperAPI + GitHub Actions
</footer>

<!-- LIMIT POPUP -->
<div class="popup-overlay" id="limit-popup">
  <div class="popup">
    <div class="popup-icon">🌿</div>
    <h3>Product limit reached</h3>
    <p>The free plan is limited to <strong>6 products</strong>.<br>Please edit or remove one before adding a new one.</p>
    <button class="popup-btn" onclick="closePopup()">Got it</button>
  </div>
</div>

<script>
  const MAX_PRODUCTS = 6;
  const HEARTS = {{ '🤍': '❤️', '❤️': '🖤', '🖤': '🤍' }};
  const API_URL = 'https://discount-finder-five.vercel.app/api/products';

  document.querySelectorAll('.heart-btn').forEach(btn => {{
    const id = btn.closest('.deal-card').dataset.id;
    const saved = localStorage.getItem(`heart_${{id}}`);
    if (saved) btn.textContent = saved;
  }});

  function toggleHeart(btn, id) {{
    const next = HEARTS[btn.textContent] || '❤️';
    btn.textContent = next;
    localStorage.setItem(`heart_${{id}}`, next);
  }}

  function getProducts() {{
    return Array.from(document.querySelectorAll('.product-tag')).map(t => t.dataset.keyword);
  }}

  function updateCounter() {{
    const count = getProducts().length;
    document.getElementById('pm-counter').textContent = `${{count}} of ${{MAX_PRODUCTS}}`;
  }}

  function setLoading(on) {{
    document.getElementById('pm-add-btn').disabled = on;
    document.getElementById('pm-add-btn').textContent = on ? 'Saving...' : '+ Add';
  }}

  async function addProduct() {{
    const input = document.getElementById('new-product-input');
    const keyword = input.value.trim().toLowerCase();
    if (!keyword) return;
    if (getProducts().length >= MAX_PRODUCTS) {{
      document.getElementById('limit-popup').classList.add('show');
      return;
    }}
    if (getProducts().includes(keyword)) {{ input.value = ''; return; }}
    setLoading(true);
    try {{
      const res = await fetch(API_URL, {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify({{ action: 'add', product: keyword }})
      }});
      const data = await res.json();
      if (!res.ok) {{ alert(data.error); return; }}
      const tag = document.createElement('span');
      tag.className = 'product-tag';
      tag.dataset.keyword = keyword;
      tag.innerHTML = `${{keyword}} <button onclick="removeProduct('${{keyword}}')">×</button>`;
      document.getElementById('tags-container').appendChild(tag);
      input.value = '';
      updateCounter();
      rebuildProductDropdown();
    }} catch(e) {{
      alert('Could not save. Try again.');
    }} finally {{
      setLoading(false);
    }}
  }}

  async function removeProduct(keyword) {{
    try {{
      await fetch(API_URL, {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify({{ action: 'remove', product: keyword }})
      }});
    }} catch(e) {{ /* UI updates regardless */ }}
    document.querySelector(`.product-tag[data-keyword="${{keyword}}"]`)?.remove();
    updateCounter();
    rebuildProductDropdown();
  }}

  function rebuildProductDropdown() {{
    const sel = document.getElementById('product-filter');
    const current = sel.value;
    sel.innerHTML = '<option value="all">All Products</option>';
    getProducts().forEach(kw => {{
      const count = document.querySelectorAll(`.deal-card[data-keyword="${{kw}}"]`).length;
      const opt = document.createElement('option');
      opt.value = kw;
      opt.textContent = `${{kw.charAt(0).toUpperCase() + kw.slice(1)}} (${{count}})`;
      if (kw === current) opt.selected = true;
      sel.appendChild(opt);
    }});
  }}

  function closePopup() {{
    document.getElementById('limit-popup').classList.remove('show');
  }}

  function applyFilters() {{
    const productFilter = document.getElementById('product-filter').value;
    const storeFilter = document.getElementById('store-filter').value;
    const sortFilter = document.getElementById('sort-filter').value;
    const cards = Array.from(document.querySelectorAll('.deal-card'));
    cards.forEach(card => {{
      const pm = productFilter === 'all' || card.dataset.keyword === productFilter;
      const sm = storeFilter === 'all' || card.dataset.store === storeFilter;
      card.classList.toggle('hidden', !pm || !sm);
    }});
    const visible = cards.filter(c => !c.classList.contains('hidden'));
    visible.sort((a, b) => {{
      if (sortFilter === 'discount') return +b.dataset.discount - +a.dataset.discount;
      if (sortFilter === 'price-asc') return +a.dataset.price - +b.dataset.price;
      return +b.dataset.price - +a.dataset.price;
    }});
    const grid = document.getElementById('deals-grid');
    visible.forEach(card => grid.appendChild(card));
    document.getElementById('visible-count').textContent = visible.length;
  }}

  document.getElementById('new-product-input').addEventListener('keydown', e => {{
    if (e.key === 'Enter') addProduct();
  }});
</script>
</body>
</html>"""

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)
