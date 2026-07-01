"""
email_handler.py — Works with in-memory PDF bytes (no disk needed).
"""

import os
import uuid
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text       import MIMEText
from email.mime.application import MIMEApplication
from datetime import datetime

from database import (get_connection, update_order_status,
                      save_invoice_to_db, fetch_invoice_by_token,
                      update_invoice_status, POSTGRES)

YOUR_GMAIL        = os.environ.get("YOUR_GMAIL",        "ammarwaqar439@gmail.com")
YOUR_APP_PASSWORD = os.environ.get("YOUR_APP_PASSWORD", "vejc dfey byfo jcwv")
BASE_URL          = os.environ.get("BASE_URL",          "http://localhost:5000")


def _send_gmail(to_email, subject, html_body, pdf_bytes=None, pdf_filename=None):
    msg = MIMEMultipart("mixed")
    msg["From"]    = YOUR_GMAIL
    msg["To"]      = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(html_body, "html"))

    if pdf_bytes and pdf_filename:
        part = MIMEApplication(pdf_bytes, Name=pdf_filename)
        part["Content-Disposition"] = f'attachment; filename="{pdf_filename}"'
        msg.attach(part)

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.ehlo()
        server.starttls()
        server.login(YOUR_GMAIL, YOUR_APP_PASSWORD)
        server.sendmail(YOUR_GMAIL, to_email, msg.as_string())

    print(f"[EMAIL] Sent to {to_email}")


def create_and_send_invoice(order, pdf_bytes, invoice_id, boss_email, your_email):
    """Save invoice record and send approval email to boss."""
    token = str(uuid.uuid4())
    save_invoice_to_db(invoice_id, order["order_id"], boss_email, your_email, token)

    accept_url = f"{BASE_URL}/accept?token={token}"
    reject_url = f"{BASE_URL}/reject?token={token}"

    subject = f"Invoice Approval Required — Order {order['order_id']} | {order['product_name']}"

    html = f"""
<html>
<body style="margin:0;padding:0;background:#0F172A;font-family:'Segoe UI',Arial,sans-serif;">
<div style="max-width:580px;margin:40px auto;">
  <div style="height:5px;background:linear-gradient(90deg,#6366F1,#8B5CF6,#EC4899);border-radius:8px 8px 0 0;"></div>
  <div style="background:#1E293B;padding:32px 36px 24px;border-left:1px solid #334155;border-right:1px solid #334155;">
    <div style="display:flex;align-items:center;gap:12px;">
      <div style="background:linear-gradient(135deg,#6366F1,#8B5CF6);width:44px;height:44px;border-radius:10px;text-align:center;line-height:44px;font-size:22px;">📱</div>
      <div>
        <div style="color:white;font-size:18px;font-weight:700;">MobileMart Pakistan</div>
        <div style="color:#94A3B8;font-size:12px;">Invoice Approval Request</div>
      </div>
    </div>
  </div>
  <div style="background:#1E293B;padding:28px 36px;border-left:1px solid #334155;border-right:1px solid #334155;">
    <p style="color:#E2E8F0;font-size:15px;margin:0 0 8px;">Dear Sir/Ma'am,</p>
    <p style="color:#94A3B8;font-size:14px;line-height:1.7;margin:0 0 24px;">
      A new order invoice is awaiting your approval.
      The <b style="color:#A5B4FC;">PDF invoice is attached</b> to this email.
    </p>
    <div style="background:#0F172A;border:1px solid #334155;border-radius:10px;padding:18px 22px;margin-bottom:28px;">
      <div style="color:#64748B;font-size:10px;text-transform:uppercase;letter-spacing:1px;margin-bottom:12px;">Order Reference</div>
      <div style="display:flex;justify-content:space-between;flex-wrap:wrap;gap:12px;">
        <div><div style="color:#64748B;font-size:11px;">Order ID</div><div style="color:#A5B4FC;font-size:20px;font-weight:700;">{order['order_id']}</div></div>
        <div><div style="color:#64748B;font-size:11px;">Customer</div><div style="color:#E2E8F0;font-size:14px;font-weight:600;">{order['customer_name']}</div></div>
        <div><div style="color:#64748B;font-size:11px;">Amount</div><div style="color:#34D399;font-size:16px;font-weight:700;">PKR {order['total_price']:,.0f}</div></div>
      </div>
    </div>
    <p style="color:#94A3B8;font-size:13px;text-align:center;margin:0 0 20px;">Review the PDF and take action:</p>
    <table width="100%" cellpadding="0" cellspacing="0">
      <tr>
        <td style="padding:0 8px 0 0;">
          <a href="{accept_url}" style="display:block;background:linear-gradient(135deg,#059669,#10B981);color:white;text-align:center;padding:16px;border-radius:10px;text-decoration:none;font-size:15px;font-weight:700;">
            ✅ &nbsp; ACCEPT ORDER
          </a>
        </td>
        <td style="padding:0 0 0 8px;">
          <a href="{reject_url}" style="display:block;background:linear-gradient(135deg,#DC2626,#EF4444);color:white;text-align:center;padding:16px;border-radius:10px;text-decoration:none;font-size:15px;font-weight:700;">
            ❌ &nbsp; REJECT ORDER
          </a>
        </td>
      </tr>
    </table>
  </div>
  <div style="background:#0F172A;padding:16px 36px;border-radius:0 0 8px 8px;text-align:center;">
    <p style="color:#334155;font-size:11px;margin:0;">MobileMart Pakistan · Invoice: {invoice_id}</p>
  </div>
</div>
</body>
</html>"""

    _send_gmail(boss_email, subject, html,
                pdf_bytes=pdf_bytes,
                pdf_filename=f"{invoice_id}.pdf")
    return token


def process_acceptance(token):
    invoice = fetch_invoice_by_token(token)
    if not invoice:
        return False, "Invalid link.", None
    if invoice["status"] != "AWAITING APPROVAL":
        return False, f"Already {invoice['status']}.", None

    update_invoice_status(invoice["invoice_id"], "APPROVED", "approved_at", datetime.now().isoformat())
    update_order_status(invoice["order_id"], "APPROVED")
    _send_confirmation_to_you(invoice["your_email"], invoice["invoice_id"], invoice["order_id"])
    return True, invoice["invoice_id"], invoice["order_id"]


def process_rejection(token):
    invoice = fetch_invoice_by_token(token)
    if not invoice:
        return False, "Invalid link."
    if invoice["status"] != "AWAITING APPROVAL":
        return False, f"Already {invoice['status']}."

    update_invoice_status(invoice["invoice_id"], "REJECTED")
    update_order_status(invoice["order_id"], "REJECTED")
    return True, invoice["invoice_id"]


def _send_confirmation_to_you(your_email, invoice_id, order_id):
    subject = f"✅ Boss Approved — Order {order_id} | Ready to Forward"
    html = f"""
<html>
<body style="margin:0;padding:0;background:#0F172A;font-family:'Segoe UI',Arial,sans-serif;">
<div style="max-width:580px;margin:40px auto;">
  <div style="height:5px;background:linear-gradient(90deg,#10B981,#34D399);border-radius:8px 8px 0 0;"></div>
  <div style="background:#1E293B;padding:32px 36px;border:1px solid #334155;border-radius:0 0 8px 8px;">
    <div style="text-align:center;margin-bottom:24px;">
      <div style="font-size:52px;">🎉</div>
      <h2 style="color:#34D399;margin:12px 0 4px;">Order Approved!</h2>
      <p style="color:#64748B;font-size:13px;">Your boss accepted the invoice. Forward to supplier now.</p>
    </div>
    <div style="background:#0F172A;border:1px solid #1E3A2F;border-radius:10px;padding:20px 24px;margin-bottom:20px;">
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;">
        <div><div style="color:#64748B;font-size:11px;">Invoice ID</div><div style="color:#A5B4FC;font-weight:700;margin-top:4px;">{invoice_id}</div></div>
        <div><div style="color:#64748B;font-size:11px;">Order ID</div><div style="color:#A5B4FC;font-weight:700;margin-top:4px;">{order_id}</div></div>
        <div><div style="color:#64748B;font-size:11px;">Status</div><div style="color:#34D399;font-weight:700;margin-top:4px;">✅ APPROVED</div></div>
        <div><div style="color:#64748B;font-size:11px;">Time</div><div style="color:#E2E8F0;font-size:12px;margin-top:4px;">{datetime.now().strftime("%d %b %Y, %H:%M")}</div></div>
      </div>
    </div>
    <div style="background:#1C1917;border:1px dashed #78716C;border-radius:10px;padding:16px;text-align:center;">
      <p style="color:#A8A29E;font-size:13px;margin:0;">👉 Go to your dashboard and click <b style="color:#FCD34D;">"Forward to Supplier"</b></p>
    </div>
  </div>
</div>
</body>
</html>"""
    _send_gmail(your_email, subject, html)


def send_to_supplier(order, invoice_id, supplier_email, your_email):
    subject = f"New Order to Arrange — {order['order_id']} | {order['product_name']}"
    subtotal = order["total_price"]
    tax      = subtotal * 0.18
    grand    = subtotal + tax

    html = f"""
<html>
<body style="margin:0;padding:0;background:#0F172A;font-family:'Segoe UI',Arial,sans-serif;">
<div style="max-width:580px;margin:40px auto;">
  <div style="height:5px;background:linear-gradient(90deg,#F59E0B,#FCD34D);border-radius:8px 8px 0 0;"></div>
  <div style="background:#1C1917;padding:28px 36px;border:1px solid #292524;border-top:none;">
    <div style="display:flex;align-items:center;gap:14px;margin-bottom:20px;">
      <div style="background:linear-gradient(135deg,#D97706,#F59E0B);width:44px;height:44px;border-radius:10px;text-align:center;line-height:44px;font-size:22px;">📦</div>
      <div>
        <div style="color:white;font-size:18px;font-weight:700;">MobileMart Pakistan</div>
        <div style="color:#A8A29E;font-size:12px;">Supplier Arrangement Request</div>
      </div>
    </div>
    <p style="color:#E7E5E4;font-size:14px;line-height:1.7;margin:0 0 20px;">
      Dear Supplier, please arrange the following approved order and dispatch to the customer.
    </p>
    <div style="background:#0C0A09;border:1px solid #292524;border-radius:10px;overflow:hidden;margin-bottom:16px;">
      <div style="background:#292524;padding:10px 18px;"><span style="color:#FCD34D;font-size:11px;font-weight:700;text-transform:uppercase;">Order Details</span></div>
      <div style="padding:16px 18px;">
        <table style="width:100%;border-collapse:collapse;font-size:13px;">
          <tr><td style="color:#78716C;padding:7px 0;width:45%">Order ID</td><td style="color:#FCD34D;font-weight:700">{order['order_id']}</td></tr>
          <tr><td style="color:#78716C;padding:7px 0">Product</td><td style="color:#E7E5E4;font-weight:600">{order['product_name']}</td></tr>
          <tr><td style="color:#78716C;padding:7px 0">Brand / Model</td><td style="color:#E7E5E4">{order['brand']} {order['model']}</td></tr>
          <tr><td style="color:#78716C;padding:7px 0">Quantity</td><td style="color:#E7E5E4;font-weight:700">{order['quantity']} unit(s)</td></tr>
          <tr><td style="color:#78716C;padding:7px 0">Subtotal</td><td style="color:#E7E5E4">PKR {subtotal:,.0f}</td></tr>
          <tr><td style="color:#78716C;padding:7px 0">Tax (18%)</td><td style="color:#E7E5E4">PKR {tax:,.0f}</td></tr>
          <tr><td style="color:#78716C;padding:10px 0;font-weight:700">Grand Total</td><td style="color:#34D399;font-size:16px;font-weight:700">PKR {grand:,.0f}</td></tr>
        </table>
      </div>
    </div>
    <div style="background:#0C0A09;border:1px solid #292524;border-radius:10px;overflow:hidden;margin-bottom:16px;">
      <div style="background:#292524;padding:10px 18px;"><span style="color:#FCD34D;font-size:11px;font-weight:700;text-transform:uppercase;">Delivery Info</span></div>
      <div style="padding:16px 18px;">
        <table style="width:100%;border-collapse:collapse;font-size:13px;">
          <tr><td style="color:#78716C;padding:7px 0;width:45%">Customer</td><td style="color:#E7E5E4;font-weight:600">{order['customer_name']}</td></tr>
          <tr><td style="color:#78716C;padding:7px 0">Phone</td><td style="color:#E7E5E4">{order['customer_phone']}</td></tr>
          <tr><td style="color:#78716C;padding:7px 0">Address</td><td style="color:#FBBF24;font-weight:600">{order['delivery_address']}</td></tr>
        </table>
      </div>
    </div>
    <div style="text-align:center;padding:14px;background:#1C1917;border:1px solid #292524;border-radius:8px;">
      <p style="color:#A8A29E;font-size:12px;margin:0;">Dispatch within 24 hours. Contact: <span style="color:#FCD34D">{your_email}</span></p>
    </div>
  </div>
</div>
</body>
</html>"""

    update_invoice_status(invoice_id, "FORWARDED TO SUPPLIER",
                          "supplier_email", supplier_email)
    update_order_status(order["order_id"], "DISPATCHED TO SUPPLIER")
    _send_gmail(supplier_email, subject, html)
    print(f"[EMAIL] Supplier notified for {order['order_id']}")