"""Wordnest - Read. Write. Earn.

Run on your computer:   streamlit run app.py
Deploy:                 Streamlit Community Cloud, main file = app.py
"""
import streamlit as st

st.set_page_config(page_title="Wordnest · Jobs, news and reading", page_icon="logo_icon.svg", layout="wide")

import wn_auth  # noqa: E402
import wn_db  # noqa: E402
import wn_seed  # noqa: E402
import wn_ui  # noqa: E402
from wn_pages_admin import page_admin  # noqa: E402
from wn_pages_books import page_book, page_books  # noqa: E402
from wn_pages_jobs import page_career, page_employers, page_job, page_jobs, page_services  # noqa: E402
from wn_pages_legal import page_policies  # noqa: E402
from wn_pages_public import page_article, page_articles, page_home, page_news  # noqa: E402
from wn_pages_write import page_account, page_dashboard, page_write  # noqa: E402

wn_seed.setup()
wn_ui.inject_css()
user = wn_auth.current_user()
unread = wn_db.unread_count(user["id"]) if user else 0
staff = wn_auth.is_staff(user)

pages = {
    "home": st.Page(page_home, title="Home", icon=":material/home:", url_path="home", default=True),
    "jobs": st.Page(page_jobs, title="Jobs", icon=":material/work:", url_path="jobs"),
    "job": st.Page(page_job, title="Job", url_path="job", visibility="hidden"),
    "career": st.Page(page_career, title="My job profile", icon=":material/badge:", url_path="career",
                      visibility="visible" if user else "hidden"),
    "services": st.Page(page_services, title="Career services", icon=":material/support_agent:", url_path="services",
                        visibility="visible" if user else "hidden"),
    "employers": st.Page(page_employers, title="For employers", icon=":material/business:", url_path="employers"),
    "news": st.Page(page_news, title="Daily News", icon=":material/newspaper:", url_path="news"),
    "articles": st.Page(page_articles, title="Articles", icon=":material/article:", url_path="articles"),
    "books": st.Page(page_books, title="Books", icon=":material/menu_book:", url_path="books"),
    "write": st.Page(page_write, title="Write with us", icon=":material/edit:", url_path="write"),
    "dashboard": st.Page(page_dashboard, title=f"My dashboard ({unread})" if unread else "My dashboard",
                         icon=":material/dashboard:", url_path="dashboard", visibility="visible" if user else "hidden"),
    "admin": st.Page(page_admin, title="Admin", icon=":material/admin_panel_settings:", url_path="admin",
                     visibility="visible" if staff else "hidden"),
    "account": st.Page(page_account, title="Sign in" if not user else "Account", icon=":material/person:", url_path="account"),
    "article": st.Page(page_article, title="Article", url_path="article", visibility="hidden"),
    "book": st.Page(page_book, title="Book", url_path="book", visibility="hidden"),
    "policies": st.Page(page_policies, title="Policies", url_path="policies", visibility="hidden"),
}
wn_ui.PAGES.clear()
wn_ui.PAGES.update(pages)

main = [pages[k] for k in ("home", "jobs", "news", "articles", "books", "write", "article", "book", "job", "policies")]
account = [pages["career"], pages["services"], pages["employers"], pages["dashboard"], pages["admin"], pages["account"]]
if not user:  # signed-out visitors see "For employers" and "Sign in" instead of an Account menu
    main, account = main + [pages["employers"], pages["services"], pages["career"], pages["dashboard"], pages["admin"],
                            pages["account"]], []
nav = st.navigation({"": main, "Account": account} if account else main, position="top")
st.logo("logo.svg", icon_image="logo_icon.svg", size="large", link=None)

if "toast" in st.session_state:
    st.toast(st.session_state.pop("toast"), icon=":material/notifications:")

nav.run()
wn_ui.footer()
