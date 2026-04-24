import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from config import GMAIL_USER, GMAIL_APP_PASSWORD, NOTIFY_EMAILS

STORE_COLORS = {
    "Pottery Barn": "#8B4513",
    "Etsy": "#F56400",
    "Amazon": "#FF9900",
    "IKEA": "#0058A3",
    "H&M": "#E50010",
    "Zara": "#000000",
}


def build_email_html(results: dict, products: list) -> str:
    deals = results["deals"]
    last_updated = results["last_updated"]

    sections = ""
    for keyword in products:
        keyword_deals = [d for d in deals if d["keyword"] == keyword]
        if not keyword_deals:
            continue

        cards = ""
        for d in keyword_deals:
            store_color = STORE_COLORS.get(d["store"], "#333")
            discount_badge = f'<span style="background:#e53e3e;color:white;padding:2px 8px;border-radius:12px;font-size:12px;font-weight:bold;">{d["discount_pct"]}% OFF</span>' if d["discount_pct"] else ""
            original_price = f'<span style="text-decoration:line-through;color:#999;font-size:13px;">CA${d["original_price"]:.2f}</span> ' if d["original_price"] else ""
            img_html = f'<img src="{d["image_url"]}" style="width:80px;height:80px;object-fit:cover;border-radius:4px;margin-right:12px;" />' if d["image_url"] else ""

            cards += f"""
            <tr>
              <td style="padding:12px;border-bottom:1px solid #eee;">
                <table cellpadding="0" cellspacing="0" border="0" width="100%">
                  <tr>
                    <td style="width:80px;vertical-align:top;">{img_html}</td>
                    <td style="vertical-align:top;padding-left:12px;">
                      <div style="font-size:11px;font-weight:bold;color:{store_color};margin-bottom:4px;">{d['store'].upper()}</div>
                      <div style="font-size:14px;font-weight:500;margin-bottom:6px;">{d['product_name']}</div>
                      <div style="margin-bottom:6px;">{original_price}<strong style="font-size:16px;">CA${d['current_price']:.2f}</strong> {discount_badge}</div>
                      <div style="font-size:11px;color:#888;margin-bottom:8px;">{d['discount_label']}</div>
                      <a href="{d['url']}" style="background:#2b6cb0;color:white;padding:6px 14px;border-radius:4px;text-decoration:none;font-size:13px;">Buy Now</a>
                    </td>
                  </tr>
                </table>
              </td>
            </tr>"""

        sections += f"""
        <tr><td style="padding:16px 0 8px;font-size:18px;font-weight:bold;border-bottom:2px solid #2b6cb0;color:#2b6cb0;">
          {keyword.title()} — {len(keyword_deals)} deal(s) found
        </td></tr>
        {cards}
        <tr><td style="height:20px;"></td></tr>"""

    if not sections:
        return ""

    return f"""
    <html><body style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;color:#333;">
      <table cellpadding="0" cellspacing="0" border="0" width="100%">
        <tr><td style="background:#2b6cb0;padding:20px;text-align:center;">
          <h1 style="color:white;margin:0;font-size:22px;">Deal Finder — Daily Update</h1>
          <p style="color:#bee3f8;margin:6px 0 0;font-size:13px;">Updated: {last_updated[:10]}</p>
        </td></tr>
        <tr><td style="padding:16px;">
          <table cellpadding="0" cellspacing="0" border="0" width="100%">
            {sections}
          </table>
        </td></tr>
        <tr><td style="background:#f7fafc;padding:16px;text-align:center;font-size:12px;color:#999;">
          You're receiving this because you subscribed to Deal Finder alerts.
        </td></tr>
      </table>
    </body></html>"""


def send_notification(results: dict, products: list):
    html_body = build_email_html(results, products)
    if not html_body:
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Deal Finder: {results['total_deals']} deal(s) found today"
    msg["From"] = GMAIL_USER
    msg["To"] = ", ".join([e for e in NOTIFY_EMAILS if e])
    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        server.sendmail(GMAIL_USER, [e for e in NOTIFY_EMAILS if e], msg.as_string())
