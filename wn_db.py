"""Wordnest - database layer (SQLite).

Everything the site stores lives in one SQLite file (wordnest.db).
Note for Streamlit Community Cloud: the file resets when the app restarts,
so the demo re-creates its sample content every time. For the live site,
move to a hosted database (Supabase/PostgreSQL or the Hostinger MySQL).
"""
import datetime
import json
import os
import sqlite3

DB_PATH = os.environ.get("WORDNEST_DB", "wordnest.db")

DEFAULT_SETTINGS = {
    "auto_publish_on_pass": "0",   # 1 = publish community articles that AI passes, without editor approval
    "strict_government": "0",      # 1 = block ANY mention of government/politics in community writing
    "royalty_pct": "70",           # author share of net book revenue
    "gst_pct": "18",               # GST included in the ebook price (confirm rate with your CA)
    "gateway_fee_pct": "2",        # payment gateway fee (Razorpay etc.)
    "sample_pages": "10",          # free pages for a paid book
    "max_strikes": "3",            # blocked submissions before an account is suspended
    "pass_mark": "60",             # demo interview score needed to count as a pass
    "free_attempts": "3",          # free interview attempts per job area
    "retake_days": "30",           # after the free attempts: one free retake every N days
    "ats_threshold": "80",         # CV score below this suggests the paid CV services
}


def now():
    return datetime.datetime.now().isoformat(timespec="seconds")


def conn():
    c = sqlite3.connect(DB_PATH, check_same_thread=False, timeout=20)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys = ON")
    return c


def q(sql, params=(), one=False):
    """Run a SELECT and return dict rows."""
    with conn() as c:
        cur = c.execute(sql, params)
        rows = [dict(r) for r in cur.fetchall()]
    if one:
        return rows[0] if rows else None
    return rows


def x(sql, params=()):
    """Run an INSERT/UPDATE/DELETE and return the new row id."""
    with conn() as c:
        cur = c.execute(sql, params)
        c.commit()
        return cur.lastrowid


SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    pen_name TEXT,
    bio TEXT,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'reader',          -- reader | editor | admin
    status TEXT NOT NULL DEFAULT 'active',        -- active | suspended
    strikes INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kind TEXT NOT NULL DEFAULT 'article',         -- article | news
    title TEXT NOT NULL,
    summary TEXT,
    body TEXT NOT NULL,
    category TEXT NOT NULL,
    language TEXT NOT NULL DEFAULT 'English',
    author_id INTEGER REFERENCES users(id),
    cover BLOB,
    cover_mime TEXT,
    source_name TEXT,
    source_url TEXT,
    is_top INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'pending',       -- ai_blocked | pending | published | rejected | unpublished
    ai_decision TEXT,
    ai_report TEXT,
    admin_note TEXT,
    views INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    published_at TEXT
);
CREATE TABLE IF NOT EXISTS books (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    subtitle TEXT,
    author_id INTEGER REFERENCES users(id),
    author_display TEXT NOT NULL,
    description TEXT,
    category TEXT NOT NULL,
    language TEXT NOT NULL DEFAULT 'English',
    price INTEGER NOT NULL DEFAULT 0,
    pages INTEGER,
    isbn TEXT,
    published_on TEXT,
    cover BLOB,
    cover_mime TEXT,
    cover_color TEXT DEFAULT '#1F6F5C',
    pdf BLOB,
    sample_pages INTEGER,
    status TEXT NOT NULL DEFAULT 'pending',       -- ai_blocked | pending | published | rejected | unpublished
    ai_decision TEXT,
    ai_report TEXT,
    admin_note TEXT,
    created_at TEXT NOT NULL,
    published_at TEXT
);
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    book_id INTEGER NOT NULL REFERENCES books(id),
    amount REAL NOT NULL,
    gst REAL NOT NULL DEFAULT 0,
    gateway_fee REAL NOT NULL DEFAULT 0,
    net REAL NOT NULL DEFAULT 0,
    author_share REAL NOT NULL DEFAULT 0,
    platform_share REAL NOT NULL DEFAULT 0,
    payment_ref TEXT,
    status TEXT NOT NULL DEFAULT 'paid',
    created_at TEXT NOT NULL,
    UNIQUE(user_id, book_id)
);
CREATE TABLE IF NOT EXISTS reading_progress (
    user_id INTEGER NOT NULL,
    book_id INTEGER NOT NULL,
    page INTEGER NOT NULL DEFAULT 0,
    updated_at TEXT,
    PRIMARY KEY (user_id, book_id)
);
CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_type TEXT NOT NULL,                      -- article | book
    item_id INTEGER NOT NULL,
    user_id INTEGER,
    reason TEXT NOT NULL,
    details TEXT,
    status TEXT NOT NULL DEFAULT 'open',          -- open | resolved
    action TEXT,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    is_read INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS moderation_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_type TEXT NOT NULL,
    item_id INTEGER,
    decision TEXT NOT NULL,
    engine TEXT NOT NULL,
    report TEXT,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS newsletter (
    email TEXT PRIMARY KEY,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS companies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_id INTEGER NOT NULL REFERENCES users(id),
    name TEXT NOT NULL,
    website TEXT,
    work_email TEXT,
    gstin TEXT,
    cin TEXT,
    city TEXT,
    about TEXT,
    status TEXT NOT NULL DEFAULT 'pending',       -- pending | verified | rejected
    admin_note TEXT,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER NOT NULL REFERENCES companies(id),
    title TEXT NOT NULL,
    category TEXT NOT NULL,
    location TEXT,
    work_mode TEXT,
    job_type TEXT,
    exp_min INTEGER DEFAULT 0,
    exp_max INTEGER DEFAULT 0,
    salary_min INTEGER,                           -- rupees per month
    salary_max INTEGER,
    skills TEXT,
    description TEXT NOT NULL,
    max_notice_days INTEGER DEFAULT 90,
    needs_interview INTEGER NOT NULL DEFAULT 1,
    status TEXT NOT NULL DEFAULT 'pending',       -- ai_blocked | pending | published | closed | rejected
    ai_decision TEXT,
    ai_report TEXT,
    created_at TEXT NOT NULL,
    published_at TEXT
);
CREATE TABLE IF NOT EXISTS candidates (
    user_id INTEGER PRIMARY KEY REFERENCES users(id),
    headline TEXT,
    category TEXT,
    total_exp REAL DEFAULT 0,
    current_role TEXT,
    current_company TEXT,
    skills TEXT,
    location TEXT,
    work_mode TEXT,
    expected_salary INTEGER,
    employment_status TEXT,
    notice_days INTEGER DEFAULT 0,
    resigned INTEGER DEFAULT 0,
    resignation_date TEXT,
    last_working_day TEXT,
    max_notice_can_serve INTEGER,
    shortfall_reason TEXT,
    phone TEXT,
    cv BLOB,
    cv_name TEXT,
    cv_text TEXT,
    cv_review TEXT,
    visible INTEGER NOT NULL DEFAULT 0,
    confirmed_at TEXT,
    updated_at TEXT
);
CREATE TABLE IF NOT EXISTS interviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    category TEXT NOT NULL,
    qa TEXT NOT NULL,                             -- JSON list of {q, answer, seconds, voice}
    result TEXT,                                  -- JSON scoring
    overall REAL,
    engine TEXT,
    started_at TEXT,
    finished_at TEXT
);
CREATE TABLE IF NOT EXISTS interview_audio (
    interview_id INTEGER NOT NULL,
    q_index INTEGER NOT NULL,
    audio BLOB NOT NULL,
    PRIMARY KEY (interview_id, q_index)
);
CREATE TABLE IF NOT EXISTS applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER NOT NULL REFERENCES jobs(id),
    user_id INTEGER NOT NULL REFERENCES users(id),
    interview_id INTEGER,
    note TEXT,
    status TEXT NOT NULL DEFAULT 'applied',      -- applied | shortlisted | rejected | hired
    created_at TEXT NOT NULL,
    UNIQUE(job_id, user_id)
);
CREATE TABLE IF NOT EXISTS profile_views (
    company_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    viewed_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS candidate_choices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    industry TEXT NOT NULL,
    function TEXT NOT NULL,
    subrole TEXT,
    level TEXT NOT NULL,
    is_primary INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS interview_video (
    interview_id INTEGER NOT NULL,
    q_index INTEGER NOT NULL,
    question TEXT NOT NULL,
    video BLOB NOT NULL,
    mime TEXT,
    seconds INTEGER,
    score INTEGER,
    feedback TEXT,
    transcript TEXT,
    PRIMARY KEY (interview_id, q_index)
);
CREATE TABLE IF NOT EXISTS service_orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    service TEXT NOT NULL,
    title TEXT NOT NULL,
    price REAL NOT NULL,
    area TEXT,
    preferred_slot TEXT,
    notes TEXT,
    payment_ref TEXT,
    status TEXT NOT NULL DEFAULT 'booked',        -- booked | scheduled | completed | refunded
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""


MIGRATIONS = {  # columns added after the first version; added automatically to older databases
    "jobs": [("industry", "TEXT"), ("function", "TEXT"), ("subrole", "TEXT"), ("level", "TEXT"),
             ("industry_required", "INTEGER DEFAULT 0")],
    "interviews": [("industry", "TEXT"), ("function", "TEXT"), ("subrole", "TEXT"), ("level", "TEXT")],
    "applications": [("match_score", "INTEGER")],
}


def init():
    with conn() as c:
        c.executescript(SCHEMA)
        for table, cols in MIGRATIONS.items():
            have = {r["name"] for r in c.execute(f"PRAGMA table_info({table})")}
            for name, typ in cols:
                if name not in have:
                    c.execute(f"ALTER TABLE {table} ADD COLUMN {name} {typ}")
        for k, v in DEFAULT_SETTINGS.items():
            c.execute("INSERT OR IGNORE INTO settings(key, value) VALUES (?, ?)", (k, v))
        c.commit()


# ---------- settings ----------
def get_setting(key):
    r = q("SELECT value FROM settings WHERE key=?", (key,), one=True)
    return r["value"] if r else DEFAULT_SETTINGS.get(key)


def get_setting_num(key):
    try:
        return float(get_setting(key))
    except (TypeError, ValueError):
        return float(DEFAULT_SETTINGS[key])


def set_setting(key, value):
    x("INSERT INTO settings(key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
      (key, str(value)))


# ---------- notifications ----------
def notify(user_id, title, message):
    x("INSERT INTO notifications(user_id, title, message, created_at) VALUES (?,?,?,?)",
      (user_id, title, message, now()))


def unread_count(user_id):
    r = q("SELECT COUNT(*) n FROM notifications WHERE user_id=? AND is_read=0", (user_id,), one=True)
    return r["n"] if r else 0


# ---------- articles ----------
ARTICLE_COLS = ("id, kind, title, summary, category, language, author_id, cover_mime, source_name, "
                "source_url, is_top, status, ai_decision, admin_note, views, created_at, published_at")


def list_articles(kind="article", category=None, language=None, search=None, limit=60, top_only=False):
    sql = (f"SELECT a.{ARTICLE_COLS.replace(', ', ', a.')}, u.pen_name, u.name AS user_name, "
           "(a.cover IS NOT NULL) AS has_cover FROM articles a LEFT JOIN users u ON u.id=a.author_id "
           "WHERE a.kind=? AND a.status='published'")
    params = [kind]
    if category and category != "All":
        sql += " AND a.category=?"
        params.append(category)
    if language and language != "All":
        sql += " AND a.language=?"
        params.append(language)
    if search:
        sql += " AND (a.title LIKE ? OR a.summary LIKE ?)"
        params += [f"%{search}%", f"%{search}%"]
    if top_only:
        sql += " AND a.is_top=1"
    sql += " ORDER BY a.published_at DESC LIMIT ?"
    params.append(limit)
    return q(sql, params)


def get_article(aid):
    return q("SELECT a.*, u.pen_name, u.name AS user_name, u.bio FROM articles a "
             "LEFT JOIN users u ON u.id=a.author_id WHERE a.id=?", (aid,), one=True)


def get_cover(table, item_id):
    if table not in ("articles", "books"):
        return None
    r = q(f"SELECT cover, cover_mime FROM {table} WHERE id=?", (item_id,), one=True)
    if r and r["cover"]:
        return r["cover"], r["cover_mime"] or "image/jpeg"
    return None


# ---------- books ----------
BOOK_COLS = ("id, title, subtitle, author_id, author_display, description, category, language, price, pages, "
             "isbn, published_on, cover_mime, cover_color, sample_pages, status, ai_decision, admin_note, "
             "created_at, published_at, (cover IS NOT NULL) AS has_cover, (pdf IS NOT NULL) AS has_pdf")


def list_books(status="published", search=None, author_id=None):
    sql = f"SELECT {BOOK_COLS} FROM books WHERE 1=1"
    params = []
    if status:
        sql += " AND status=?"
        params.append(status)
    if author_id:
        sql += " AND author_id=?"
        params.append(author_id)
    if search:
        sql += " AND (title LIKE ? OR author_display LIKE ? OR description LIKE ?)"
        params += [f"%{search}%"] * 3
    sql += " ORDER BY published_at DESC, id ASC"
    return q(sql, params)


def get_book(bid):
    return q(f"SELECT {BOOK_COLS} FROM books WHERE id=?", (bid,), one=True)


def get_book_pdf(bid):
    r = q("SELECT pdf FROM books WHERE id=?", (bid,), one=True)
    return r["pdf"] if r else None


def owns_book(user_id, book_id):
    if not user_id:
        return False
    return q("SELECT 1 FROM orders WHERE user_id=? AND book_id=? AND status='paid'", (user_id, book_id),
             one=True) is not None


def money_split(price):
    """Split a GST-inclusive ebook price into GST, gateway fee, author royalty and platform share."""
    gst_pct = get_setting_num("gst_pct")
    fee_pct = get_setting_num("gateway_fee_pct")
    roy_pct = get_setting_num("royalty_pct")
    base = price / (1 + gst_pct / 100) if price else 0
    gst = price - base
    fee = price * fee_pct / 100
    net = max(base - fee, 0)
    author = net * roy_pct / 100
    return {"amount": round(price, 2), "gst": round(gst, 2), "fee": round(fee, 2), "net": round(net, 2),
            "author": round(author, 2), "platform": round(net - author, 2)}


def create_order(user_id, book_id, price, payment_ref):
    s = money_split(price)
    x("INSERT OR IGNORE INTO orders(user_id, book_id, amount, gst, gateway_fee, net, author_share, platform_share, "
      "payment_ref, status, created_at) VALUES (?,?,?,?,?,?,?,?,?, 'paid', ?)",
      (user_id, book_id, s["amount"], s["gst"], s["fee"], s["net"], s["author"], s["platform"], payment_ref, now()))


def get_progress(user_id, book_id):
    r = q("SELECT page FROM reading_progress WHERE user_id=? AND book_id=?", (user_id, book_id), one=True)
    return r["page"] if r else 0


def save_progress(user_id, book_id, page):
    x("INSERT INTO reading_progress(user_id, book_id, page, updated_at) VALUES (?,?,?,?) "
      "ON CONFLICT(user_id, book_id) DO UPDATE SET page=excluded.page, updated_at=excluded.updated_at",
      (user_id, book_id, page, now()))


def log_moderation(item_type, item_id, decision, engine, report):
    x("INSERT INTO moderation_log(item_type, item_id, decision, engine, report, created_at) VALUES (?,?,?,?,?,?)",
      (item_type, item_id, decision, engine, json.dumps(report), now()))


# ---------- jobs ----------
JOB_SELECT = ("SELECT j.*, c.name AS company, c.status AS company_status, c.city AS company_city "
              "FROM jobs j JOIN companies c ON c.id=j.company_id")


def list_jobs(search=None, function=None, work_mode=None, location=None, industry=None, level=None, limit=100):
    sql = JOB_SELECT + " WHERE j.status='published' AND c.status='verified'"
    params = []
    if search:
        sql += " AND (j.title LIKE ? OR j.skills LIKE ? OR c.name LIKE ? OR j.subrole LIKE ?)"
        params += [f"%{search}%"] * 4
    if function and function != "All":
        sql += " AND COALESCE(j.function, j.category)=?"
        params.append(function)
    if industry and industry != "All":
        sql += " AND j.industry=?"
        params.append(industry)
    if level and level != "All":
        sql += " AND j.level=?"
        params.append(level)
    if work_mode and work_mode != "All":
        sql += " AND j.work_mode=?"
        params.append(work_mode)
    if location:
        sql += " AND j.location LIKE ?"
        params.append(f"%{location}%")
    sql += " ORDER BY j.published_at DESC, j.id DESC LIMIT ?"
    params.append(limit)
    return q(sql, params)


def get_job(jid):
    return q(JOB_SELECT + " WHERE j.id=?", (jid,), one=True)


def company_of(user_id):
    return q("SELECT * FROM companies WHERE owner_id=? ORDER BY id DESC LIMIT 1", (user_id,), one=True)


def candidate(user_id):
    return q("SELECT * FROM candidates WHERE user_id=?", (user_id,), one=True)


def latest_interview(user_id):
    return q("SELECT * FROM interviews WHERE user_id=? AND result IS NOT NULL ORDER BY id DESC LIMIT 1",
             (user_id,), one=True)


def choices(user_id):
    return q("SELECT * FROM candidate_choices WHERE user_id=? ORDER BY is_primary DESC, id", (user_id,))


def area_interviews(user_id, industry, function):
    return q("SELECT * FROM interviews WHERE user_id=? AND industry=? AND function=? AND result IS NOT NULL "
             "ORDER BY id DESC", (user_id, industry, function))


def best_interview(user_id, industry=None, function=None):
    """Best scored interview for a job area (or overall when no area is given)."""
    if industry and function:
        r = q("SELECT * FROM interviews WHERE user_id=? AND industry=? AND function=? AND result IS NOT NULL "
              "ORDER BY overall DESC, id DESC LIMIT 1", (user_id, industry, function), one=True)
        if r:
            return r
        return q("SELECT * FROM interviews WHERE user_id=? AND function=? AND result IS NOT NULL "
                 "ORDER BY overall DESC, id DESC LIMIT 1", (user_id, function), one=True)
    return q("SELECT * FROM interviews WHERE user_id=? AND result IS NOT NULL ORDER BY overall DESC, id DESC LIMIT 1",
             (user_id,), one=True)
