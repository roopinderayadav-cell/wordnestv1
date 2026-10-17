"""Wordnest - look and feel, shared building blocks (cards, covers, disclaimer, footer)."""
import base64
import datetime
import html
import io

import streamlit as st

import wn_auth
import wn_db

PAGES = {}  # filled in app.py so every page can link to every other page

GREEN, INK, BG, AMBER, LINE, MUTED = "#1F6F5C", "#1C2321", "#F6F7F4", "#E0A43A", "#DDE2DC", "#4A5551"

CATEGORY_COLORS = {
    "Travel Destinations": "#2E6F8E", "Travel Industry": "#1F6F5C", "Technology": "#2B3A55",
    "Careers & Jobs": "#5B4A8B", "Food & Recipes": "#B5562F", "Lifestyle": "#8C2F39",
    "Geopolitics": "#2B3A55", "Industry Update": "#1F6F5C", "Job Market": "#5B4A8B",
    "Economy": "#B7791F", "Entertainment": "#8C2F39", "Sport": "#2E6F8E",
}

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,400;8..60,600;8..60,700&family=Manrope:wght@400;500;600;700&display=swap');
html, body, .stApp, .stMarkdown, button, input, textarea, select, label { font-family: 'Manrope', system-ui, sans-serif; }
.stApp { background: #F6F7F4; color: #1C2321; }
[data-testid="stMainBlockContainer"] { max-width: 1240px; padding-top: 4.5rem; padding-bottom: 2rem; }
h1, h2, h3, .wn-serif { font-family: 'Source Serif 4', Georgia, serif !important; color: #1C2321; letter-spacing: -0.3px; }
h1 { font-weight: 700 !important; }
a { color: #1F6F5C; }
[data-testid="stBaseButton-primary"], .stButton button[kind="primary"], .stFormSubmitButton button[kind="primaryFormSubmit"] {
  background: #1F6F5C; border-color: #1F6F5C; color: #fff; border-radius: 999px; font-weight: 700; }
[data-testid="stBaseButton-primary"]:hover { background: #164F42; border-color: #164F42; color: #fff; }
.stButton button, .stDownloadButton button, .stFormSubmitButton button { border-radius: 999px; font-weight: 600; min-height: 44px; }
[data-testid="stPageLink"] a { border-radius: 999px; }
/* pill links */
[class*="st-key-links"] [data-testid="stPageLink"] a { background:#fff; border:1px solid #C9D0C8; padding:.45rem 1rem; }
[class*="st-key-cta"] [data-testid="stPageLink"] a { background:#1F6F5C; padding:.6rem 1.2rem; }
[class*="st-key-cta"] [data-testid="stPageLink"] a p, [class*="st-key-cta"] [data-testid="stPageLink"] a span { color:#fff !important; font-weight:700; }
[class*="st-key-amber"] [data-testid="stPageLink"] a { background:#E0A43A; padding:.6rem 1.2rem; }
[class*="st-key-amber"] [data-testid="stPageLink"] a p { color:#1C2321 !important; font-weight:700; }
/* cards */
.wn-card { background:#fff; border:1px solid #DDE2DC; border-radius:16px; overflow:hidden; height:100%; }
.wn-thumb { height:170px; display:flex; align-items:flex-end; padding:16px; box-sizing:border-box; color:#fff;
  font-family:'Source Serif 4', Georgia, serif; font-size:22px; font-weight:700; background-size:cover; background-position:center; }
.wn-thumb.lg { height:240px; font-size:30px; }
.wn-body { padding:16px 18px 6px; }
.wn-kicker { font-size:12px; font-weight:700; letter-spacing:1.2px; text-transform:uppercase; color:#1F6F5C; }
.wn-title { font-family:'Source Serif 4', Georgia, serif; font-size:21px; line-height:1.25; font-weight:600; margin:6px 0 8px; color:#1C2321; }
.wn-title.lg { font-size:30px; }
.wn-sum { font-size:15px; line-height:1.55; color:#4A5551; margin:0 0 10px; }
.wn-meta { font-size:13px; color:#5F6A66; }
.wn-row { display:flex; gap:14px; align-items:flex-start; padding:12px 0; border-bottom:1px solid #E6E9E5; }
.wn-row .wn-dot { flex:none; width:64px; height:64px; border-radius:10px; }
.wn-row .wn-title { font-size:17px; margin:2px 0 4px; }
/* hero */
.wn-hero { background:#fff; border:1px solid #DDE2DC; border-radius:24px; padding:44px 44px 36px; }
.wn-hero h1 { font-size:52px; line-height:1.05; margin:10px 0 16px; }
.wn-hero p { font-size:18px; line-height:1.6; color:#4A5551; max-width:560px; }
.wn-eyebrow { font-size:13px; font-weight:700; letter-spacing:1.6px; text-transform:uppercase; color:#1F6F5C; }
.wn-shelf { display:flex; gap:14px; align-items:flex-end; justify-content:center; padding:26px 10px 10px; }
/* book covers */
.wn-cover { border-radius:5px 12px 12px 5px; padding:16px; box-sizing:border-box; display:flex; flex-direction:column;
  justify-content:space-between; color:#fff; box-shadow: inset 6px 0 0 rgba(0,0,0,.12); overflow:hidden; }
.wn-cover .t { font-family:'Source Serif 4', Georgia, serif; font-weight:700; line-height:1.1; word-break:normal; overflow-wrap:normal; }
.wn-facts { display:grid; grid-template-columns:repeat(auto-fill,minmax(130px,1fr)); gap:14px; border-top:1px solid #DDE2DC; padding-top:16px; margin-top:8px; }
.wn-facts span { display:block; font-size:12.5px; color:#5F6A66; } .wn-facts b { font-size:16px; }
.wn-cover .a { font-size:11px; font-weight:700; letter-spacing:1.4px; }
.wn-cover img { width:100%; height:100%; object-fit:cover; border-radius:inherit; }
.wn-price { font-size:20px; font-weight:700; color:#1C2321; }
.wn-badge { display:inline-block; font-size:12px; font-weight:700; border-radius:999px; padding:4px 10px; }
.wn-free { background:#DDF1E6; color:#145C40; }
/* bands */
.wn-dark { background:#1C2321; color:#fff; border-radius:24px; padding:40px; }
.wn-dark h2 { color:#fff !important; font-size:38px; margin:8px 0 12px; }
.wn-dark p { color:#D3D9D5; font-size:17px; line-height:1.6; }
.wn-step { background:#262F2C; border-radius:14px; padding:16px 18px; margin-bottom:10px; color:#D3D9D5; font-size:15px; }
.wn-step b { color:#fff; display:block; font-size:17px; }
.wn-note { background:#FFF7E6; border:1px solid #F1D9A6; border-radius:14px; padding:16px 18px; font-size:14.5px; line-height:1.6; color:#4A3B12; }
.wn-disclaimer { background:#EEF0EB; border-radius:12px; padding:14px 16px; font-size:13.5px; line-height:1.6; color:#4A5551; }
.wn-reader { background:#FFFDF8; border:1px solid #E6E4DC; border-radius:16px; padding:40px 48px; font-family:'Source Serif 4', Georgia, serif; line-height:1.85; color:#2A2F2D; }
.wn-reader.night { background:#191C1B; color:#E4E2DA; border-color:#2C302E; }
.wn-chip { display:inline-block; font-size:12.5px; background:#EEF0EB; color:#33403C; border-radius:999px; padding:3px 10px; margin:0 6px 6px 0; }
.wn-step-chip { font-size:14px; font-weight:600; background:#fff; border:1px solid #DDE2DC; border-radius:12px; padding:10px 12px; color:#5F6A66; }
.wn-step-chip.done { background:#DDF1E6; border-color:#BFE3CF; color:#145C40; }
.wn-question { font-family:'Source Serif 4', Georgia, serif; font-size:24px; line-height:1.35; background:#fff; border:1px solid #DDE2DC; border-radius:16px; padding:22px 24px; margin:10px 0 14px; }
.wn-job-hero { background:#1F6F5C; border-radius:24px; padding:40px 40px 30px; color:#fff; }
.wn-job-hero h1 { color:#fff !important; font-size:48px; line-height:1.08; margin:8px 0 12px; }
.wn-job-hero p { color:#D8ECE5; font-size:18px; line-height:1.55; max-width:640px; }
.wn-mini-book { display:flex; gap:12px; align-items:center; padding:8px 0; border-bottom:1px solid #EEF0EB; }
.wn-footer { border-top:1px solid #DDE2DC; margin-top:48px; padding-top:28px; font-size:14px; color:#4A5551; }
.wn-section-title { display:flex; justify-content:space-between; align-items:flex-end; margin:36px 0 14px; }
.wn-section-title h2 { margin:0; font-size:32px; }
@media (max-width: 760px) { .wn-hero { padding:26px 20px; } .wn-hero h1 { font-size:36px; } .wn-reader { padding:24px 20px; } .wn-dark { padding:26px 20px; } }
</style>
"""


def inject_css():
    st.markdown(CSS, unsafe_allow_html=True)


def esc(s):
    return html.escape(str(s or ""))


def fmt_date(ts):
    if not ts:
        return ""
    try:
        return datetime.datetime.fromisoformat(ts).strftime("%d %b %Y")
    except ValueError:
        return ts[:10]


def ago(ts):
    try:
        d = datetime.datetime.now() - datetime.datetime.fromisoformat(ts)
    except (TypeError, ValueError):
        return ""
    s = int(d.total_seconds())
    if s < 0:
        return fmt_date(ts)
    if s < 3600:
        return f"{max(s // 60, 1)} min ago"
    if s < 86400:
        n = s // 3600
        return f"{n} hour{'s' if n > 1 else ''} ago"
    if s < 86400 * 7:
        n = s // 86400
        return f"{n} day{'s' if n > 1 else ''} ago"
    return fmt_date(ts)


def rupees(n):
    return "Free" if not n else f"₹{int(n):,}" if float(n).is_integer() else f"₹{n:,.2f}"


@st.cache_data(max_entries=500, show_spinner=False)
def cover_data_uri(table, item_id, stamp):
    c = wn_db.get_cover(table, item_id)
    if not c:
        return None
    data, mime = c
    return f"data:{mime};base64,{base64.b64encode(data).decode()}"


def shrink_image(file_bytes, max_side=1400):
    """Resize uploads so pages stay fast. Returns (bytes, mime)."""
    from PIL import Image
    img = Image.open(io.BytesIO(file_bytes))
    img.thumbnail((max_side, max_side))
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")
    out = io.BytesIO()
    img.save(out, format="JPEG", quality=85)
    return out.getvalue(), "image/jpeg"


def author_of(row):
    return row.get("pen_name") or row.get("user_name") or "Wordnest"


def thumb_html(row, large=False, table="articles"):
    color = CATEGORY_COLORS.get(row.get("category"), GREEN)
    uri = cover_data_uri(table, row["id"], row.get("published_at") or row.get("created_at")) if row.get("has_cover") else None
    cls = "wn-thumb lg" if large else "wn-thumb"
    if uri:
        return f'<div class="{cls}" style="background-image:url({uri})"></div>'
    return (f'<div class="{cls}" style="background:linear-gradient(135deg,{color} 0%,{color}CC 60%,#1C2321 140%)">'
            f'{esc(row.get("category"))}</div>')


def article_card(row, large=False, news=False):
    """Card with picture, category, title, summary and a link to read."""
    with st.container():
        meta = (f'{ago(row.get("published_at"))} · {esc(row.get("source_name") or "Wordnest")}' if news
                else f'{esc(author_of(row))} · {fmt_date(row.get("published_at"))}')
        st.markdown(
            f'<div class="wn-card">{thumb_html(row, large)}<div class="wn-body">'
            f'<span class="wn-kicker">{esc(row["category"])}</span>'
            f'<div class="wn-title{" lg" if large else ""}">{esc(row["title"])}</div>'
            f'<p class="wn-sum">{esc(row.get("summary"))}</p><span class="wn-meta">{meta}</span></div></div>',
            unsafe_allow_html=True)
        st.page_link(PAGES["article"], label="Read more", icon=":material/arrow_forward:",
                     query_params={"id": row["id"]})


def news_row(row):
    color = CATEGORY_COLORS.get(row.get("category"), GREEN)
    c1, c2 = st.columns([5, 1], vertical_alignment="center")
    with c1:
        st.markdown(
            f'<div class="wn-row" style="border:none;padding:6px 0"><div class="wn-dot" style="background:linear-gradient(135deg,{color},#1C2321)"></div>'
            f'<div><div class="wn-title">{esc(row["title"])}</div><span class="wn-meta">{ago(row.get("published_at"))} · '
            f'<b style="color:{GREEN}">{esc(row["category"])}</b></span></div></div>', unsafe_allow_html=True)
    with c2:
        st.page_link(PAGES["article"], label="Read", query_params={"id": row["id"]})


def book_cover_html(book, width=150, height=225, title_size=20):
    uri = cover_data_uri("books", book["id"], book.get("published_at") or book.get("created_at")) if book.get("has_cover") else None
    if uri:
        return (f'<div class="wn-cover" style="width:{width}px;height:{height}px;padding:0">'
                f'<img src="{uri}" alt="Cover of {esc(book["title"])}"></div>')
    color = book.get("cover_color") or GREEN
    ink = "#1C2321" if color.upper() in ("#E0A43A", "#B7791F") else "#FFFFFF"
    if width < 90:  # thumbnail: colour block with initials only
        initials = "".join(w[0] for w in str(book["title"]).split()[:3] if w[0].isalnum()).upper()
        return (f'<div class="wn-cover" style="flex:none;width:{width}px;height:{height}px;background:{color};color:{ink};'
                f'padding:8px;justify-content:center;align-items:center"><span class="t" style="font-size:16px">'
                f'{esc(initials)}</span></div>')
    longest = max((len(w) for w in str(book["title"]).split()), default=1)
    size = min(title_size, int((width - 34) / (longest * 0.56)))  # keep the longest word on one line
    return (f'<div class="wn-cover" style="width:{width}px;height:{height}px;background:{color};color:{ink}">'
            f'<span class="t" style="font-size:{size}px">{esc(book["title"])}</span>'
            f'<span class="a">{esc(book["author_display"]).upper()}</span></div>')


def book_card(book, owned=False):
    with st.container(border=True):
        st.markdown(f'<div style="display:flex;justify-content:center">{book_cover_html(book, 170, 250, 21)}</div>',
                    unsafe_allow_html=True)
        st.markdown(
            f'<div class="wn-title" style="font-size:18px;margin-top:10px">{esc(book["title"])}</div>'
            f'<div class="wn-meta">{esc(book["author_display"])}</div>'
            f'<div class="wn-meta" style="margin:2px 0 8px">{esc(book["category"])} · {esc(book["language"])}</div>'
            + (f'<span class="wn-badge wn-free">In your library</span>' if owned else
               f'<div class="wn-price">{rupees(book["price"])}</div>'),
            unsafe_allow_html=True)
        st.page_link(PAGES["book"], label="Read now" if (owned or not book["price"]) else "Read sample · Buy",
                     icon=":material/menu_book:", query_params={"id": book["id"]})


def section_title(title, link_page=None, link_label=None, query_params=None):
    c1, c2 = st.columns([4, 1], vertical_alignment="bottom")
    c1.markdown(f"## {title}")
    if link_page:
        c2.page_link(PAGES[link_page], label=link_label, icon=":material/arrow_forward:", query_params=query_params)


DISCLAIMER = ("**Disclaimer:** Articles and books by community writers are their own views. "
              "Wordnest and its operator SHROOP Global do not endorse, support or take responsibility for opinions, "
              "claims or content written by users. Every piece is checked by our AI review bot and an editor, "
              "but if you find something wrong, offensive or unsafe, please report it and we will act on it.")


def disclaimer_box(item_type, item_id, key):
    st.markdown(f'<div class="wn-disclaimer">{DISCLAIMER.replace("**Disclaimer:**", "<b>Disclaimer:</b>")}</div>',
                unsafe_allow_html=True)
    if st.button("Report this content", icon=":material/flag:", key=f"report_{key}"):
        report_dialog(item_type, item_id)


@st.dialog("Report this content")
def report_dialog(item_type, item_id):
    reason = st.selectbox("What is wrong?", [
        "Offensive or abusive", "Sexual or adult content", "Political or government content",
        "False or misleading information", "Copied from somewhere else", "Personal information exposed", "Other"])
    details = st.text_area("Tell us more (optional)", max_chars=1000)
    if st.button("Send report", type="primary"):
        user = wn_auth.current_user()
        wn_db.x("INSERT INTO reports(item_type, item_id, user_id, reason, details, created_at) VALUES (?,?,?,?,?,?)",
                (item_type, item_id, user["id"] if user else None, reason, details, wn_db.now()))
        st.success("Thank you. Our team will review this within 24 hours.")


def decision_badge(decision):
    colors = {"pass": ("#145C40", "#DDF1E6", "Passed AI review"),
              "review": ("#7A4B00", "#FBEBC8", "Needs editor review"),
              "block": ("#8B1E2B", "#F8DDE0", "Blocked by AI review")}
    fg, bg, label = colors.get(decision, ("#3D4844", "#E6E9E5", decision or "Not checked"))
    return f'<span class="wn-badge" style="color:{fg};background:{bg}">{label}</span>'


def show_review(report):
    """Readable AI review result for writers and editors."""
    st.markdown(decision_badge(report.get("decision")) +
                f' <span class="wn-meta">Checked by: {esc(report.get("engine", "rules"))}</span>', unsafe_allow_html=True)
    if report.get("summary"):
        st.write(report["summary"])
    if report.get("labels"):
        st.markdown("**Flagged:** " + ", ".join(report["labels"]))
    for r in report.get("reasons", []):
        st.markdown(f"- {r}")
    if report.get("suggestions"):
        st.markdown("**How to fix it:**")
        for s in report["suggestions"]:
            st.markdown(f"- {s}")
    for n in report.get("notes", []):
        st.caption(n)


def footer():
    st.markdown('<div class="wn-footer"></div>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns([2.2, 1, 1, 1])
    with c1:
        st.markdown('<div class="wn-serif" style="font-size:24px;font-weight:700">Wordnest</div>', unsafe_allow_html=True)
        st.caption("Jobs, news and reading for your working life. Wordnest is operated by SHROOP Global, Uttar Pradesh, India. "
                   "Free for job seekers: no employer may ask you for money.")
        st.caption("Views in community articles are their authors' own. Wordnest does not endorse them or take "
                   "responsibility for them. See our disclaimer.")
    with c2:
        st.markdown("**Explore**")
        st.page_link(PAGES["jobs"], label="Jobs")
        st.page_link(PAGES["employers"], label="For employers")
        st.page_link(PAGES["news"], label="Daily News")
        st.page_link(PAGES["articles"], label="Articles")
        st.page_link(PAGES["books"], label="Books")
    with c3:
        st.markdown("**Write**")
        st.page_link(PAGES["write"], label="Write with us")
        st.page_link(PAGES["policies"], label="Content guidelines", query_params={"p": "guidelines"})
        st.page_link(PAGES["policies"], label="Royalty terms", query_params={"p": "royalty"})
    with c4:
        st.markdown("**Company**")
        st.page_link(PAGES["policies"], label="Disclaimer", query_params={"p": "disclaimer"})
        st.page_link(PAGES["policies"], label="Terms and privacy", query_params={"p": "terms"})
        st.page_link(PAGES["policies"], label="Refunds", query_params={"p": "refunds"})
        st.page_link(PAGES["policies"], label="Grievance and contact", query_params={"p": "grievance"})
    st.caption("© 2026 Wordnest. Articles and books remain the copyright of their authors.")
