"""Wordnest - Books: store, book page, online reader, checkout and PDF download."""
import uuid

import streamlit as st

import wn_auth
import wn_db
import wn_pdf
from wn_seed import BOOK_CATEGORIES
from wn_ui import PAGES, book_card, book_cover_html, disclaimer_box, esc, fmt_date, rupees


def _qp(name, default=None):
    v = st.query_params.get(name)
    return v if v not in (None, "") else default


# ---------------------------------------------------------------- store
def page_books():
    user = wn_auth.current_user()
    st.markdown('<h1 class="wn-serif" style="font-size:46px;margin-bottom:0">Discover Books</h1>', unsafe_allow_html=True)
    st.caption("Read online or download as PDF. Free and paid books from Wordnest writers.")
    options = ["All books", "Free", "Paid"] + BOOK_CATEGORIES + ["My library"]
    c1, c2 = st.columns([3.4, 1.2], vertical_alignment="bottom")
    with c1:
        start = _qp("category", "All books")
        pick = st.pills("Filter", options, default=start if start in options else "All books", required=True,
                        label_visibility="collapsed", key="book_filter")
    search = c2.text_input("Search", placeholder="Search books or authors", label_visibility="collapsed")
    books = wn_db.list_books(search=search.strip() or None)
    owned = {r["book_id"] for r in wn_db.q("SELECT book_id FROM orders WHERE user_id=?", (user["id"],))} if user else set()
    if pick == "Free":
        books = [b for b in books if not b["price"]]
    elif pick == "Paid":
        books = [b for b in books if b["price"]]
    elif pick == "My library":
        if not user:
            st.info("Sign in to see the books you own.")
            st.page_link(PAGES["account"], label="Sign in", icon=":material/login:")
            return
        books = [b for b in books if b["id"] in owned]
    elif pick in BOOK_CATEGORIES:
        books = [b for b in books if b["category"] == pick]
    if not books:
        st.info("No books here yet.")
        return
    per_row = 5
    for i in range(0, len(books), per_row):
        cols = st.columns(per_row, gap="small")
        for col, b in zip(cols, books[i:i + per_row]):
            with col:
                book_card(b, owned=b["id"] in owned)


# ---------------------------------------------------------------- checkout
@st.dialog("Checkout", width="medium")
def checkout_dialog(book_id):
    user = wn_auth.current_user()
    book = wn_db.get_book(book_id)
    if not user:
        st.write("Please sign in or create a free account to buy this book. Your books stay in **My library**.")
        st.page_link(PAGES["account"], label="Sign in / Create account", icon=":material/login:")
        return
    split = wn_db.money_split(book["price"])
    st.markdown(f"### {esc(book['title'])}")
    st.caption(f"by {book['author_display']} · Read online + PDF download")
    c1, c2 = st.columns(2)
    c1.metric("Price", rupees(book["price"]))
    c2.metric("Includes GST", rupees(split["gst"]))
    st.radio("Pay with", ["UPI", "Debit / credit card", "Net banking"], horizontal=True)
    st.info("Demo mode: no money is charged. The live website will take payment through Razorpay "
            "(UPI, cards, net banking) and issue a GST invoice from SHROOP Global.")
    if st.button(f"Pay {rupees(book['price'])} (demo)", type="primary", width="stretch"):
        ref = "DEMO-" + uuid.uuid4().hex[:8].upper()
        wn_db.create_order(user["id"], book_id, book["price"], ref)
        wn_db.notify(user["id"], "Purchase successful",
                     f"'{book['title']}' is now in My library. Payment reference {ref}.")
        if book["author_id"] and book["author_id"] != user["id"]:
            wn_db.notify(book["author_id"], "You made a sale",
                         f"A reader bought '{book['title']}'. Your royalty: {rupees(split['author'])}.")
        st.session_state["just_bought"] = book_id
        st.rerun()


@st.cache_data(max_entries=50, show_spinner="Preparing your PDF...")
def _download_bytes(book_id, stamp, stamp_text):
    return wn_pdf.watermark(wn_db.get_book_pdf(book_id), stamp_text)


# ---------------------------------------------------------------- book page + reader
def page_book():
    user = wn_auth.current_user()
    try:
        bid = int(_qp("id", 0))
    except ValueError:
        bid = 0
    book = wn_db.get_book(bid) if bid else None
    can_preview = book and user and (wn_auth.is_staff(user) or user["id"] == book["author_id"])
    if not book or (book["status"] != "published" and not can_preview):
        st.warning("This book is not available.")
        st.page_link(PAGES["books"], label="Back to books", icon=":material/arrow_back:")
        return
    if st.session_state.pop("just_bought", None) == bid:
        st.toast("Purchase complete. Enjoy your book!", icon=":material/check_circle:")
    free = not book["price"]
    owned = free or wn_db.owns_book(user["id"] if user else None, bid) or (user and user["id"] == book["author_id"]) \
        or wn_auth.is_staff(user)
    stamp = book["published_at"] or book["created_at"]

    st.page_link(PAGES["books"], label="Books", icon=":material/arrow_back:")
    c1, c2 = st.columns([1, 2.2], gap="large")
    with c1:
        st.markdown(f'<div style="display:flex;justify-content:center">{book_cover_html(book, 280, 420, 32)}</div>',
                    unsafe_allow_html=True)
    with c2:
        st.markdown(f'<span class="wn-kicker">{esc(book["category"])} · {esc(book["language"])}</span>'
                    f'<h1 class="wn-serif" style="font-size:46px;line-height:1.05;margin:8px 0 6px">{esc(book["title"])}</h1>'
                    + (f'<p style="font-size:19px;color:#4A5551;margin:0 0 6px">{esc(book["subtitle"])}</p>' if book["subtitle"] else "")
                    + f'<p>by <b style="color:#1F6F5C">{esc(book["author_display"])}</b></p>'
                    f'<p style="font-size:17px;line-height:1.7;color:#33403C">{esc(book["description"])}</p>',
                    unsafe_allow_html=True)
        if book["status"] != "published":
            st.info(f"Preview only. Status: {book['status'].replace('_', ' ')}.")
        if owned:
            st.markdown('<span class="wn-badge wn-free">'
                        + ("Free book" if free and not wn_db.owns_book(user["id"] if user else None, bid) else "In your library")
                        + "</span>", unsafe_allow_html=True)
            who = user["email"] if user else "Free copy"
            label = f"Licensed to {who} · Wordnest · Please do not share" if not free else f"Free copy from Wordnest · {who}"
            if book["has_pdf"]:
                st.download_button("Download PDF", data=_download_bytes(bid, stamp, label), type="primary",
                                   file_name=f"{book['title'].replace(' ', '_')}.pdf", mime="application/pdf",
                                   icon=":material/download:")
            st.caption("Read the full book online below, or download the PDF. Your page is remembered.")
        else:
            st.markdown(f'<div class="wn-price" style="font-size:30px">{rupees(book["price"])}</div>'
                        '<p class="wn-meta">One price: read online for life + download the PDF. Includes GST.</p>',
                        unsafe_allow_html=True)
            if st.button("Buy now", type="primary", icon=":material/shopping_cart:"):
                checkout_dialog(bid)
            st.caption("The first pages are free to read online below.")
        st.caption("Secure payment by UPI, card or net banking. Sold by SHROOP Global. Mobile app coming later.")
        st.markdown(f'<div class="wn-facts"><div><span>Pages</span><b>{book["pages"] or "-"}</b></div>'
                    f'<div><span>Language</span><b>{esc(book["language"])}</b></div>'
                    f'<div><span>Published</span><b>{fmt_date(book["published_on"] or book["published_at"]) or "-"}</b></div>'
                    f'<div><span>ISBN</span><b>{esc(book["isbn"] or "-")}</b></div></div>', unsafe_allow_html=True)

    st.divider()
    _reader(book, user, owned, stamp)
    st.write("")
    disclaimer_box("book", bid, f"b{bid}")


def _reader(book, user, owned, stamp):
    bid = book["id"]
    st.markdown("## Read online")
    if not book["has_pdf"]:
        st.info("The manuscript for this book has not been uploaded yet.")
        return
    total = book["pages"] or wn_pdf.page_count(wn_db.get_book_pdf(bid))
    sample = book["sample_pages"] or int(wn_db.get_setting_num("sample_pages"))
    allowed = total if owned else min(sample, total)
    key = f"page_{bid}"
    if key not in st.session_state:
        st.session_state[key] = min(wn_db.get_progress(user["id"], bid), allowed - 1) if user else 0

    t1, t2, t3, t4 = st.columns([1.6, 1.3, 1, 1.4], vertical_alignment="center")
    mode = t1.segmented_control("View", ["Book pages", "Text view"], default="Book pages", required=True,
                                key=f"mode_{bid}", label_visibility="collapsed")
    size = t2.select_slider("Text size", ["Small", "Medium", "Large", "Extra large"], value="Medium",
                            key=f"size_{bid}", disabled=mode != "Text view", label_visibility="collapsed")
    night = t3.toggle("Night mode", key=f"night_{bid}")
    t4.caption(f"Page {st.session_state[key] + 1} of {total}" + ("" if owned else f" · free sample: {allowed} pages"))

    page = st.session_state[key]
    left, mid, right = st.columns([1, 6, 1])
    with mid:
        if mode == "Book pages":
            png = wn_pdf.render_page(bid, stamp, page)
            if png:
                if night:
                    st.markdown('<style>.st-key-bookpage img{filter:invert(.92) hue-rotate(180deg)}</style>',
                                unsafe_allow_html=True)
                with st.container(key="bookpage", horizontal_alignment="center"):
                    st.image(png, width=620)
        else:
            text = wn_pdf.page_text(bid, stamp, page) or "(No selectable text on this page. Use Book pages view.)"
            px = {"Small": 16, "Medium": 19, "Large": 22, "Extra large": 26}[size]
            paras = "".join(f"<p>{esc(p)}</p>" for p in text.split("\n") if p.strip())
            st.markdown(f'<div class="wn-reader{" night" if night else ""}" style="font-size:{px}px">{paras}</div>',
                        unsafe_allow_html=True)
        st.progress((page + 1) / total)
        uid = user["id"] if user else None
        at_limit = page >= allowed - 1
        b1, b2, b3 = st.columns([1, 2, 1], vertical_alignment="center")
        b1.button("Previous", icon=":material/arrow_back:", disabled=page == 0, key=f"prev_{bid}",
                  on_click=_go, args=(bid, page - 1, uid))
        b3.button("Next page", icon=":material/arrow_forward:", disabled=at_limit, key=f"next_{bid}",
                  on_click=_go, args=(bid, page + 1, uid))
        jkey = f"jump_{bid}"
        if jkey not in st.session_state or st.session_state[jkey] > allowed:
            st.session_state[jkey] = page + 1
        b2.number_input("Go to page", 1, allowed, key=jkey, label_visibility="collapsed",
                        on_change=_jump, args=(bid, uid))
        if at_limit and not owned:
            st.warning(f"The free sample ends here. Buy the book for {rupees(book['price'])} to keep reading "
                       "and download the PDF.")
            if st.button("Buy now to continue", type="primary", key=f"buy_end_{bid}"):
                checkout_dialog(bid)


def _go(bid, new_page, user_id):
    st.session_state[f"page_{bid}"] = new_page
    st.session_state[f"jump_{bid}"] = new_page + 1
    if user_id:
        wn_db.save_progress(user_id, bid, new_page)


def _jump(bid, user_id):
    new_page = int(st.session_state[f"jump_{bid}"]) - 1
    st.session_state[f"page_{bid}"] = new_page
    if user_id:
        wn_db.save_progress(user_id, bid, new_page)
