import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from config import GMAIL_USER, GMAIL_APP_PASSWORD, NOTIFY_EMAILS

WEB_URL = "https://joseangulovalle-cmd.github.io/discount-finder/"


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
            discount_badge = (
                f'<span style="background:#C96B50;color:white;padding:2px 10px;'
                f'border-radius:12px;font-size:11px;font-weight:700;">'
                f'{d["discount_pct"]}% OFF</span>'
            ) if d["discount_pct"] else (
                f'<span style="background:#C96B50;color:white;padding:2px 10px;'
                f'border-radius:12px;font-size:11px;font-weight:700;">'
                f'{d.get("discount_label","Sale")}</span>'
            )
            original_price = (
                f'<span style="text-decoration:line-through;color:#aaa;font-size:12px;">'
                f'CA${d["original_price"]:.2f}</span>&nbsp;'
            ) if d["original_price"] else ""
            img_url = d["image_url"] if d.get("image_url", "").startswith("https://") else ""
            img_html = (
                f'<img src="{img_url}" style="width:72px;height:72px;'
                f'object-fit:cover;border-radius:6px;" />'
            ) if img_url else (
                f'<div style="width:72px;height:72px;background:#f0ebe6;'
                f'border-radius:6px;"></div>'
            )

            cards += f"""
            <tr>
              <td style="padding:14px 0;border-bottom:1px solid #f0ebe6;">
                <table cellpadding="0" cellspacing="0" border="0" width="100%">
                  <tr>
                    <td style="width:72px;vertical-align:top;">{img_html}</td>
                    <td style="vertical-align:top;padding-left:14px;">
                      <div style="font-size:10px;font-weight:700;color:#B8A9C9;letter-spacing:.08em;text-transform:uppercase;margin-bottom:3px;">{d['store']}</div>
                      <div style="font-size:13px;font-weight:600;color:#2d2d2d;margin-bottom:6px;line-height:1.3;">{d['product_name']}</div>
                      <div style="margin-bottom:8px;">{original_price}<strong style="font-size:15px;color:#2d2d2d;">CA${d['current_price']:.2f}</strong>&nbsp;&nbsp;{discount_badge}</div>
                      <a href="{d['url']}" style="background:#C96B50;color:white;padding:6px 16px;border-radius:20px;text-decoration:none;font-size:12px;font-weight:600;">Buy Now →</a>
                    </td>
                  </tr>
                </table>
              </td>
            </tr>"""

        sections += f"""
        <tr>
          <td style="padding:18px 0 6px;">
            <div style="font-size:13px;font-weight:700;color:#B8A9C9;text-transform:uppercase;letter-spacing:.1em;border-left:3px solid #C96B50;padding-left:10px;">
              {keyword.title()} &mdash; {len(keyword_deals)} deal(s)
            </div>
          </td>
        </tr>
        {cards}
        <tr><td style="height:10px;"></td></tr>"""

    if not sections:
        return ""

    return f"""
    <html><body style="margin:0;padding:0;background:#FAF0EB;font-family:'Segoe UI',Arial,sans-serif;">
      <table cellpadding="0" cellspacing="0" border="0" width="100%" style="background:#FAF0EB;">
        <tr><td align="center" style="padding:24px 16px;">

          <table cellpadding="0" cellspacing="0" border="0" width="600" style="max-width:600px;background:white;border-radius:12px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,0.08);">

            <!-- HEADER -->
            <tr>
              <td style="background:linear-gradient(135deg,#C96B50,#B85A40);padding:28px 32px;">
                <div style="font-size:22px;font-weight:700;color:white;margin-bottom:4px;">🏷️ Deal Finder</div>
                <div style="font-size:13px;color:rgba(255,255,255,0.8);">Automated discount tracker across Canadian online stores</div>
                <div style="margin-top:12px;font-size:13px;color:rgba(255,255,255,0.9);">
                  <strong style="color:white;">{results['total_deals']} deals</strong> found today &nbsp;·&nbsp; {last_updated[:10]}
                </div>
              </td>
            </tr>

            <!-- CTA BUTTON -->
            <tr>
              <td style="padding:20px 32px 8px;text-align:center;background:white;">
                <a href="{WEB_URL}" style="display:inline-block;background:#C96B50;color:white;padding:13px 36px;border-radius:30px;text-decoration:none;font-size:15px;font-weight:700;letter-spacing:.01em;">
                  Ver todos los deals →
                </a>
              </td>
            </tr>

            <!-- DEALS -->
            <tr>
              <td style="padding:8px 32px 16px;">
                <table cellpadding="0" cellspacing="0" border="0" width="100%">
                  {sections}
                </table>
              </td>
            </tr>

            <!-- FOOTER -->
            <tr>
              <td style="background:#FAF0EB;padding:16px 32px;text-align:center;font-size:11px;color:#B8A9C9;">
                Recibes este email porque estás suscrito a Deal Finder alerts.
              </td>
            </tr>

          </table>
        </td></tr>
      </table>
    </body></html>"""


def send_notification(results: dict, products: list):
    html_body = build_email_html(results, products)
    if not html_body:
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"🏷️ Deal Finder: {results['total_deals']} deal(s) encontrados hoy"
    msg["From"] = GMAIL_USER
    msg["To"] = ", ".join([e for e in NOTIFY_EMAILS if e])
    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        server.sendmail(GMAIL_USER, [e for e in NOTIFY_EMAILS if e], msg.as_string())
