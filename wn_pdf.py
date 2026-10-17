"""Wordnest - PDF helpers: page images for the reader, text view, buyer watermark, demo PDFs."""
import io

import streamlit as st
from pypdf import PdfReader, PdfWriter
from reportlab.lib.pagesizes import A5
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

import wn_db


def page_count(pdf_bytes):
    try:
        return len(PdfReader(io.BytesIO(pdf_bytes)).pages)
    except Exception:
        return 0


@st.cache_data(max_entries=300, show_spinner=False)
def render_page(book_id, stamp, page_no, scale=1.6):
    """Render one PDF page to PNG (keeps the exact layout, works for Hindi too)."""
    import pypdfium2 as pdfium
    pdf_bytes = wn_db.get_book_pdf(book_id)
    if not pdf_bytes:
        return None
    doc = pdfium.PdfDocument(pdf_bytes)
    try:
        page = doc[page_no]
        img = page.render(scale=scale).to_pil()
        buf = io.BytesIO()
        img.save(buf, format="PNG", optimize=True)
        return buf.getvalue()
    finally:
        doc.close()


@st.cache_data(max_entries=300, show_spinner=False)
def page_text(book_id, stamp, page_no):
    pdf_bytes = wn_db.get_book_pdf(book_id)
    if not pdf_bytes:
        return ""
    try:
        return PdfReader(io.BytesIO(pdf_bytes)).pages[page_no].extract_text() or ""
    except Exception:
        return ""


def first_pages_text(pdf_bytes, pages=15):
    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
        return "\n".join((p.extract_text() or "") for p in reader.pages[:pages])
    except Exception:
        return ""


def watermark(pdf_bytes, text):
    """Stamp the buyer's details on the footer of every page (discourages sharing)."""
    reader = PdfReader(io.BytesIO(pdf_bytes))
    writer = PdfWriter()
    overlays = {}
    for page in reader.pages:
        w = float(page.mediabox.width)
        h = float(page.mediabox.height)
        key = (round(w), round(h))
        if key not in overlays:
            buf = io.BytesIO()
            c = canvas.Canvas(buf, pagesize=(w, h))
            c.setFont("Helvetica", 6.5)
            c.setFillGray(0.45)
            c.drawCentredString(w / 2, 10, text)
            c.save()
            buf.seek(0)
            overlays[key] = PdfReader(buf).pages[0]
        page.merge_page(overlays[key])
        writer.add_page(page)
    out = io.BytesIO()
    writer.write(out)
    return out.getvalue()


def demo_book_pdf(title, author, color_hex, chapters=8, pages_per_chapter=3):
    """A clearly labelled placeholder book so the reader and downloads can be tried before real manuscripts are uploaded."""
    buf = io.BytesIO()
    W, H = A5
    c = canvas.Canvas(buf, pagesize=A5)
    c.setTitle(title)
    c.setAuthor(author)
    # cover
    c.setFillColor(color_hex)
    c.rect(0, 0, W, H, stroke=0, fill=1)
    c.setFillColor("#FFFFFF")
    c.setFont("Times-Bold", 26)
    y = H - 60 * mm
    for line in _wrap(title, 18):
        c.drawCentredString(W / 2, y, line)
        y -= 30
    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(W / 2, 22 * mm, author.upper())
    c.showPage()
    body = ("This page is placeholder text for the Wordnest demo. It shows how the online reader, "
            "chapter navigation, free sample pages and the watermarked PDF download work. "
            "Upload the real manuscript PDF from the Admin panel to replace this demo book.")
    for ch in range(1, chapters + 1):
        for p in range(pages_per_chapter):
            c.setFillColor("#1C2321")
            if p == 0:
                c.setFont("Helvetica-Bold", 9)
                c.setFillColor(color_hex)
                c.drawString(18 * mm, H - 30 * mm, f"CHAPTER {ch}")
                c.setFillColor("#1C2321")
                c.setFont("Times-Bold", 20)
                c.drawString(18 * mm, H - 42 * mm, f"Chapter {ch} title")
                y = H - 58 * mm
            else:
                y = H - 25 * mm
            c.setFont("Times-Roman", 11.5)
            for _ in range(3 if p == 0 else 4):
                for line in _wrap(body, 62):
                    c.drawString(18 * mm, y, line)
                    y -= 16
                y -= 10
            c.setFont("Helvetica", 8)
            c.setFillColor("#5F6A66")
            c.drawCentredString(W / 2, 12 * mm, f"{title}  ·  page {c.getPageNumber()}")
            c.showPage()
    c.save()
    return buf.getvalue()


def _wrap(text, width):
    words, lines, cur = text.split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 > width:
            lines.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}".strip()
    if cur:
        lines.append(cur)
    return lines


def demo_cv_pdf():
    """A short sample CV for the demo job seeker (fictional person)."""
    buf = io.BytesIO()
    from reportlab.lib.pagesizes import A4
    W, H = A4
    c = canvas.Canvas(buf, pagesize=A4)
    y = H - 60
    c.setFont("Helvetica-Bold", 20)
    c.drawString(50, y, "Priya Sharma (demo profile)")
    y -= 20
    c.setFont("Helvetica", 10)
    c.drawString(50, y, "Noida, India  |  priya.demo@example.com  |  98000 00000")
    sections = [
        ("SUMMARY", ["Air ticketing executive with 4 years in corporate travel for US clients. Amadeus, reissues,",
                     "refunds and fare rules. Quality score above 98% for six months in a row."]),
        ("EXPERIENCE", ["Ticketing Executive, a travel management company, Noida   2022 - present",
                        "- Issue, reissue and refund 60+ tickets a day on Amadeus for US corporate travellers",
                        "- Created a reissue checklist now used by a team of 14; reduced errors by 30%",
                        "Travel Associate, a travel agency, Delhi   2021 - 2022",
                        "- Domestic bookings, hotel reservations and customer calls"]),
        ("SKILLS", ["Amadeus, ticketing, reissues, refunds, fare rules, queue handling, customer service,",
                    "advanced Excel (VLOOKUP, pivot tables), English and Hindi"]),
        ("EDUCATION", ["B.Com, University of Delhi, 2021  |  IATA Foundation in Travel and Tourism"]),
    ]
    for head, lines in sections:
        y -= 34
        c.setFont("Helvetica-Bold", 11)
        c.drawString(50, y, head)
        c.setFont("Helvetica", 10)
        for line in lines:
            y -= 16
            c.drawString(50, y, line)
    c.save()
    return buf.getvalue()
