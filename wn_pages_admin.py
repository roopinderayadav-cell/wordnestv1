"""Wordnest - Admin panel for the owner and editors."""
import datetime
import json

import pandas as pd
import streamlit as st

import wn_auth
import wn_db
import wn_moderation
import wn_pdf
from wn_seed import BOOK_CATEGORIES, LANGUAGES, NEWS_SECTIONS
from wn_ui import PAGES, decision_badge, esc, fmt_date, rupees, show_review, shrink_image

REMINDER_TEXT = ("A friendly reminder from the Wordnest team: please keep your writing original, respectful and safe. "
                 "Wordnest does not publish sexual or adult content, abusive or hateful language, violence, illegal "
                 "activity, other people's personal details, or anything about governments, political parties or "
                 "politicians. Every submission is checked by our AI review bot and an editor; blocked submissions "
                 "count as strikes, and 3 strikes suspend an account. Writers are responsible for their own content, "
                 "and Wordnest does not endorse or take responsibility for it. Thank you for writing with us!")


def page_admin():
    user = wn_auth.current_user()
    if not wn_auth.is_staff(user):
        st.warning("This area is for Wordnest editors and admins.")
        st.page_link(PAGES["account"], label="Sign in", icon=":material/login:")
        return
    admin = wn_auth.is_admin(user)
    st.markdown('<h1 class="wn-serif" style="font-size:42px;margin-bottom:0">Admin panel</h1>', unsafe_allow_html=True)
    import wn_ai
    st.caption(f"Review bot {wn_ai.status_text()} · Signed in as {user['email']} ({user['role']})")
    if admin and wn_auth.using_default_admin():
        st.warning("You are using the default admin password. Set ADMIN_EMAIL and ADMIN_PASSWORD in Streamlit secrets.")

    pend_a = wn_db.q("SELECT COUNT(*) n FROM articles WHERE status='pending'", one=True)["n"]
    pend_b = wn_db.q("SELECT COUNT(*) n FROM books WHERE status='pending'", one=True)["n"]
    pend_j = wn_db.q("SELECT COUNT(*) n FROM jobs WHERE status='pending'", one=True)["n"]
    pend_c = wn_db.q("SELECT COUNT(*) n FROM companies WHERE status='pending'", one=True)["n"]
    open_r = wn_db.q("SELECT COUNT(*) n FROM reports WHERE status='open'", one=True)["n"]
    names = [f"Review queue ({pend_a + pend_b + pend_j})", "Post news", f"Reports ({open_r})", "Manage content"]
    if admin:
        open_s = wn_db.q("SELECT COUNT(*) n FROM service_orders WHERE status IN ('booked','scheduled')", one=True)["n"]
        names += [f"Companies ({pend_c})", f"Career services ({open_s})", "Upload a book", "Users and reminders",
                  "Sales and royalties", "Settings"]
    tabs = st.tabs(names)
    with tabs[0]:
        _queue(user)
    with tabs[1]:
        _post_news(user)
    with tabs[2]:
        _reports()
    with tabs[3]:
        _manage()
    if admin:
        with tabs[4]:
            _companies()
        with tabs[5]:
            _service_orders()
        with tabs[6]:
            _upload_book(user)
        with tabs[7]:
            _users()
        with tabs[8]:
            _sales()
        with tabs[9]:
            _settings()


# ---------------------------------------------------------------- review queue
def _queue(editor):
    show_blocked = st.toggle("Also show items blocked by AI (to double-check)", value=False)
    states = ("pending", "ai_blocked") if show_blocked else ("pending",)
    marks = ",".join("?" * len(states))
    arts = wn_db.q(f"SELECT a.*, u.pen_name, u.email, u.strikes FROM articles a JOIN users u ON u.id=a.author_id "
                   f"WHERE a.status IN ({marks}) ORDER BY a.id", states)
    books = wn_db.q(f"SELECT id, title, subtitle, author_id, author_display, description, category, language, price, pages, "
                    f"status, ai_decision, ai_report, created_at FROM books WHERE status IN ({marks}) ORDER BY id", states)
    jobs = wn_db.q(f"SELECT j.*, c.name AS company, c.owner_id FROM jobs j JOIN companies c ON c.id=j.company_id "
                   f"WHERE j.status IN ({marks}) ORDER BY j.id", states)
    if not arts and not books and not jobs:
        st.success("Nothing waiting. All caught up.")
        return
    for j in jobs:
        with st.container(border=True):
            c1, c2 = st.columns([3, 1.3], vertical_alignment="center")
            c1.markdown(f"**{esc(j['title'])}**  \n<span class='wn-meta'>Job post · {esc(j['company'])} · {esc(j['location'])} · "
                        f"₹{j['salary_min'] or 0:,}–{j['salary_max'] or 0:,}/month</span>", unsafe_allow_html=True)
            c2.markdown(decision_badge(j["ai_decision"]), unsafe_allow_html=True)
            with st.expander("Read the job post"):
                st.markdown(j["description"])
            if j["ai_report"]:
                with st.expander("AI review report", expanded=True):
                    show_review(json.loads(j["ai_report"]))
            k = st.columns([1, 1, 3])
            if k[0].button("Approve and publish", type="primary", key=f"jok_{j['id']}"):
                wn_db.x("UPDATE jobs SET status='published', published_at=? WHERE id=?", (wn_db.now(), j["id"]))
                wn_db.notify(j["owner_id"], f"Job live: {j['title']}", "An editor approved your job post.")
                wn_db.log_moderation("job", j["id"], "approved", f"editor:{editor['email']}", {})
                st.rerun()
            if k[1].button("Reject", key=f"jno_{j['id']}"):
                wn_db.x("UPDATE jobs SET status='rejected' WHERE id=?", (j["id"],))
                wn_db.notify(j["owner_id"], f"Job not approved: {j['title']}",
                             "An editor did not approve this post. Please make sure it asks candidates for no payment and "
                             "describes the role, pay and company clearly.")
                wn_db.log_moderation("job", j["id"], "rejected", f"editor:{editor['email']}", {})
                st.rerun()
    for a in arts:
        with st.container(border=True):
            c1, c2 = st.columns([3, 1.3], vertical_alignment="center")
            c1.markdown(f"**{esc(a['title'])}**  \n<span class='wn-meta'>Article · {esc(a['category'])} · {esc(a['language'])} · "
                        f"by {esc(a['pen_name'])} ({esc(a['email'])}, strikes {a['strikes']}) · {fmt_date(a['created_at'])}</span>",
                        unsafe_allow_html=True)
            c2.markdown(decision_badge(a["ai_decision"]), unsafe_allow_html=True)
            with st.expander("Read the article"):
                st.markdown(f"*{a['summary'] or ''}*")
                st.markdown(a["body"])
            if a["ai_report"]:
                with st.expander("AI review report", expanded=a["ai_decision"] != "pass"):
                    show_review(json.loads(a["ai_report"]))
            _decide("articles", a, editor)
    for b in books:
        with st.container(border=True):
            c1, c2 = st.columns([3, 1.3], vertical_alignment="center")
            c1.markdown(f"**{esc(b['title'])}**  \n<span class='wn-meta'>Book · {esc(b['category'])} · {esc(b['language'])} · "
                        f"{rupees(b['price'])} · {b['pages']} pages · by {esc(b['author_display'])}</span>",
                        unsafe_allow_html=True)
            c2.markdown(decision_badge(b["ai_decision"]), unsafe_allow_html=True)
            st.caption(b["description"] or "")
            st.page_link(PAGES["book"], label="Open the book preview and reader", query_params={"id": b["id"]})
            if b["ai_report"]:
                with st.expander("AI review report", expanded=b["ai_decision"] != "pass"):
                    show_review(json.loads(b["ai_report"]))
            _decide("books", b, editor)


def _decide(table, item, editor):
    kind = "article" if table == "articles" else "book"
    note = st.text_input("Note to the writer (shown to them)", key=f"note_{table}_{item['id']}",
                         placeholder="Optional for approval, recommended for rejection")
    c = st.columns([1, 1, 1, 2])
    if c[0].button("Approve and publish", type="primary", key=f"ok_{table}_{item['id']}"):
        wn_db.x(f"UPDATE {table} SET status='published', published_at=?, admin_note=? WHERE id=?",
                (wn_db.now(), note or None, item["id"]))
        wn_db.notify(item["author_id"], f"Published: {item['title']}",
                     f"An editor approved your {kind}. It is now live." + (f" Note: {note}" if note else ""))
        wn_db.log_moderation(kind, item["id"], "approved", f"editor:{editor['email']}", {"note": note})
        st.rerun()
    if c[1].button("Reject", key=f"no_{table}_{item['id']}"):
        wn_db.x(f"UPDATE {table} SET status='rejected', admin_note=? WHERE id=?", (note or "Does not meet our guidelines.", item["id"]))
        wn_db.notify(item["author_id"], f"Not approved: {item['title']}",
                     f"An editor did not approve your {kind}. Reason: {note or 'it does not meet our guidelines.'} "
                     "You can edit it from My dashboard and submit again.")
        wn_db.log_moderation(kind, item["id"], "rejected", f"editor:{editor['email']}", {"note": note})
        st.rerun()
    if c[2].button("Run AI check again", key=f"ai_{table}_{item['id']}"):
        if table == "articles":
            full = wn_db.q("SELECT title, summary, body FROM articles WHERE id=?", (item["id"],), one=True)
            text = f"{full['title']}\n{full['summary']}\n{full['body']}"
        else:
            text = f"{item['title']}\n{item.get('subtitle') or ''}\n{item['description']}\n" + \
                   wn_pdf.first_pages_text(wn_db.get_book_pdf(item["id"]) or b"")
        with st.spinner("Checking..."):
            rep = wn_moderation.review(text, kind)
        wn_db.x(f"UPDATE {table} SET ai_decision=?, ai_report=? WHERE id=?", (rep["decision"], json.dumps(rep), item["id"]))
        wn_db.log_moderation(kind, item["id"], rep["decision"], rep["engine"], rep)
        st.rerun()


# ---------------------------------------------------------------- news
def _post_news(editor):
    st.markdown("Post a story to **Daily News**. Write a short summary in your own words, keep it neutral, and always "
                "credit the original source. Do not copy text or photos from other news sites.")
    result = st.session_state.pop("news_result", None)
    if result:
        st.success(result)
    with st.form(f"news_form_{st.session_state.get('news_n', 0)}"):
        c1, c2 = st.columns(2)
        section = c1.selectbox("Section", NEWS_SECTIONS)
        lang = c2.selectbox("Language", LANGUAGES)
        title = st.text_input("Headline", max_chars=140)
        summary = st.text_area("Summary (1 to 2 sentences)", max_chars=300, height=80)
        body = st.text_area("Story", height=260)
        s1, s2 = st.columns(2)
        src_name = s1.text_input("Source name (required)", placeholder="e.g. Press release, ministry website, agency")
        src_url = s2.text_input("Source link (required)", placeholder="https://")
        cover = st.file_uploader("Picture (optional: your own, licensed or free-to-use only)", type=["jpg", "jpeg", "png", "webp"])
        top = st.checkbox("Show in Today's top news")
        override = st.checkbox("Publish even if the AI asks for review (I have checked the facts and source)")
        b1, b2 = st.columns(2)
        check = b1.form_submit_button("Check with AI", width="stretch")
        publish = b2.form_submit_button("Publish story", type="primary", width="stretch")
    if not (check or publish):
        return
    if len(title.strip()) < 10 or len(body.split()) < 30 or not src_name.strip() or not src_url.strip().startswith("http"):
        st.error("Please add a headline, a story of at least 30 words, a source name and a source link starting with http.")
        return
    with st.spinner("AI review bot is checking the story..."):
        rep = wn_moderation.review(f"{title}\n{summary}\n{body}\nSource: {src_name} {src_url}", "news")
    show_review(rep)
    if check:
        return
    if rep["decision"] == "block":
        st.error("Blocked: this story breaks the universal rules (adult, abusive, violent or illegal content). Not published.")
        return
    if rep["decision"] == "review" and not override:
        st.warning("The AI asks for a second look. Fix the points above, or tick 'Publish even if the AI asks for review'.")
        return
    cover_bytes, mime = (shrink_image(cover.getvalue()) if cover else (None, None))
    nid = wn_db.x("INSERT INTO articles(kind, title, summary, body, category, language, author_id, cover, cover_mime, "
                  "source_name, source_url, is_top, status, ai_decision, ai_report, created_at, published_at) "
                  "VALUES ('news',?,?,?,?,?,?,?,?,?,?,?, 'published', ?, ?, ?, ?)",
                  (title.strip(), summary.strip(), body.strip(), section, lang, editor["id"], cover_bytes, mime,
                   src_name.strip(), src_url.strip(), int(top), rep["decision"], json.dumps(rep), wn_db.now(), wn_db.now()))
    wn_db.log_moderation("news", nid, rep["decision"], rep["engine"], rep)
    st.session_state["news_result"] = f"Published in {section}: {title.strip()}"
    st.session_state["news_n"] = st.session_state.get("news_n", 0) + 1
    st.rerun()


# ---------------------------------------------------------------- reports
def _reports():
    rows = wn_db.q("SELECT * FROM reports WHERE status='open' ORDER BY id DESC")
    if not rows:
        st.success("No open reports.")
    for r in rows:
        table = {"article": "articles", "book": "books", "job": "jobs"}.get(r["item_type"], "articles")
        item = wn_db.q(f"SELECT id, title, status FROM {table} WHERE id=?", (r["item_id"],), one=True)
        page = {"articles": "article", "books": "book", "jobs": "job"}[table]
        with st.container(border=True):
            st.markdown(f"**{esc(r['reason'])}** on {r['item_type']}: **{esc(item['title'] if item else 'deleted item')}**  \n"
                        f"<span class='wn-meta'>{fmt_date(r['created_at'])}</span>", unsafe_allow_html=True)
            if r["details"]:
                st.write(r["details"])
            c = st.columns([1.2, 1, 1, 2])
            if item:
                c[0].page_link(PAGES[page], label="Open it", query_params={"id": item["id"]})
            if item and c[1].button("Take it down", type="primary", key=f"down_{r['id']}"):
                wn_db.x(f"UPDATE {table} SET status=? WHERE id=?", ("closed" if table == "jobs" else "unpublished", item["id"]))
                wn_db.x("UPDATE reports SET status='resolved', action='taken down' WHERE id=?", (r["id"],))
                owner = (wn_db.q("SELECT c.owner_id AS author_id FROM jobs j JOIN companies c ON c.id=j.company_id WHERE j.id=?",
                                 (item["id"],), one=True) if table == "jobs" else
                         wn_db.q(f"SELECT author_id FROM {table} WHERE id=?", (item["id"],), one=True))
                if owner and owner["author_id"]:
                    wn_db.notify(owner["author_id"], f"Taken down: {item['title']}",
                                 f"After a reader report ({r['reason']}), an editor removed this from Wordnest.")
                st.rerun()
            if c[2].button("Dismiss", key=f"dismiss_{r['id']}"):
                wn_db.x("UPDATE reports SET status='resolved', action='dismissed' WHERE id=?", (r["id"],))
                st.rerun()
    done = wn_db.q("SELECT reason, item_type, item_id, action, created_at FROM reports WHERE status='resolved' ORDER BY id DESC LIMIT 50")
    if done:
        with st.expander("Resolved reports"):
            st.dataframe(pd.DataFrame(done), hide_index=True)


# ---------------------------------------------------------------- companies
def _companies():
    rows = wn_db.q("SELECT c.*, u.email AS owner_email FROM companies c JOIN users u ON u.id=c.owner_id "
                   "ORDER BY (c.status='pending') DESC, c.id DESC")
    if not rows:
        st.caption("No employers yet.")
    for c in rows:
        with st.container(border=True):
            k1, k2 = st.columns([3, 1])
            k1.markdown(f"**{esc(c['name'])}** · {esc(c['city'] or '')}  \n<span class='wn-meta'>GSTIN {esc(c['gstin'] or '-')} · "
                        f"CIN {esc(c['cin'] or '-')} · work email {esc(c['work_email'] or '-')} · account {esc(c['owner_email'])} · "
                        f"{esc(c['website'] or '')}</span>", unsafe_allow_html=True)
            k2.markdown(f"**{c['status'].title()}**")
            if c["about"]:
                st.caption(c["about"])
            st.caption("Check: GSTIN on the GST portal, the company website and that the work email uses the company domain.")
            note = st.text_input("Note to employer", key=f"cn_{c['id']}")
            b = st.columns([1, 1, 3])
            if c["status"] != "verified" and b[0].button("Verify", type="primary", key=f"cv_{c['id']}"):
                wn_db.x("UPDATE companies SET status='verified', admin_note=? WHERE id=?", (note or None, c["id"]))
                wn_db.notify(c["owner_id"], "Company verified", f"{c['name']} is verified. You can now post jobs and search candidates.")
                st.rerun()
            if c["status"] != "rejected" and b[1].button("Reject" if c["status"] == "pending" else "Suspend", key=f"cr_{c['id']}"):
                wn_db.x("UPDATE companies SET status='rejected', admin_note=? WHERE id=?", (note or "Could not verify the details.", c["id"]))
                wn_db.x("UPDATE jobs SET status='closed' WHERE company_id=? AND status='published'", (c["id"],))
                wn_db.notify(c["owner_id"], "Company not verified", f"Reason: {note or 'we could not verify the details.'}")
                st.rerun()


# ---------------------------------------------------------------- career services bookings
def _service_orders():
    rows = wn_db.q("SELECT o.*, u.email, u.name FROM service_orders o JOIN users u ON u.id=o.user_id ORDER BY o.id DESC")
    if not rows:
        st.caption("No bookings yet.")
        return
    paid = sum(r["price"] for r in rows if r["status"] != "refunded")
    m = st.columns(3)
    m[0].metric("Bookings", len(rows))
    m[1].metric("Open", sum(r["status"] in ("booked", "scheduled") for r in rows))
    m[2].metric("Revenue (demo)", f"₹{paid:,.0f}")
    for r in rows:
        with st.container(border=True):
            k1, k2 = st.columns([3, 1])
            k1.markdown(f"**{esc(r['title'])}** · {esc(r['name'])} ({esc(r['email'])})  \n<span class='wn-meta'>{esc(r['area'] or '')} · "
                        f"preferred {esc(r['preferred_slot'] or '')} · ₹{r['price']:,.0f} · ref {esc(r['payment_ref'])}</span>",
                        unsafe_allow_html=True)
            k2.markdown(f"**{r['status'].title()}**")
            if r["notes"]:
                st.caption(f"Notes: {r['notes']}")
            b = st.columns([1, 1, 1, 3])
            for col, (label, val) in zip(b, [("Scheduled", "scheduled"), ("Completed", "completed"), ("Refunded", "refunded")]):
                if r["status"] != val and col.button(label, key=f"so_{val}_{r['id']}"):
                    wn_db.x("UPDATE service_orders SET status=? WHERE id=?", (val, r["id"]))
                    wn_db.notify(r["user_id"], f"{r['title']}: {val}", f"Your booking {r['payment_ref']} is now {val}.")
                    st.rerun()


# ---------------------------------------------------------------- manage content
def _manage():
    kind = st.segmented_control("Show", ["Articles", "News", "Books", "Jobs"], default="Articles", required=True)
    if kind == "Jobs":
        rows = wn_db.q("SELECT j.id, j.title, c.name AS company, j.category, j.status, j.published_at FROM jobs j "
                       "JOIN companies c ON c.id=j.company_id ORDER BY j.id DESC")
        table = "jobs"
    elif kind == "Books":
        rows = wn_db.q("SELECT id, title, author_display AS author, category, price, status, published_at FROM books ORDER BY id DESC")
        table = "books"
    else:
        rows = wn_db.q("SELECT a.id, a.title, COALESCE(u.pen_name, u.name) AS author, a.category, a.status, a.is_top, a.views, "
                       "a.published_at FROM articles a LEFT JOIN users u ON u.id=a.author_id WHERE a.kind=? ORDER BY a.id DESC",
                       ("news" if kind == "News" else "article",))
        table = "articles"
    if not rows:
        st.caption("Nothing here yet.")
        return
    st.dataframe(pd.DataFrame(rows), hide_index=True, height=320)
    pick = st.selectbox("Choose an item", rows, format_func=lambda r: f"#{r['id']} · {r['title']} ({r['status']})")
    c = st.columns(5)
    if c[0].button("Publish", key="m_pub"):
        wn_db.x(f"UPDATE {table} SET status='published', published_at=COALESCE(published_at, ?) WHERE id=?", (wn_db.now(), pick["id"]))
        st.rerun()
    if c[1].button("Take down", key="m_down"):
        wn_db.x(f"UPDATE {table} SET status='unpublished' WHERE id=?", (pick["id"],))
        st.rerun()
    if kind == "News" and c[2].button("Toggle top story", key="m_top"):
        wn_db.x("UPDATE articles SET is_top = 1 - is_top WHERE id=?", (pick["id"],))
        st.rerun()
    if c[3].button("Delete forever", key="m_del"):
        st.session_state["confirm_delete"] = (table, pick["id"])
    conf = st.session_state.get("confirm_delete")
    if conf and conf == (table, pick["id"]):
        st.warning(f"Delete '{pick['title']}' permanently? This cannot be undone.")
        if st.button("Yes, delete", type="primary"):
            if table == "books":
                wn_db.x("DELETE FROM orders WHERE book_id=?", (pick["id"],))
            if table == "jobs":
                wn_db.x("DELETE FROM applications WHERE job_id=?", (pick["id"],))
            wn_db.x(f"DELETE FROM {table} WHERE id=?", (pick["id"],))
            st.session_state.pop("confirm_delete", None)
            st.rerun()


# ---------------------------------------------------------------- upload a book (owner's catalogue)
def _upload_book(admin):
    st.markdown("Add a book to the store directly (for example your own books). It is checked by the AI bot first.")
    msg = st.session_state.pop("book_msg", None)
    if msg:
        st.success(msg)
    with st.form("admin_book", clear_on_submit=False):
        c1, c2 = st.columns(2)
        title = c1.text_input("Title")
        author = c2.text_input("Author name shown", value="R.K. Yadav")
        subtitle = st.text_input("Subtitle (optional)")
        c3, c4, c5, c6 = st.columns(4)
        cat = c3.selectbox("Category", BOOK_CATEGORIES)
        lang = c4.selectbox("Language", LANGUAGES)
        price = c5.number_input("Price ₹ (0 = free)", 0, 5000, 299, step=10)
        sample = c6.number_input("Free sample pages", 1, 100, int(wn_db.get_setting_num("sample_pages")))
        desc = st.text_area("Description")
        c7, c8, c9 = st.columns(3)
        isbn = c7.text_input("ISBN")
        pub_on = c8.date_input("Published on", value=datetime.date.today())
        color = c9.color_picker("Cover colour (used when no cover image)", "#1F6F5C")
        pdf = st.file_uploader("Book PDF", type=["pdf"])
        cover = st.file_uploader("Cover image", type=["jpg", "jpeg", "png", "webp"])
        mine = st.checkbox("Link this book to my account for royalty reports", value=True)
        sent = st.form_submit_button("Check and publish", type="primary")
    if not sent:
        return
    if not title.strip() or not pdf:
        st.error("Title and PDF are required.")
        return
    pdf_bytes = pdf.getvalue()
    pages = wn_pdf.page_count(pdf_bytes)
    if not pages:
        st.error("That PDF could not be read.")
        return
    with st.spinner("AI review bot is checking the book..."):
        rep = wn_moderation.review(f"{title}\n{subtitle}\n{desc}\n{wn_pdf.first_pages_text(pdf_bytes)}", "book")
    show_review(rep)
    status = "published" if rep["decision"] != "block" else "ai_blocked"
    cover_bytes, mime = (shrink_image(cover.getvalue(), 1600) if cover else (None, None))
    bid = wn_db.x("INSERT INTO books(title, subtitle, author_id, author_display, description, category, language, price, pages, "
                  "isbn, published_on, cover, cover_mime, cover_color, pdf, sample_pages, status, ai_decision, ai_report, "
                  "created_at, published_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                  (title.strip(), subtitle.strip() or None, admin["id"] if mine else None, author.strip() or "Wordnest",
                   desc.strip(), cat, lang, int(price), pages, isbn.strip() or None, pub_on.isoformat(), cover_bytes, mime,
                   color, pdf_bytes, int(sample), status, rep["decision"], json.dumps(rep), wn_db.now(),
                   wn_db.now() if status == "published" else None))
    wn_db.log_moderation("book", bid, rep["decision"], rep["engine"], rep)
    if status == "published":
        st.session_state["book_msg"] = f"Published '{title.strip()}' ({pages} pages)."
        st.rerun()
    st.error("Blocked by the AI review. It was saved as blocked; you can publish it from Manage content after checking.")


# ---------------------------------------------------------------- users and reminders
def _users():
    users = wn_db.q("SELECT id, email, name, pen_name, role, status, strikes, created_at FROM users ORDER BY id")
    st.dataframe(pd.DataFrame(users), hide_index=True, height=260)
    pick = st.selectbox("Choose a user", users, format_func=lambda u: f"{u['email']} ({u['role']}, {u['status']})")
    c = st.columns(4)
    role = c[0].selectbox("Role", ["reader", "editor", "admin"], index=["reader", "editor", "admin"].index(pick["role"]))
    status = c[1].selectbox("Status", ["active", "suspended"], index=["active", "suspended"].index(pick["status"]))
    reset = c[2].checkbox("Reset strikes to 0")
    if c[3].button("Save user", type="primary"):
        wn_db.x("UPDATE users SET role=?, status=?, strikes=CASE WHEN ? THEN 0 ELSE strikes END WHERE id=?",
                (role, status, int(reset), pick["id"]))
        st.success("Saved.")
        st.rerun()

    st.divider()
    st.markdown("### Send a reminder")
    st.caption("Sends an in-app message to everyone's Messages tab. Email reminders will be added on the live website.")
    with st.form("reminder"):
        who = st.radio("Send to", ["Everyone who has written", "All users"], horizontal=True)
        title = st.text_input("Title", value="Reminder: Wordnest content guidelines")
        msg = st.text_area("Message", value=REMINDER_TEXT, height=170)
        if st.form_submit_button("Send reminder", type="primary"):
            if who == "All users":
                ids = [u["id"] for u in users]
            else:
                ids = [r["author_id"] for r in wn_db.q(
                    "SELECT DISTINCT author_id FROM articles WHERE kind='article' "
                    "UNION SELECT DISTINCT author_id FROM books WHERE author_id IS NOT NULL")]
            for uid in ids:
                wn_db.notify(uid, title, msg)
            st.success(f"Reminder sent to {len(ids)} people.")


# ---------------------------------------------------------------- sales
def _sales():
    rows = wn_db.q("SELECT o.id, o.created_at, b.title, b.author_display AS author, u.email AS buyer, o.amount, o.gst, "
                   "o.gateway_fee, o.author_share, o.platform_share, o.payment_ref FROM orders o "
                   "JOIN books b ON b.id=o.book_id JOIN users u ON u.id=o.user_id ORDER BY o.id DESC")
    paid = [r for r in rows if r["amount"]]
    m = st.columns(5)
    m[0].metric("Paid orders", len(paid))
    m[1].metric("Sales (incl. GST)", rupees(sum(r["amount"] for r in paid)))
    m[2].metric("GST collected", rupees(sum(r["gst"] for r in paid)))
    m[3].metric("Royalties owed to authors", rupees(sum(r["author_share"] for r in paid)))
    m[4].metric("Wordnest share", rupees(sum(r["platform_share"] for r in paid)))
    st.caption("All demo orders are simulated. GST rate and fees come from Settings; confirm them with your CA.")
    if rows:
        df = pd.DataFrame(rows)
        st.markdown("**Royalty payable by author**")
        st.dataframe(df.groupby("author", as_index=False)[["amount", "author_share"]].sum()
                     .rename(columns={"amount": "sales", "author_share": "royalty_payable"}), hide_index=True)
        st.markdown("**All orders**")
        st.dataframe(df, hide_index=True)
        st.download_button("Download orders (CSV)", df.to_csv(index=False).encode(), "wordnest_orders.csv", "text/csv")


# ---------------------------------------------------------------- settings
def _settings():
    with st.form("settings"):
        st.markdown("**Content review**")
        auto = st.toggle("Publish community articles automatically when the AI passes them (no editor step)",
                         value=wn_db.get_setting("auto_publish_on_pass") == "1",
                         help="Only works when the Gemini AI layer is on. Recommended OFF while the site is new.")
        strict = st.toggle("Strict government rule: block ANY mention of government or politics in community writing",
                           value=wn_db.get_setting("strict_government") == "1",
                           help="OFF: neutral practical mentions (e.g. 'apply on the government e-visa website') are allowed; "
                                "opinions or discussion about governments and politics are blocked. ON: every mention is blocked.")
        strikes = st.number_input("Strikes before suspension", 1, 10, int(wn_db.get_setting_num("max_strikes")))
        st.markdown("**Books and money**")
        c = st.columns(4)
        roy = c[0].number_input("Author royalty %", 0, 100, int(wn_db.get_setting_num("royalty_pct")))
        gst = c[1].number_input("GST % in price", 0.0, 28.0, wn_db.get_setting_num("gst_pct"), step=1.0)
        fee = c[2].number_input("Gateway fee %", 0.0, 10.0, wn_db.get_setting_num("gateway_fee_pct"), step=0.5)
        sample = c[3].number_input("Default free sample pages", 1, 100, int(wn_db.get_setting_num("sample_pages")))
        st.markdown("**Jobs: interviews and CV**")
        j = st.columns(4)
        pass_mark = j[0].number_input("Interview pass mark", 0, 100, int(wn_db.get_setting_num("pass_mark")))
        attempts = j[1].number_input("Free attempts per job area", 1, 10, int(wn_db.get_setting_num("free_attempts")))
        retake = j[2].number_input("Then one free retake every (days)", 1, 365, int(wn_db.get_setting_num("retake_days")))
        ats = j[3].number_input("ATS score below which CV help is offered", 0, 100, int(wn_db.get_setting_num("ats_threshold")))
        st.markdown("**Career services prices (₹, incl. GST)**")
        from wn_jobs_data import SERVICES
        from wn_pages_jobs import price
        pc = st.columns(len(SERVICES))
        prices = {sid: pc[i].number_input(title, 0, 50000, int(price(sid)), step=50, key=f"price_in_{sid}")
                  for i, (sid, title, _, _) in enumerate(SERVICES)}
        if st.form_submit_button("Save settings", type="primary"):
            for k, v in [("auto_publish_on_pass", int(auto)), ("strict_government", int(strict)), ("max_strikes", strikes),
                         ("royalty_pct", roy), ("gst_pct", gst), ("gateway_fee_pct", fee), ("sample_pages", sample),
                         ("pass_mark", pass_mark), ("free_attempts", attempts), ("retake_days", retake), ("ats_threshold", ats)]:
                wn_db.set_setting(k, v)
            for sid, v in prices.items():
                wn_db.set_setting(f"price_{sid}", v)
            st.success("Settings saved.")
    st.divider()
    st.markdown("**Test the AI review bot**")
    sample_text = st.text_area("Paste any text", value="A simple guide to packing for a family trip to Kerala in the monsoon.")
    kind = st.radio("Check as", ["article", "news", "book"], horizontal=True)
    if st.button("Run check"):
        with st.spinner("Checking..."):
            show_review(wn_moderation.review(sample_text, kind))
    log = wn_db.q("SELECT created_at, item_type, item_id, decision, engine FROM moderation_log ORDER BY id DESC LIMIT 100")
    if log:
        with st.expander("Moderation log (last 100 decisions)"):
            st.dataframe(pd.DataFrame(log), hide_index=True)
