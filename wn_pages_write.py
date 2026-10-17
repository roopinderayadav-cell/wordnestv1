"""Wordnest - Write with us, My dashboard (articles, books, royalties, notifications), Account."""
import json

import streamlit as st

import wn_auth
import wn_db
import wn_moderation
import wn_pdf
from wn_seed import ARTICLE_CATEGORIES, BOOK_CATEGORIES, DEMO_AUTHOR, DEMO_EMPLOYER, DEMO_READER, DEMO_SEEKER, LANGUAGES
from wn_ui import PAGES, decision_badge, esc, fmt_date, rupees, show_review, shrink_image

STATUS_TEXT = {"ai_blocked": "Blocked by AI review", "pending": "Waiting for editor", "published": "Live",
               "rejected": "Rejected by editor", "unpublished": "Taken down"}

GUIDELINES_REMINDER = """
**Before you write, please remember**

Not allowed on Wordnest:
- Sexual, pornographic or adult content
- Abusive, hateful or offensive language about any person, religion, caste, community or gender
- Anything about governments, political parties, politicians or elections (opinions, praise or criticism)
- Violence, threats, self-harm, drugs, gambling, scams or other illegal activity
- Other people's personal details (phone numbers, emails, ID numbers, addresses)
- Copied text, photos or chapters you do not own

Every article is checked by our **AI review bot** and then by an **editor**. Blocked submissions count as a strike;
after 3 strikes the account is suspended.
"""


def _status_badge(status):
    colors = {"published": ("#145C40", "#DDF1E6"), "pending": ("#7A4B00", "#FBEBC8"),
              "ai_blocked": ("#8B1E2B", "#F8DDE0"), "rejected": ("#8B1E2B", "#F8DDE0"),
              "unpublished": ("#3D4844", "#E6E9E5")}
    fg, bg = colors.get(status, ("#3D4844", "#E6E9E5"))
    return f'<span class="wn-badge" style="color:{fg};background:{bg}">{STATUS_TEXT.get(status, status)}</span>'


def apply_decision(user, item_type, item_id, title, report):
    """Set the status after AI review, tell the writer, and count strikes for serious blocks."""
    table = "articles" if item_type == "article" else "books"
    auto = wn_db.get_setting("auto_publish_on_pass") == "1" and report.get("ai_used")
    if report["decision"] == "block":
        status = "ai_blocked"
    elif report["decision"] == "pass" and auto and item_type == "article":
        status = "published"
    else:
        status = "pending"
    wn_db.x(f"UPDATE {table} SET status=?, ai_decision=?, ai_report=?, published_at=? WHERE id=?",
            (status, report["decision"], json.dumps(report), wn_db.now() if status == "published" else None, item_id))
    wn_db.log_moderation(item_type, item_id, report["decision"], report.get("engine", "rules"), report)
    if status == "ai_blocked":
        reasons = "; ".join(report.get("reasons", [])[:3]) or "it breaks our content guidelines"
        wn_db.notify(user["id"], f"Not published: {title}",
                     f"Our AI review blocked your {item_type} because {reasons}. Please edit it and submit again. "
                     "Reminder: Wordnest does not allow adult, abusive, violent or political content.")
        if wn_moderation.is_serious(report):
            strikes = user["strikes"] + 1
            max_strikes = int(wn_db.get_setting_num("max_strikes"))
            if strikes >= max_strikes:
                wn_db.x("UPDATE users SET strikes=?, status='suspended' WHERE id=?", (strikes, user["id"]))
                wn_db.notify(user["id"], "Account suspended",
                             f"Your account reached {strikes} strikes for adult or abusive content and has been "
                             "suspended. Contact the grievance officer if you think this is a mistake.")
            else:
                wn_db.x("UPDATE users SET strikes=? WHERE id=?", (strikes, user["id"]))
                wn_db.notify(user["id"], "Warning: strike added",
                             f"This is strike {strikes} of {max_strikes}. Repeated adult or abusive submissions "
                             "will suspend your account.")
    elif status == "published":
        wn_db.notify(user["id"], f"Published: {title}", "Your article passed review and is now live. Thank you!")
    else:
        wn_db.notify(user["id"], f"Submitted: {title}",
                     "Your submission passed the first check and is waiting for an editor. You will be notified here.")
    return status


# ---------------------------------------------------------------- Write with us
def page_write():
    user = wn_auth.current_user()
    st.markdown('<h1 class="wn-serif" style="font-size:46px;margin-bottom:0">Write with us</h1>', unsafe_allow_html=True)
    st.caption("Share your experience, ideas and stories. Free to publish; books earn up to 70% royalty.")
    left, right = st.columns([1.7, 1], gap="large")
    with right:
        st.markdown(f'<div class="wn-note">{_md_to_html(GUIDELINES_REMINDER)}</div>', unsafe_allow_html=True)
        st.write("")
        st.page_link(PAGES["policies"], label="Full content guidelines", icon=":material/gavel:",
                     query_params={"p": "guidelines"})
        st.page_link(PAGES["policies"], label="Disclaimer", icon=":material/info:", query_params={"p": "disclaimer"})
        st.page_link(PAGES["dashboard"], label="Want to publish a book? Use My dashboard", icon=":material/auto_stories:")
    with left:
        if not user:
            st.info("Please sign in or create a free account to write for Wordnest.")
            st.page_link(PAGES["account"], label="Sign in / Create account", icon=":material/login:")
            return
        if user["status"] == "suspended":
            st.error("Your account is suspended because of repeated guideline breaks. Contact the grievance officer.")
            return
        edit = None
        try:
            edit_id = int(st.query_params.get("edit") or 0)
        except ValueError:
            edit_id = 0
        if edit_id:
            edit = wn_db.q("SELECT * FROM articles WHERE id=? AND author_id=? AND kind='article'", (edit_id, user["id"]),
                           one=True)
            if edit:
                st.info(f"Editing: {edit['title']}. Fix the points from the review and submit again.")
        result = st.session_state.pop("write_result", None)
        if result:
            st.markdown(f"#### Review result · {STATUS_TEXT.get(result['status'], result['status'])}")
            show_review(result["report"])
            if result["status"] == "ai_blocked":
                st.page_link(PAGES["write"], label="Edit and resubmit", icon=":material/edit:",
                             query_params={"edit": result["id"]})
            st.divider()

        with st.form("write_form", clear_on_submit=False):
            title = st.text_input("Title", value=edit["title"] if edit else "", max_chars=140)
            c1, c2 = st.columns(2)
            cat = c1.selectbox("Category", ARTICLE_CATEGORIES,
                               index=ARTICLE_CATEGORIES.index(edit["category"]) if edit and edit["category"] in ARTICLE_CATEGORIES else 0)
            lang = c2.selectbox("Language", LANGUAGES,
                                index=LANGUAGES.index(edit["language"]) if edit and edit["language"] in LANGUAGES else 0)
            summary = st.text_area("Short summary (shown on cards)", value=edit["summary"] if edit else "",
                                   max_chars=240, height=80)
            body = st.text_area("Your article", value=edit["body"] if edit else "", height=360,
                                help="Plain text. Use **bold** for emphasis and a blank line between paragraphs.")
            cover = st.file_uploader("Cover picture (optional, your own photo)", type=["jpg", "jpeg", "png", "webp"])
            st.markdown("**Please confirm**")
            a1 = st.checkbox("This is my own original writing and photo, not copied from anywhere.")
            a2 = st.checkbox("It follows the Wordnest content guidelines (no adult, abusive, violent or political content).")
            a3 = st.checkbox("I understand I am fully responsible for what I write. Wordnest and SHROOP Global do not "
                             "endorse or take responsibility for community content, and may remove it at any time.")
            b1, b2 = st.columns(2)
            check = b1.form_submit_button("Check with AI first", icon=":material/fact_check:", width="stretch")
            send = b2.form_submit_button("Submit for review", type="primary", icon=":material/send:", width="stretch")

        text = f"{title}\n{summary}\n{body}"
        if check or send:
            problems = []
            if len(title.strip()) < 10:
                problems.append("Title should be at least 10 characters.")
            if len(body.split()) < 80:
                problems.append(f"Article is {len(body.split())} words. Please write at least 80 words.")
            if send and not (a1 and a2 and a3):
                problems.append("Please tick all three confirmations.")
            if problems:
                for p in problems:
                    st.error(p)
                return
            with st.spinner("AI review bot is reading your article..."):
                report = wn_moderation.review(text, "article")
            if check:
                st.markdown("#### AI check (nothing has been submitted yet)")
                show_review(report)
                return
            cover_bytes, mime = (shrink_image(cover.getvalue()) if cover else (None, None))
            if edit:
                wn_db.x("UPDATE articles SET title=?, summary=?, body=?, category=?, language=?, admin_note=NULL, "
                        "cover=COALESCE(?, cover), cover_mime=COALESCE(?, cover_mime) WHERE id=?",
                        (title.strip(), summary.strip(), body.strip(), cat, lang, cover_bytes, mime, edit["id"]))
                aid = edit["id"]
            else:
                aid = wn_db.x("INSERT INTO articles(kind, title, summary, body, category, language, author_id, cover, "
                              "cover_mime, status, created_at) VALUES ('article',?,?,?,?,?,?,?,?, 'pending', ?)",
                              (title.strip(), summary.strip(), body.strip(), cat, lang, user["id"], cover_bytes, mime,
                               wn_db.now()))
            status = apply_decision(user, "article", aid, title.strip(), report)
            st.session_state["write_result"] = {"id": aid, "status": status, "report": report}
            st.query_params.clear()
            st.rerun()


def _md_to_html(md):
    out, in_list = [], False
    for line in md.strip().splitlines():
        line = esc(line).replace("**", "\u0000")
        parts = line.split("\u0000")
        line = "".join(f"<b>{p}</b>" if i % 2 else p for i, p in enumerate(parts))
        if line.startswith("- "):
            if not in_list:
                out.append('<ul style="margin:4px 0 10px 18px;padding:0">')
                in_list = True
            out.append(f"<li>{line[2:]}</li>")
        else:
            if in_list:
                out.append("</ul>")
                in_list = False
            if line.strip():
                out.append(f'<p style="margin:0 0 8px">{line}</p>')
    if in_list:
        out.append("</ul>")
    return "".join(out)


# ---------------------------------------------------------------- My dashboard
def page_dashboard():
    user = wn_auth.current_user()
    if not user:
        st.info("Please sign in to see your dashboard.")
        st.page_link(PAGES["account"], label="Sign in / Create account", icon=":material/login:")
        return
    st.markdown(f'<h1 class="wn-serif" style="font-size:42px;margin-bottom:0">Welcome back, {esc(wn_auth.display_name(user))}</h1>',
                unsafe_allow_html=True)
    st.caption("Your articles, books, earnings and messages in one place.")
    if user["status"] == "suspended":
        st.error("Your account is suspended. You can still read and download your books.")
    arts = wn_db.q("SELECT id, title, category, status, ai_decision, ai_report, admin_note, views, created_at, published_at "
                   "FROM articles WHERE author_id=? AND kind='article' ORDER BY id DESC", (user["id"],))
    books = wn_db.list_books(status=None, author_id=user["id"])
    sales = wn_db.q("SELECT o.*, b.title FROM orders o JOIN books b ON b.id=o.book_id WHERE b.author_id=? "
                    "ORDER BY o.id DESC", (user["id"],))
    earned = sum(s["author_share"] for s in sales)
    unread = wn_db.unread_count(user["id"])

    m = st.columns(5)
    m[0].metric("Articles live", sum(a["status"] == "published" for a in arts))
    m[1].metric("Waiting for review", sum(a["status"] == "pending" for a in arts) + sum(b["status"] == "pending" for b in books))
    m[2].metric("Books live", sum(b["status"] == "published" for b in books))
    m[3].metric("Royalty earned", rupees(earned) if earned else "₹0")
    m[4].metric("New messages", unread)

    tabs = st.tabs([f"Messages ({unread})", "My articles", "My books and royalties", "Publish a book", "My library",
                    "Profile"])
    with tabs[0]:
        notes = wn_db.q("SELECT * FROM notifications WHERE user_id=? ORDER BY id DESC LIMIT 50", (user["id"],))
        if unread and st.button("Mark all as read"):
            wn_db.x("UPDATE notifications SET is_read=1 WHERE user_id=?", (user["id"],))
            st.rerun()
        for n in notes:
            with st.container(border=True):
                st.markdown(f"{'**● ' if not n['is_read'] else '**'}{esc(n['title'])}**  \n"
                            f"<span class='wn-meta'>{fmt_date(n['created_at'])}</span>", unsafe_allow_html=True)
                st.write(n["message"])
        if not notes:
            st.caption("No messages yet.")
    with tabs[1]:
        st.page_link(PAGES["write"], label="Write a new article", icon=":material/add:")
        if not arts:
            st.caption("You have not written any articles yet.")
        for a in arts:
            with st.container(border=True):
                c1, c2 = st.columns([3, 1.4], vertical_alignment="center")
                c1.markdown(f"**{esc(a['title'])}**  \n<span class='wn-meta'>{esc(a['category'])} · "
                            f"{fmt_date(a['created_at'])} · {a['views']} reads</span>", unsafe_allow_html=True)
                c2.markdown(_status_badge(a["status"]), unsafe_allow_html=True)
                if a["admin_note"]:
                    st.caption(f"Editor's note: {a['admin_note']}")
                lc = st.columns([1, 1, 3])
                lc[0].page_link(PAGES["article"], label="View", query_params={"id": a["id"]})
                if a["status"] in ("ai_blocked", "rejected", "pending"):
                    lc[1].page_link(PAGES["write"], label="Edit", query_params={"edit": a["id"]})
                if a["ai_report"]:
                    with st.expander("AI review details"):
                        show_review(json.loads(a["ai_report"]))
    with tabs[2]:
        roy = int(wn_db.get_setting_num("royalty_pct"))
        st.markdown(f"You keep **{roy}%** of each sale after GST and payment gateway fees. Royalties are paid monthly.")
        if not books:
            st.caption("No books yet. Use the 'Publish a book' tab.")
        for b in books:
            bs = [s for s in sales if s["book_id"] == b["id"]]
            with st.container(border=True):
                c1, c2, c3, c4 = st.columns([3, 1, 1, 1.4], vertical_alignment="center")
                c1.markdown(f"**{esc(b['title'])}**  \n<span class='wn-meta'>{esc(b['language'])} · "
                            f"{rupees(b['price'])}</span>", unsafe_allow_html=True)
                c2.metric("Sold", len(bs))
                c3.metric("Earned", rupees(sum(s["author_share"] for s in bs)) if bs else "₹0")
                c4.markdown(_status_badge(b["status"]), unsafe_allow_html=True)
                if b["price"]:
                    sp = wn_db.money_split(b["price"])
                    st.caption(f"Per sale: price {rupees(sp['amount'])} − GST {rupees(sp['gst'])} − gateway fee "
                               f"{rupees(sp['fee'])} = {rupees(sp['net'])} net → your share {rupees(sp['author'])}")
    with tabs[3]:
        _book_form(user)
    with tabs[4]:
        owned = wn_db.q("SELECT b.id, b.title, b.author_display, o.created_at FROM orders o JOIN books b ON b.id=o.book_id "
                        "WHERE o.user_id=? ORDER BY o.id DESC", (user["id"],))
        if not owned:
            st.caption("Books you buy appear here.")
        for o in owned:
            c1, c2 = st.columns([4, 1])
            c1.markdown(f"**{esc(o['title'])}** · {esc(o['author_display'])} · bought {fmt_date(o['created_at'])}")
            c2.page_link(PAGES["book"], label="Open", query_params={"id": o["id"]})
    with tabs[5]:
        with st.form("profile"):
            pen = st.text_input("Pen name (shown on your articles and books)", value=user["pen_name"] or "")
            bio = st.text_area("Short bio", value=user["bio"] or "", max_chars=300)
            if st.form_submit_button("Save profile", type="primary"):
                wn_db.x("UPDATE users SET pen_name=?, bio=? WHERE id=?", (pen.strip() or user["name"], bio.strip(), user["id"]))
                st.success("Saved.")
        st.caption(f"Signed in as {user['email']} · role: {user['role']} · strikes: {user['strikes']}")


def _book_form(user):
    if user["status"] == "suspended":
        st.error("Suspended accounts cannot submit books.")
        return
    roy = int(wn_db.get_setting_num("royalty_pct"))
    st.markdown(f"Upload your ebook as a PDF. Our AI bot checks the title, description and opening pages, then an editor "
                f"approves it. You keep the copyright and **{roy}%** of net sales.")
    with st.form("book_form", clear_on_submit=True):
        title = st.text_input("Book title", max_chars=140)
        subtitle = st.text_input("Subtitle (optional)", max_chars=160)
        c1, c2, c3 = st.columns(3)
        cat = c1.selectbox("Category", BOOK_CATEGORIES)
        lang = c2.selectbox("Language", LANGUAGES)
        price = c3.number_input("Price in ₹ (0 = free)", 0, 5000, 199, step=10)
        desc = st.text_area("Description (back-cover text)", max_chars=1500)
        isbn = st.text_input("ISBN (optional)")
        pdf = st.file_uploader("Manuscript PDF", type=["pdf"])
        cover = st.file_uploader("Cover image (JPG or PNG, about 1600 × 2400)", type=["jpg", "jpeg", "png", "webp"])
        a1 = st.checkbox("I wrote this book and own all rights to its text and cover.")
        a2 = st.checkbox(f"I agree to the royalty terms ({roy}% to me) and that Wordnest may remove the book if it breaks "
                         "the guidelines.")
        sent = st.form_submit_button("Submit book for review", type="primary")
    if sent:
        if len(title.strip()) < 2 or not pdf or not (a1 and a2):
            st.error("Please add a title, the PDF and tick both confirmations.")
            return
        pdf_bytes = pdf.getvalue()
        pages = wn_pdf.page_count(pdf_bytes)
        if not pages:
            st.error("That PDF could not be read. Please export it again from Word and retry.")
            return
        cover_bytes, mime = (shrink_image(cover.getvalue(), 1600) if cover else (None, None))
        with st.spinner("AI review bot is checking your book..."):
            report = wn_moderation.review(f"{title}\n{subtitle}\n{desc}\n{wn_pdf.first_pages_text(pdf_bytes)}", "book")
        bid = wn_db.x("INSERT INTO books(title, subtitle, author_id, author_display, description, category, language, price, "
                      "pages, isbn, cover, cover_mime, pdf, status, created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?, 'pending', ?)",
                      (title.strip(), subtitle.strip() or None, user["id"], wn_auth.display_name(user), desc.strip(), cat,
                       lang, int(price), pages, isbn.strip() or None, cover_bytes, mime, pdf_bytes, wn_db.now()))
        status = apply_decision(user, "book", bid, title.strip(), report)
        st.markdown(f"#### {_status_badge(status)}", unsafe_allow_html=True)
        show_review(report)


# ---------------------------------------------------------------- Account
def page_account():
    user = wn_auth.current_user()
    st.markdown('<h1 class="wn-serif" style="font-size:42px">Your account</h1>', unsafe_allow_html=True)
    if user:
        st.success(f"Signed in as **{user['email']}** ({user['role']}).")
        c = st.columns(3)
        c[0].page_link(PAGES["dashboard"], label="My dashboard", icon=":material/dashboard:")
        if wn_auth.is_staff(user):
            c[1].page_link(PAGES["admin"], label="Admin panel", icon=":material/admin_panel_settings:")
        if c[2].button("Sign out", icon=":material/logout:"):
            wn_auth.logout()
            st.rerun()
        return
    left, right = st.columns([1.3, 1], gap="large")
    with left:
        t1, t2 = st.tabs(["Sign in", "Create account"])
        with t1:
            with st.form("login"):
                email = st.text_input("Email")
                pw = st.text_input("Password", type="password")
                if st.form_submit_button("Sign in", type="primary"):
                    u, err = wn_auth.login(email, pw)
                    if err:
                        st.error(err)
                    else:
                        if wn_db.unread_count(u["id"]):
                            st.session_state["toast"] = "You have new messages in My dashboard."
                        if u["role"] in ("admin", "editor"):
                            st.switch_page(PAGES["admin"])
                        elif wn_db.company_of(u["id"]):
                            st.switch_page(PAGES["employers"])
                        elif wn_db.candidate(u["id"]):
                            st.switch_page(PAGES["career"])
                        st.switch_page(PAGES["dashboard"])
        with t2:
            with st.form("signup"):
                name = st.text_input("Full name (private, for payments)")
                pen = st.text_input("Pen name (shown publicly, optional)")
                email = st.text_input("Email ")
                pw = st.text_input("Password (8+ characters)", type="password")
                goal = st.radio("I am here to", ["Find a job", "Hire people", "Read and write"], horizontal=True)
                ok = st.checkbox("I agree to the Terms of use, Privacy policy and Content guidelines.")
                if st.form_submit_button("Create account", type="primary"):
                    if not ok:
                        st.error("Please accept the terms to continue.")
                    else:
                        uid, err = wn_auth.register(email, name, pen, pw)
                        if err:
                            st.error(err)
                        else:
                            st.session_state["user_id"] = uid
                            st.switch_page(PAGES[{"Find a job": "career", "Hire people": "employers"}.get(goal, "dashboard")])
    with right:
        with st.container(border=True):
            st.markdown("**Demo accounts** (for trying the demo)")
            st.markdown(f"- Job seeker: `{DEMO_SEEKER[0]}` / `{DEMO_SEEKER[1]}`\n"
                        f"- Employer: `{DEMO_EMPLOYER[0]}` / `{DEMO_EMPLOYER[1]}`\n"
                        f"- Reader: `{DEMO_READER[0]}` / `{DEMO_READER[1]}`\n"
                        f"- Author (R.K. Yadav): `{DEMO_AUTHOR[0]}` / `{DEMO_AUTHOR[1]}`")
            if wn_auth.using_default_admin():
                st.markdown(f"- Admin: `{wn_auth.DEFAULT_ADMIN_EMAIL}` / `{wn_auth.DEFAULT_ADMIN_PASSWORD}`")
                st.caption("Set ADMIN_EMAIL and ADMIN_PASSWORD in Streamlit secrets to replace the default admin.")
            else:
                st.caption("Admin: use the ADMIN_EMAIL and ADMIN_PASSWORD from your Streamlit secrets.")
