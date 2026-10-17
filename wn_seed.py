"""Wordnest - demo content created on first start (safe to delete once real content is added)."""
import json

import streamlit as st

import wn_auth
import wn_db
import wn_moderation
import wn_pdf

ARTICLE_CATEGORIES = ["Travel Destinations", "Travel Industry", "Technology", "Careers & Jobs",
                      "Food & Recipes", "Lifestyle"]
NEWS_SECTIONS = ["Geopolitics", "Industry Update", "Job Market", "Economy", "Entertainment", "Sport"]
BOOK_CATEGORIES = ["Fiction", "Career & Learning", "Travel", "Family & Food", "Self-help", "Poetry"]
LANGUAGES = ["English", "Hindi"]

DEMO_AUTHOR = ("author@wordnest.demo", "Author123!")
DEMO_READER = ("reader@wordnest.demo", "Reader123!")
DEMO_EMPLOYER = ("employer@wordnest.demo", "Employer123!")
DEMO_SEEKER = ("jobseeker@wordnest.demo", "Seeker123!")

COMPANIES = [
    ("BlueSky Travel Services (Demo)", "Noida", "A travel management company serving corporate travellers in the US, UK and India."),
    ("Northstar Support Solutions (Demo)", "Gurugram", "Customer support and back-office services for e-commerce and travel brands."),
]
# (company, title, industry, function, sub-role, level, industry required, location, mode, type, exp min, exp max,
#  salary min, salary max, skills, join within days, description)
JOBS = [
    (0, "Air Ticketing Executive (US shift)", "Travel & Tourism", "Core Operations", "Air ticketing & reservations",
     "Associate / Senior Associate", 1, "Noida", "Work from office", "Full-time", 1, 3, 22000, 30000,
     "Amadeus, ticketing, reissues, refunds, customer handling", 30,
     "Issue, reissue and refund air tickets for corporate travellers in the US. Handle email and phone requests, check fare "
     "rules, and keep every booking accurate within agreed turnaround times.\n\n**Shift:** 7 pm to 4 am IST, five days a week, "
     "cab provided.\n\n**You will need:** hands-on Amadeus or Sabre, good written English, and patience with travellers in a hurry."),
    (0, "Refunds and Reissue Specialist", "Travel & Tourism", "Core Operations", "Refunds & reissues",
     "Associate / Senior Associate", 1, "Remote (India)", "Work from home", "Full-time", 2, 5, 28000, 38000,
     "Refunds, reissues, fare rules, Amadeus, Sabre", 45,
     "Own the refunds and exchanges queue for a busy travel desk. Calculate penalties and fare differences, process refunds "
     "and reissues correctly the first time, and help reduce agency debit memos.\n\n**You will need:** two or more years in "
     "refunds or reissues, strong fare-rule knowledge, a stable internet connection and a quiet place to work."),
    (0, "Quality Analyst, Travel Fulfilment", "Travel & Tourism", "Quality", "Quality analyst",
     "Associate / Senior Associate", 1, "Noida", "Hybrid", "Full-time", 2, 5, 30000, 40000,
     "Quality, calibration, audit forms, Amadeus, feedback", 30,
     "Audit air and hotel transactions against SOPs, run weekly calibration with team leads, coach agents on repeat errors and "
     "share trend reports with the operations manager.\n\n**You will need:** two or more years in travel operations or quality, "
     "and a clear, fair feedback style."),
    (0, "HR Business Partner, Operations", "Travel & Tourism", "BU HR / HR Business Partner", "HR business partner", "Manager", 0,
     "Noida", "Work from office", "Full-time", 6, 10, 60000, 85000,
     "HRBP, employee relations, attrition, engagement, appraisal", 60,
     "Partner with the operations head for a 300-person delivery unit. Own attrition and engagement plans, employee relations "
     "cases, appraisal calibration and monthly HR dashboards.\n\n**You will need:** six or more years in HR, at least three as an "
     "HRBP in a shift-based operation. Experience from any industry is welcome."),
    (1, "WFM Real-time Analyst (US shift)", "BPO / BPM / KPO", "WFM (Workforce Management)", "Real-time analyst",
     "Associate / Senior Associate", 0, "Gurugram", "Work from office", "Full-time", 1, 4, 26000, 36000,
     "Real time, adherence, scheduling, Excel, WFM", 30,
     "Monitor queues and agent states in real time, move breaks and skills to protect service level, report adherence every "
     "hour and share end-of-day summaries with operations.\n\n**You will need:** one or more years in WFM or MIS in a contact "
     "centre, strong Excel and calm decision-making under pressure."),
    (1, "Payroll Executive", "BPO / BPM / KPO", "Payroll", "Payroll processing", "Associate / Senior Associate", 0, "Gurugram",
     "Hybrid", "Full-time", 2, 4, 28000, 36000, "Payroll, PF, ESI, TDS, Excel", 30,
     "Run monthly payroll for 1,200 employees: attendance inputs, deductions, PF, ESI and professional tax, TDS and the bank "
     "file, plus full and final settlements.\n\n**You will need:** two or more years in payroll processing and good knowledge "
     "of Indian statutory compliance."),
    (1, "Customer Support Associate (Chat and Email)", "E-commerce & Retail", "Customer Support", "Chat & email support",
     "Fresher / Entry", 0, "Remote (India)", "Work from home", "Full-time", 0, 2, 18000, 24000,
     "Chat support, email writing, English, CRM", 15,
     "Help online shoppers by chat and email: order status, returns, refunds and account questions. Full training is given in "
     "your first two weeks.\n\n**Freshers welcome.** You need clear written English, a laptop, stable internet and the "
     "ability to work rotational shifts."),
    (1, "MIS Executive (Advanced Excel)", "BPO / BPM / KPO", "Data Analytics", "MIS & reporting", "Associate / Senior Associate", 0,
     "Gurugram", "Hybrid", "Full-time", 1, 3, 25000, 32000, "Advanced Excel, VLOOKUP, pivot, Power BI, reporting", 30,
     "Prepare daily and monthly operations reports for client teams: productivity, quality and turnaround. Automate repeat "
     "reports and keep data accurate.\n\n**You will need:** strong Excel (lookups, pivots), basic Power BI and an eye for detail."),
]
SEEKER_ANSWERS = [
    "I am a ticketing executive with four years of experience at a travel management company in Noida. I handle "
    "issuance, reissues and refunds for US corporate travellers on Amadeus, mostly on the night shift. I now want a "
    "role with more refunds and exchange work and a chance to grow into a senior or SME position.",
    "First I stay calm and apologise for the stress. I check the ticket and fare rules to see whether a change is allowed "
    "and what the penalty and fare difference are. I explain the options clearly, for example reissue on the next "
    "flight or refund of taxes only, confirm the customer's choice, reissue the ticket and email the new itinerary.",
    "I sort the records by departure date and time, so travellers flying in the next 24 hours come first. I check "
    "for missed connections and protect those passengers before anything else, then work through the rest and note "
    "any that need customer approval.",
    "My biggest strength is accuracy. Last year my quality score stayed above 98% for six months, and I created a small "
    "checklist for reissues that my team now uses.",
    "Once I reissued a ticket without checking the validity date and the customer paid an extra fee. I fixed it with the "
    "airline, and since then I always check validity and fare rules before every reissue.",
]

ARTICLES = [
    ("Careers & Jobs", "How to prepare for your first interview in travel operations",
     "The questions recruiters ask about fares, reservation systems and customer handling, and how to answer them clearly.",
     """Your first interview for a travel operations role is less about knowing everything and more about showing how you think.

**1. Know the basics of a booking.** Be ready to explain what a reservation record holds: passenger names, itinerary, contact details, ticketing time limit and the fare. You do not need to type commands from memory, but you should understand each part.

**2. Practise a customer scenario.** A common question is: *"A traveller missed their flight. What do you do?"* A good answer has an order: stay calm, check the ticket and fare rules, explain the options and costs, and confirm the new plan in writing.

**3. Show you can work in shifts.** Many roles support the US, UK or Australia. Say honestly which shifts you can work and for how long.

**4. Ask one good question.** For example: *"How do new joiners get trained on the booking system in the first month?"*

Small, clear answers beat long ones. Practise aloud with a friend before the day."""),
    ("Travel Industry", "What a fare rule really means for your ticket",
     "Changes, refunds and no-shows explained in plain words before you book.",
     """Every airline ticket comes with fare rules. They decide what happens if your plans change.

**Change fee.** Some fares allow a date change for a fee plus any difference in fare. Cheaper fares may not allow changes at all.

**Refund.** A refundable fare returns money (sometimes minus a fee). A non-refundable fare may still return airport taxes, so it is worth asking.

**No-show.** If you do not turn up and do not tell the airline, the rest of the journey can be cancelled. Always inform the airline or your agent if you will miss a flight.

**Validity.** Many fares must be used within a set period from the date of issue.

Before you pay, ask one simple question: *"If I need to change this, what will it cost?"* That single answer saves most travel arguments later."""),
    ("Food & Recipes", "A Sunday dal the whole family can cook together",
     "A simple recipe with jobs for every age, from washing lentils to the final tadka.",
     """Cooking together is one of the easiest ways to spend unhurried time as a family.

**You need (serves 4):** 1 cup toor dal, 1 tomato, 1 onion, 2 green chillies, 1 tsp cumin, a pinch of asafoetida, ½ tsp turmeric, salt, 2 tbsp ghee, fresh coriander.

**Jobs for little hands:** wash the dal three times and tear the coriander leaves.

**Jobs for teenagers:** chop the onion and tomato.

**Jobs for grandparents:** taste and decide the salt. Everyone agrees they know best.

**Method.** Pressure-cook the dal with turmeric and 3 cups of water for 3 whistles. Heat ghee, add cumin and asafoetida, then onion until golden, then tomato and chillies until soft. Pour this tadka into the dal, add salt, simmer for 5 minutes and finish with coriander.

Serve with rice and a story from whoever cooked the most."""),
    ("Technology", "How AI is quietly changing everyday office work",
     "From drafting emails to searching process documents, a practical look at where AI helps and where people still matter.",
     """Artificial intelligence is now part of many ordinary office tools. The useful question is not *"Will AI replace me?"* but *"Which parts of my day can it make easier?"*

**Where it helps today**
- Drafting a first version of an email or report.
- Searching long process documents for the right step.
- Summarising a long meeting into action points.

**Where people still matter**
- Checking facts before anything is sent to a customer.
- Handling upset customers with empathy.
- Making decisions that affect money, safety or people.

**A simple habit:** treat AI output as a draft from a new colleague. Read it, correct it and own the final version."""),
    ("Travel Destinations", "Planning a relaxed family trip with grandparents",
     "Short distances, fewer stairs and a slower pace: a checklist for trips the whole family enjoys.",
     """Travelling with grandparents is about comfort first and sightseeing second.

- **Choose the pace.** One main outing a day, with a rest in the afternoon.
- **Pick the right stay.** Ask for a ground-floor room or a lift, and a bathroom with a grab rail if possible.
- **Plan short journeys.** Two to four hours of travel at a time is easier than a long day.
- **Carry a small health pouch.** Daily medicines, prescriptions and a list of emergency contacts.
- **Book help early.** Airlines and railways offer wheelchair or assistance services when booked in advance.

The best family trips leave everyone with energy for one more story at dinner."""),
    ("Careers & Jobs", "Five habits of a good team lead in the first 90 days",
     "Small, steady habits that build trust with a new team faster than big speeches.",
     """Moving from agent to team lead changes your job from doing the work to helping others do it well.

1. **Listen before you change.** Spend the first two weeks understanding how the team works today.
2. **Hold short one-to-ones.** Fifteen minutes a week with each person builds more trust than a monthly review.
3. **Make the scoreboard visible.** Share the few numbers that matter, such as quality, turnaround and backlog, every day.
4. **Coach on real cases.** Pick one recent transaction and walk through it together.
5. **Protect your team's time.** Push back on unnecessary meetings and reports.

None of these need a budget. All of them need consistency."""),
]

NEWS = {
    "Geopolitics": ["[Demo] Weekly brief: what to watch in world affairs", "[Demo] Explainer: how trade agreements affect travel"],
    "Industry Update": ["[Demo] Travel industry roundup for this week", "[Demo] What changed for travel agents this month"],
    "Job Market": ["[Demo] Hiring snapshot: roles in demand this week", "[Demo] Freshers: skills employers asked for this month"],
    "Economy": ["[Demo] Prices and spending: this week in numbers", "[Demo] Explainer: what an interest rate change means for you"],
    "Entertainment": ["[Demo] New releases to watch this weekend", "[Demo] Books and films people are talking about"],
    "Sport": ["[Demo] Weekend sports round-up", "[Demo] Fixtures to watch this week"],
}
NEWS_BODY = ("This is a sample story that shows how the Daily News section looks. "
             "An editor replaces it with a short, neutral summary written in their own words, "
             "states only facts confirmed by the source, and links the original report below.\n\n"
             "**How Wordnest writes news:** short summaries, no political opinions, every story credited to its source, "
             "and corrections added openly when something changes.")

BOOKS = [
    ("The Way Back", None, "R.K. Yadav", "Fiction", "English", 299, "#1F6F5C",
     "A novel by R.K. Yadav. Replace this text with the book's back-cover description."),
    ("The Love We Never Lost", None, "R.K. Yadav", "Fiction", "English", 299, "#8C2F39",
     "A novel by R.K. Yadav, available in English and Hindi. Replace this text with the back-cover description."),
    ("The Travel Career Starter", "Your first job in airline reservations and travel", "R.K. Yadav", "Career & Learning",
     "English", 249, "#B7791F",
     "A course-like guide to airline reservations, fares, booking systems and landing your first travel job."),
    ("The Middle Management Blueprint", "From Fresher to Operational Excellence Leader", "R.K. Yadav",
     "Career & Learning", "English", 299, "#2B3A55",
     "A practical guide for people moving from frontline roles into team lead and management positions."),
    ("Wordnest Free Reading Collection", "Short pieces from Wordnest writers", "Various authors", "Self-help",
     "English", 0, "#5B6B3A",
     "A free collection of short reads from Wordnest writers. Read online or download as PDF."),
]


@st.cache_resource(show_spinner="Setting up Wordnest...")
def setup():
    """Create tables, the admin account and demo content once per server start."""
    wn_db.init()
    wn_auth.ensure_admin()
    if wn_db.q("SELECT COUNT(*) n FROM articles", one=True)["n"] == 0:
        _seed()
    return True


def _user(email, password, name, pen, role="reader", bio=None):
    r = wn_db.q("SELECT id FROM users WHERE email=?", (email,), one=True)
    if r:
        return r["id"]
    return wn_db.x("INSERT INTO users(email, name, pen_name, bio, password_hash, role, created_at) VALUES (?,?,?,?,?,?,?)",
                   (email, name, pen, bio, wn_auth.hash_password(password), role, wn_db.now()))


def _seed():
    author = _user(DEMO_AUTHOR[0], DEMO_AUTHOR[1], "R.K. Yadav", "R.K. Yadav",
                   bio="Writer with more than two decades in the travel industry, writing fiction and practical career guides.")
    _user(DEMO_READER[0], DEMO_READER[1], "Demo Reader", "Demo Reader")
    guest = _user("guest@wordnest.demo", "Guest123!", "Guest Writer", "Guest Writer",
                  bio="Community writer (demo account).")
    admin = wn_db.q("SELECT id FROM users WHERE role='admin' ORDER BY id LIMIT 1", one=True)["id"]

    days = 0
    for cat, title, summary, body in ARTICLES:
        rep = wn_moderation.rule_check(f"{title}\n{summary}\n{body}", "article")
        ts = f"2026-10-{17 - days:02d}T09:{10 + days:02d}:00"
        wn_db.x("INSERT INTO articles(kind, title, summary, body, category, language, author_id, status, ai_decision, "
                "ai_report, created_at, published_at) VALUES ('article',?,?,?,?, 'English', ?, 'published', ?, ?, ?, ?)",
                (title, summary, body, cat, author, rep["decision"], json.dumps(rep), ts, ts))
        days += 1

    # one community article waiting in the editor's queue
    t, s = "A weekend walk through old Delhi's food lanes", "Where to start, what to eat first and how to avoid the crowds."
    b = ("Start early, around 8 am, before the lanes fill up. Begin with hot jalebi, then move to a plate of chole "
         "bhature. Wear comfortable shoes, carry small change and a water bottle, and keep your bag in front of you "
         "in busy lanes. Go with a friend and share plates so you can taste more.")
    rep = wn_moderation.rule_check(f"{t}\n{s}\n{b}", "article")
    wn_db.x("INSERT INTO articles(kind, title, summary, body, category, language, author_id, status, ai_decision, "
            "ai_report, created_at) VALUES ('article',?,?,?, 'Food & Recipes', 'English', ?, 'pending', ?, ?, ?)",
            (t, s, b, guest, rep["decision"], json.dumps(rep), wn_db.now()))

    hour = 0
    for section, titles in NEWS.items():
        for i, title in enumerate(titles):
            ts = f"2026-10-17T{8 + (hour % 10):02d}:{(hour * 7) % 60:02d}:00"
            wn_db.x("INSERT INTO articles(kind, title, summary, body, category, language, author_id, source_name, "
                    "source_url, is_top, status, ai_decision, created_at, published_at) "
                    "VALUES ('news',?,?,?,?, 'English', ?, ?, ?, ?, 'published', 'pass', ?, ?)",
                    (title, "Sample story to show the layout. Editors replace it with a verified summary and a source link.",
                     NEWS_BODY, section, admin, "Source name goes here", "https://example.com",
                     1 if i == 0 and section in ("Job Market", "Industry Update", "Economy", "Geopolitics") else 0, ts, ts))
            hour += 1

    for title, sub, by, cat, lang, price, color, desc in BOOKS:
        pdf = wn_pdf.demo_book_pdf(title, by, color)
        wn_db.x("INSERT INTO books(title, subtitle, author_id, author_display, description, category, language, price, "
                "pages, cover_color, pdf, status, ai_decision, created_at, published_at) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?, 'published', 'pass', ?, ?)",
                (title, sub, author if by == "R.K. Yadav" else admin, by, desc, cat, lang, price,
                 wn_pdf.page_count(pdf), color, pdf, "2026-10-16T10:00:00", "2026-10-16T10:00:00"))

    # a sample sale so the author dashboard shows earnings
    book = wn_db.q("SELECT id, price FROM books WHERE title='The Way Back'", one=True)
    reader = wn_db.q("SELECT id FROM users WHERE email=?", (DEMO_READER[0],), one=True)
    wn_db.create_order(reader["id"], book["id"], book["price"], "DEMO-0001")
    _seed_jobs(admin)


def _seed_jobs(admin):
    import wn_jobs_ai
    from wn_jobs_data import CORE_QUESTIONS, GENERAL_QUESTIONS, INDUSTRY_KEYWORDS, INDUSTRY_QUESTIONS
    owners = [_user(DEMO_EMPLOYER[0], DEMO_EMPLOYER[1], "Demo Employer", "Demo Employer"),
              _user("employer2@wordnest.demo", "Employer123!", "Second Demo Employer", "Second Demo Employer")]
    comp_ids = []
    for owner, (name, city, about) in zip(owners, COMPANIES):
        comp_ids.append(wn_db.x("INSERT INTO companies(owner_id, name, website, work_email, gstin, city, about, status, created_at) "
                                "VALUES (?,?,?,?,?,?,?, 'verified', ?)", (owner, name, "https://example.com", "hr@example.com",
                                                                       "09ABCDE1234F1Z5", city, about, wn_db.now())))
    for n, (ci, title, ind, fn, sub, lvl, req, loc, mode, jtype, emin, emax, smin, smax, skills, notice, desc) in enumerate(JOBS):
        ts = f"2026-10-17T{9 + n:02d}:00:00"
        wn_db.x("INSERT INTO jobs(company_id, title, category, industry, function, subrole, level, industry_required, location, "
                "work_mode, job_type, exp_min, exp_max, salary_min, salary_max, skills, description, max_notice_days, status, "
                "ai_decision, created_at, published_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?, 'published', 'pass', ?, ?)",
                (comp_ids[ci], title, fn, ind, fn, sub, lvl, req, loc, mode, jtype, emin, emax, smin, smax, skills, desc, notice,
                 ts, ts))
    # a ready job seeker with job areas, CV and a scored interview
    uid = _user(DEMO_SEEKER[0], DEMO_SEEKER[1], "Priya Sharma (Demo)", "Priya Sharma")
    cv = wn_pdf.demo_cv_pdf()
    text = wn_jobs_ai.cv_text(cv)
    review = _basic_cv(text)
    wn_db.x("INSERT INTO candidates(user_id, headline, category, total_exp, current_role, current_company, skills, location, "
            "work_mode, expected_salary, employment_status, notice_days, resigned, resignation_date, last_working_day, "
            "max_notice_can_serve, shortfall_reason, phone, cv, cv_name, cv_text, cv_review, visible, confirmed_at, updated_at) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,1,?,?)",
            (uid, "Air ticketing executive, 4 years, Amadeus · US shift", "Core Operations", 4, "Ticketing Executive",
             "A travel company in Noida", "Amadeus, ticketing, reissues, refunds, fare rules, Excel, quality", "Noida",
             "Work from home", 32000, "Serving notice period", 60, 1, "2026-10-01", "2026-11-15", 45,
             "Early release agreed with employer", "9800000000", cv, "Priya_Sharma_CV_demo.pdf", text, json.dumps(review),
             wn_db.now(), wn_db.now()))
    for i, (ind, fn, sub, lvl) in enumerate([("Travel & Tourism", "Core Operations", "Refunds & reissues", "Associate / Senior Associate"),
                                             ("Travel & Tourism", "Quality", "Quality analyst", "Associate / Senior Associate")]):
        wn_db.x("INSERT INTO candidate_choices(user_id, industry, function, subrole, level, is_primary, created_at) VALUES (?,?,?,?,?,?,?)",
                (uid, ind, fn, sub, lvl, int(i == 0), wn_db.now()))
    tq = CORE_QUESTIONS["Travel & Tourism"]
    qs = [GENERAL_QUESTIONS[0], tq[0], tq[2], tq[1], (INDUSTRY_QUESTIONS[0].format(industry="Travel & Tourism"), INDUSTRY_KEYWORDS)]
    answers = SEEKER_ANSWERS[:3] + [
        "A refund returns money to the customer under the fare rules, a reissue changes the ticket to a new date or route and "
        "may need a fare difference and penalty, and a revalidation only updates the flight details on the same fare without "
        "issuing a new ticket.",
        "A travel company earns from service fees and commissions and saves the client money through negotiated fares. "
        "What matters most to customers is speed, accuracy, being reachable when plans change, and clear costs."]
    qa = [{"q": q, "keywords": kw, "answer": a, "seconds": 95 + 7 * i, "voice": False}
          for i, ((q, kw), a) in enumerate(zip(qs, answers))]
    result = _basic_score(qa)
    result.update({"written_overall": result["overall"], "video_overall": None, "videos": 0, "video_scored": False})
    iid = wn_db.x("INSERT INTO interviews(user_id, category, qa, result, overall, engine, started_at, finished_at, industry, function, "
                  "subrole, level) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                  (uid, "Travel & Tourism · Core Operations", json.dumps([{k: a[k] for k in ("q", "answer", "seconds", "voice")}
                                                                         for a in qa]),
                   json.dumps(result), result["overall"], result["engine"], "2026-10-16T18:00:00", "2026-10-16T18:09:00",
                   "Travel & Tourism", "Core Operations", "Refunds & reissues", "Associate / Senior Associate"))
    job = wn_db.q("SELECT * FROM jobs WHERE title='Refunds and Reissue Specialist'", one=True)
    import wn_match
    m = wn_match.match(uid, job)
    wn_db.x("INSERT INTO applications(job_id, user_id, interview_id, note, match_score, created_at) VALUES (?,?,?,?,?,?)",
            (job["id"], uid, iid, "I have four years on Amadeus and can join by mid-November.", m["score"], wn_db.now()))


def _basic_score(qa):
    """Demo seed uses the basic scorer so the demo looks the same with or without an AI key."""
    import wn_ai
    saved = wn_ai.providers
    wn_ai.providers = lambda: []
    try:
        import wn_jobs_ai
        return wn_jobs_ai.score_interview("Travel Operations", qa)
    finally:
        wn_ai.providers = saved


def _basic_cv(text):
    import wn_ai
    saved = wn_ai.providers
    wn_ai.providers = lambda: []
    try:
        import wn_jobs_ai
        return wn_jobs_ai.review_cv(text)
    finally:
        wn_ai.providers = saved
