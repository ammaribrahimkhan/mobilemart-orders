"""
pdf_invoice.py — Generates PDF in memory (no disk write needed for Render).
"""

import io
import uuid
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT

DARK_BLUE   = colors.HexColor("#1A2E5A")
ACCENT_BLUE = colors.HexColor("#1565C0")
LIGHT_BLUE  = colors.HexColor("#E3F2FD")
LIGHT_GREY  = colors.HexColor("#F5F5F5")
MID_GREY    = colors.HexColor("#B0BEC5")
WHITE       = colors.white
GREEN       = colors.HexColor("#1B5E20")


def make_styles():
    base = getSampleStyleSheet()
    return {
        "company":       ParagraphStyle("co", parent=base["Title"],   fontSize=26, textColor=WHITE,      fontName="Helvetica-Bold", alignment=TA_LEFT,   spaceAfter=0),
        "tagline":       ParagraphStyle("tl", parent=base["Normal"],  fontSize=10, textColor=colors.HexColor("#90CAF9"), fontName="Helvetica", alignment=TA_LEFT),
        "invoice_title": ParagraphStyle("it", parent=base["Title"],   fontSize=28, textColor=WHITE,      fontName="Helvetica-Bold", alignment=TA_RIGHT,  spaceAfter=0),
        "invoice_sub":   ParagraphStyle("is", parent=base["Normal"],  fontSize=10, textColor=colors.HexColor("#90CAF9"), fontName="Helvetica", alignment=TA_RIGHT),
        "section_label": ParagraphStyle("sl", parent=base["Normal"],  fontSize=8,  textColor=colors.HexColor("#607D8B"), fontName="Helvetica-Bold", spaceAfter=2),
        "normal":        ParagraphStyle("nm", parent=base["Normal"],  fontSize=10, textColor=colors.HexColor("#212121"), fontName="Helvetica", leading=16),
        "bold":          ParagraphStyle("bd", parent=base["Normal"],  fontSize=10, textColor=DARK_BLUE,  fontName="Helvetica-Bold", leading=16),
        "footer":        ParagraphStyle("ft", parent=base["Normal"],  fontSize=8,  textColor=MID_GREY,  fontName="Helvetica", alignment=TA_CENTER),
    }


def generate_invoice_bytes(order, invoice_id=None):
    """
    Generates a PDF invoice and returns (pdf_bytes, invoice_id).
    Works both locally and on Render (no disk needed).
    """
    if not isinstance(order, dict):
        order = dict(order)

    if not invoice_id:
        invoice_id = f"INV-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:6].upper()}"

    buffer    = io.BytesIO()
    generated = datetime.now().strftime("%d %B %Y")
    styles    = make_styles()

    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=1.5*cm, rightMargin=1.5*cm,
        topMargin=1.5*cm,  bottomMargin=1.5*cm
    )
    story = []

    # Header
    header_data = [[
        Paragraph("MobileMart Pakistan", styles["company"]),
        Paragraph("INVOICE", styles["invoice_title"])
    ],[
        Paragraph("Your Trusted Mobile & Accessories Partner", styles["tagline"]),
        Paragraph(f"Invoice No: {invoice_id}", styles["invoice_sub"])
    ]]
    ht = Table(header_data, colWidths=[10*cm, 8*cm])
    ht.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), DARK_BLUE),
        ("PADDING",    (0,0), (-1,-1), 14),
        ("VALIGN",     (0,0), (-1,-1), "MIDDLE"),
    ]))
    story.append(ht)
    story.append(Spacer(1, 16))

    # Meta row
    meta_data = [[
        Paragraph("DATE ISSUED", styles["section_label"]),
        Paragraph("ORDER ID",    styles["section_label"]),
        Paragraph("ORDER DATE",  styles["section_label"]),
        Paragraph("STATUS",      styles["section_label"]),
    ],[
        Paragraph(generated,                    styles["bold"]),
        Paragraph(order["order_id"],            styles["bold"]),
        Paragraph(str(order["order_date"])[:10],styles["bold"]),
        Paragraph(order["status"],              styles["bold"]),
    ]]
    mt = Table(meta_data, colWidths=[4.5*cm]*4)
    mt.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), LIGHT_BLUE),
        ("PADDING",    (0,0), (-1,-1), 10),
        ("GRID",       (0,0), (-1,-1), 0.3, MID_GREY),
    ]))
    story.append(mt)
    story.append(Spacer(1, 16))

    # Bill to / Ship to
    bill_data = [[
        Paragraph("BILL TO", styles["section_label"]),
        Paragraph("SHIP TO", styles["section_label"]),
    ],[
        Paragraph(f"<b>{order['customer_name']}</b>", styles["normal"]),
        Paragraph(order["delivery_address"],           styles["normal"]),
    ],[
        Paragraph(order["customer_email"], styles["normal"]),
        Paragraph("", styles["normal"]),
    ],[
        Paragraph(order["customer_phone"], styles["normal"]),
        Paragraph("", styles["normal"]),
    ]]
    bt = Table(bill_data, colWidths=[9*cm, 9*cm])
    bt.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), LIGHT_GREY),
        ("PADDING",    (0,0), (-1,-1), 8),
        ("LINEABOVE",  (0,0), (-1,0), 1.5, ACCENT_BLUE),
        ("LINEBEFORE", (1,0), (1,-1), 0.5, MID_GREY),
        ("VALIGN",     (0,0), (-1,-1), "TOP"),
    ]))
    story.append(bt)
    story.append(Spacer(1, 20))

    # Items table
    story.append(Paragraph("ORDER DETAILS", styles["section_label"]))
    story.append(Spacer(1, 6))
    items = [
        ["#", "Product Name", "Brand", "Category", "Model", "Qty", "Unit Price (PKR)", "Total (PKR)"],
        ["1", order["product_name"], order["brand"], order["category"],
         order["model"], str(order["quantity"]),
         f"{order['unit_price']:,.0f}", f"{order['total_price']:,.0f}"]
    ]
    it = Table(items, colWidths=[0.8*cm,4.5*cm,2.2*cm,2.2*cm,2.5*cm,1*cm,2.5*cm,2.3*cm], repeatRows=1)
    it.setStyle(TableStyle([
        ("BACKGROUND",     (0,0), (-1,0), ACCENT_BLUE),
        ("TEXTCOLOR",      (0,0), (-1,0), WHITE),
        ("FONTNAME",       (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",       (0,0), (-1,0), 8.5),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [WHITE, LIGHT_GREY]),
        ("FONTNAME",       (0,1), (-1,-1), "Helvetica"),
        ("FONTSIZE",       (0,1), (-1,-1), 9),
        ("ALIGN",          (0,0), (-1,-1), "CENTER"),
        ("ALIGN",          (1,1), (4,-1), "LEFT"),
        ("ALIGN",          (6,0), (-1,-1), "RIGHT"),
        ("PADDING",        (0,0), (-1,-1), 7),
        ("GRID",           (0,0), (-1,-1), 0.4, MID_GREY),
    ]))
    story.append(it)
    story.append(Spacer(1, 8))

    # Totals
    subtotal = order["total_price"]
    tax_amt  = subtotal * 0.18
    grand    = subtotal + tax_amt
    tt = Table([
        ["", "Subtotal:",    f"PKR {subtotal:,.0f}"],
        ["", "Tax (18%):",   f"PKR {tax_amt:,.0f}"],
        ["", "GRAND TOTAL:", f"PKR {grand:,.0f}"],
    ], colWidths=[10.5*cm, 4*cm, 3.5*cm])
    tt.setStyle(TableStyle([
        ("FONTNAME",   (1,0), (-1,1), "Helvetica"),
        ("FONTSIZE",   (1,0), (-1,1), 10),
        ("FONTNAME",   (1,2), (-1,2), "Helvetica-Bold"),
        ("FONTSIZE",   (1,2), (-1,2), 12),
        ("BACKGROUND", (1,2), (-1,2), DARK_BLUE),
        ("TEXTCOLOR",  (1,2), (-1,2), WHITE),
        ("ALIGN",      (1,0), (-1,-1), "RIGHT"),
        ("PADDING",    (0,0), (-1,-1), 7),
    ]))
    story.append(tt)
    story.append(Spacer(1, 24))

    # Footer
    story.append(HRFlowable(width="100%", thickness=1, color=MID_GREY))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        f"MobileMart Pakistan  |  info@mobilemart.pk  |  0800-MOBILE  |  Invoice: {invoice_id}  |  {generated}",
        styles["footer"]
    ))

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes, invoice_id