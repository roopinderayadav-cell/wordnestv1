"""Wordnest - public pages: Home, Daily News, Articles, single article."""
import json

import streamlit as st

import wn_auth
import wn_db
from wn_seed import ARTICLE_CATEGORIES, NEWS_SECTIONS
from wn_ui import (CATEGORY_COLORS, PAGES, article_card, book_card, book_cover_html, disclaimer_box, esc,
                   fmt_date, news_row, section_title)


def _qp(name, default=None):
    v = st.query_params.get(name)
    return v if v not in (None, "") else default


# ---------------------------------------------------------------- Home
def page_home():
    from wn_jobs_data import FUNCTIONS
    from wn_pages_jobs import job_card
    from wn_ui import rupees

    jobs = wn_db.list_jobs(limit=6)
    n_jobs = wn_db.q("SELECT COUNT(*) n FROM jobs j JOIN companies c ON c.id=j.company_id "
                     "WHERE j.status='published' AND c.status='verified'", one=True)["n"]
    n_emp = wn_db.q("SELECT COUNT(*) n FROM companies WHERE status='verified'", one=True)["n"]
    n_cand = wn_db.q("SELECT COUNT(*) n FROM candidates WHERE visible=1", one=True)["n"]
    top_news = wn_db.list_articles("news", top_only=True, limit=5)
    if len(top_news) < 5:
        ids = {r["id"] for r in top_news}
        top_news += [r for r in wn_db.list_articles("news", limit=8) if r["id"] not in ids][:5 - len(top_news)]
    latest = wn_db.list_articles("article", limit=4)
    books = [b for b in wn_db.list_books() if b["price"]][:3] or wn_db.list_books()[:3]

    # hero with job search
    st.markdown('<div class="wn-job-hero"><span class="wn-eyebrow" style="color:#F3CF8A">Jobs · News · Articles</span>'
                '<h1 class="wn-serif">Find work you can grow in. Stay informed every day.</h1>'
                '<p>Work-from-home and office jobs from verified employers, an AI demo interview that shows recruiters what you '
                'can do, plus daily news and practical articles. Free for job seekers, always.</p></div>',
                unsafe_allow_html=True)
    with st.form("home_search", border=False):
        c1, c2, c3 = st.columns([2.4, 1.4, 0.9], vertical_alignment="bottom")
        kw = c1.text_input("What job?", placeholder="Job title, skill or company")
        loc = c2.text_input("Where?", placeholder="City or 'Work from home'")
        go = c3.form_submit_button("Search jobs", type="primary", icon=":material/search:", width="stretch")
    if go:
        params = {k: v for k, v in (("q", kw.strip()), ("loc", loc.strip())) if v}
        if loc.strip().lower() in ("work from home", "wfh", "remote"):
            params.pop("loc")
        st.switch_page(PAGES["jobs"], query_params=params or None)
    st.markdown(f'<p class="wn-meta" style="margin:-4px 0 6px"><b>{n_jobs}</b> live jobs · <b>{n_emp}</b> verified employers · '
                f'<b>{n_cand}</b> interview-ready candidates</p>', unsafe_allow_html=True)
    with st.container(horizontal=True, key="links_jobcats"):
        for fn in ["Core Operations", "Customer Support", "WFM (Workforce Management)", "Quality", "Training",
                   "BU HR / HR Business Partner", "Payroll", "Finance & Accounts", "Data Analytics", "Project Management",
                   "Risk & Compliance", "Legal"]:
            if fn in FUNCTIONS:
                st.page_link(PAGES["jobs"], label=fn.split(" (")[0], query_params={"function": fn})

    main, side = st.columns([2.4, 1], gap="large")
    with main:
        section_title("Latest jobs", "jobs", "All jobs")
        for j in jobs[:5]:
            job_card(j, compact=True)
        if not jobs:
            st.info("New jobs are coming soon.")

        section_title("Today's top news", "news", "All news")
        if top_news:
            article_card(top_news[0], large=True, news=True)
            for r in top_news[1:5]:
                news_row(r)

        section_title("Latest articles", "articles", "All articles")
        for i in range(0, len(latest), 2):
            cols = st.columns(2, gap="medium")
            for col, r in zip(cols, latest[i:i + 2]):
                with col:
                    article_card(r)

    with side:
        st.write("")
        with st.container(border=True):
            st.markdown("**Get interview-ready**")
            st.caption("Pick up to 4 job areas, get your CV's ATS score, and take the written + video demo interview. "
                       "Recruiters see your score, your videos and your real joining date.")
            with st.container(key="cta_side_career"):
                st.page_link(PAGES["career"], label="Start my job profile", icon=":material/person_add:")
        with st.container(border=True):
            st.markdown("**Hiring?**")
            st.caption("Post jobs and see pre-screened candidates with interview scores and notice periods.")
            st.page_link(PAGES["employers"], label="For employers", icon=":material/business:")
        with st.container(border=True):
            st.markdown("**From the bookshelf**")
            for b in books:
                st.markdown(f'<div class="wn-mini-book">{book_cover_html(b, 54, 80, 9)}<div><b style="font-size:14px">'
                            f'{esc(b["title"])}</b><br><span class="wn-meta">{esc(b["author_display"])} · '
                            f'{rupees(b["price"])}</span></div></div>', unsafe_allow_html=True)
            st.page_link(PAGES["books"], label="All books", icon=":material/menu_book:")
        with st.container(border=True):
            st.markdown("**Write for Wordnest**")
            st.caption("Share your experience. Every article is checked by our AI review bot and an editor.")
            st.page_link(PAGES["write"], label="Start writing", icon=":material/edit:")
        with st.container(border=True):
            st.markdown("**Weekly email**")
            with st.form("newsletter", border=False):
                email = st.text_input("Email address", placeholder="you@example.com", label_visibility="collapsed")
                if st.form_submit_button("Subscribe", type="primary"):
                    if wn_auth.valid_email(email):
                        wn_db.x("INSERT OR IGNORE INTO newsletter(email, created_at) VALUES (?,?)",
                                (email.strip().lower(), wn_db.now()))
                        st.success("Subscribed. Thank you!")
                    else:
                        st.error("Please enter a valid email address.")


# ---------------------------------------------------------------- Daily News
def page_news():
    st.markdown('<h1 class="wn-serif" style="font-size:46px;margin-bottom:0">Daily News</h1>', unsafe_allow_html=True)
    st.caption("Short, neutral summaries on world affairs, industry, jobs, the economy, entertainment and sport. "
               "Every story names its source.")
    start = _qp("category", "All")
    options = ["All"] + NEWS_SECTIONS
    section = st.pills("Section", options, default=start if start in options else "All", required=True,
                       label_visibility="collapsed", key="news_section")
    items = wn_db.list_articles("news", category=section, limit=60)
    if not items:
        st.info("No stories in this section yet.")
        return
    c1, c2 = st.columns([1.35, 1], gap="large")
    with c1:
        article_card(items[0], large=True, news=True)
    with c2:
        for r in items[1:5]:
            news_row(r)
    rest = items[5:]
    if rest:
        st.markdown("## More stories")
        for i in range(0, len(rest), 3):
            cols = st.columns(3, gap="medium")
            for col, r in zip(cols, rest[i:i + 3]):
                with col:
                    article_card(r, news=True)
    st.markdown('<div class="wn-disclaimer" style="margin-top:24px"><b>How Wordnest covers news:</b> editors write short '
                'summaries in their own words, credit and link the original source, avoid political opinions, and add '
                'corrections openly. Spotted an error? Use "Report this content" on the story.</div>',
                unsafe_allow_html=True)


# ---------------------------------------------------------------- Articles
def page_articles():
    st.markdown('<h1 class="wn-serif" style="font-size:46px;margin-bottom:0">Articles</h1>', unsafe_allow_html=True)
    st.caption("Practical ideas, guides and stories from Wordnest writers.")
    start = _qp("category", "All")
    options = ["All"] + ARTICLE_CATEGORIES
    c1, c2, c3 = st.columns([3.2, 1, 1.4], vertical_alignment="bottom")
    with c1:
        cat = st.pills("Category", options, default=start if start in options else "All", required=True,
                       label_visibility="collapsed", key="art_cat")
    lang = c2.selectbox("Language", ["All", "English", "Hindi"], label_visibility="collapsed")
    search = c3.text_input("Search", placeholder="Search articles", label_visibility="collapsed")
    items = wn_db.list_articles("article", category=cat, language=lang, search=search.strip() or None)
    if not items:
        st.info("No articles found. Try another category, or be the first to write one.")
        st.page_link(PAGES["write"], label="Write an article", icon=":material/edit:")
        return
    for i in range(0, len(items), 3):
        cols = st.columns(3, gap="medium")
        for col, r in zip(cols, items[i:i + 3]):
            with col:
                article_card(r)


# ---------------------------------------------------------------- Single article / news story
def page_article():
    user = wn_auth.current_user()
    try:
        aid = int(_qp("id", 0))
    except ValueError:
        aid = 0
    a = wn_db.get_article(aid) if aid else None
    can_preview = a and user and (wn_auth.is_staff(user) or user["id"] == a["author_id"])
    if not a or (a["status"] != "published" and not can_preview):
        st.warning("This article is not available.")
        st.page_link(PAGES["articles"], label="Back to articles", icon=":material/arrow_back:")
        return
    news = a["kind"] == "news"
    if a["status"] == "published" and not st.session_state.get(f"viewed_{aid}"):
        wn_db.x("UPDATE articles SET views = views + 1 WHERE id=?", (aid,))
        st.session_state[f"viewed_{aid}"] = True
    if a["status"] != "published":
        st.info(f"Preview only. Status: {a['status'].replace('_', ' ')}.")

    back = "news" if news else "articles"
    st.page_link(PAGES[back], label="Daily News" if news else "Articles", icon=":material/arrow_back:",
                 query_params={"category": a["category"]})
    left, right = st.columns([2.2, 1], gap="large")
    with left:
        color = CATEGORY_COLORS.get(a["category"], "#1F6F5C")
        words = len((a["body"] or "").split())
        by = esc(a["source_name"]) if news else esc(a.get("pen_name") or a.get("user_name"))
        st.markdown(f'<span class="wn-kicker" style="color:{color}">{esc(a["category"])}'
                    f'{" · हिन्दी" if a["language"] == "Hindi" else ""}</span>'
                    f'<h1 class="wn-serif" style="font-size:44px;line-height:1.1;margin:8px 0 12px">{esc(a["title"])}</h1>'
                    f'<p style="font-size:19px;color:#4A5551;line-height:1.55">{esc(a["summary"])}</p>'
                    f'<p class="wn-meta">{"Source: " if news else "By "}{by} · {fmt_date(a["published_at"] or a["created_at"])}'
                    f' · {max(words // 200, 1)} min read</p>', unsafe_allow_html=True)
        cover = wn_db.get_cover("articles", aid)
        if cover:
            st.image(cover[0], width="stretch")
        st.markdown(a["body"])
        if news and a.get("source_url"):
            st.markdown(f"**Source:** [{a['source_name'] or 'Original report'}]({a['source_url']})")
        st.write("")
        disclaimer_box("article", aid, f"a{aid}")
    with right:
        if not news:
            with st.container(border=True):
                st.markdown(f"**About {esc(a.get('pen_name') or a.get('user_name'))}**")
                st.caption(a.get("bio") or "Wordnest writer.")
        st.markdown("**More in " + a["category"] + "**")
        for r in wn_db.list_articles(a["kind"], category=a["category"], limit=5):
            if r["id"] != aid:
                st.page_link(PAGES["article"], label=r["title"], query_params={"id": r["id"]})
        if a.get("ai_report") and user and wn_auth.is_staff(user):
            with st.expander("AI review (editors only)"):
                st.json(json.loads(a["ai_report"]))
