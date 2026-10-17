"""Wordnest Jobs - job listings, job page, job seeker profile (job areas, notice period, CV/ATS check, written + video
demo interview), career services, and the employer area."""
import datetime
import json
import time

import streamlit as st

import wn_ai
import wn_auth
import wn_db
import wn_jobs_ai
import wn_match
import wn_moderation
from wn_jobs_data import (EMPLOYMENT_STATUS, FUNCTIONS, INDUSTRIES, JOB_TYPES, LEVEL_YEARS, LEVELS, MAX_AREAS, SERVICES,
                          SHORTFALL_REASONS, WORK_MODES, area_label, subroles, suggest_level)
from wn_match import join_days
from wn_ui import PAGES, ago, esc, fmt_date, report_dialog, rupees, show_review

VERIFIED = '<span class="wn-badge" style="color:#145C40;background:#DDF1E6">✓ Verified employer</span>'
ZERO_FEE = ("Wordnest is free for job seekers. No employer on Wordnest may ask you for money: registration, training, "
            "kit or security deposit. If anyone asks, do not pay; report the job and we will remove the employer.")
SERVICES_NOTE = ("Career services are optional. They never affect your applications, your visibility to employers or "
                 "your scores, and no service guarantees a job.")
FUNCTION_NAMES = list(FUNCTIONS)


def price(sid):
    default = next((p for s, _, p, _ in SERVICES if s == sid), 0)
    try:
        return float(wn_db.get_setting(f"price_{sid}") or default)
    except (TypeError, ValueError):
        return float(default)


def _qp_int(name):
    try:
        return int(st.query_params.get(name) or 0)
    except ValueError:
        return 0


def salary_text(job):
    lo, hi = job.get("salary_min"), job.get("salary_max")
    if not lo and not hi:
        return "Salary not disclosed"
    if lo and hi and lo != hi:
        return f"₹{lo:,}–{hi:,} / month"
    return f"₹{(lo or hi):,} / month"


def exp_text(job):
    a, b = job.get("exp_min") or 0, job.get("exp_max") or 0
    if not a and not b:
        return "Freshers welcome"
    return f"{a}–{b} years" if b and b != a else f"{a}+ years"


def job_area(job):
    fn = job.get("function") or job.get("category")
    return " · ".join(x for x in (job.get("industry"), fn, job.get("subrole"), job.get("level")) if x)


def notice_text(c):
    if not c:
        return "Not shared"
    if c.get("employment_status") in ("Available now (not working)", "Fresher"):
        return "Can join immediately"
    if c.get("resigned"):
        txt = f"Resigned on {fmt_date(c.get('resignation_date'))}, last working day {fmt_date(c.get('last_working_day'))}"
        if c.get("shortfall_reason"):
            txt += f" · early exit: {c['shortfall_reason']}"
        return txt
    txt = f"{c.get('notice_days') or 0}-day notice, not resigned yet"
    if c.get("max_notice_can_serve") and c["max_notice_can_serve"] < (c.get("notice_days") or 0):
        txt += f" · can join in {c['max_notice_can_serve']} days"
    return txt


def fresh_text(c):
    if not c or not c.get("confirmed_at"):
        return "never confirmed"
    days = (datetime.datetime.now() - datetime.datetime.fromisoformat(c["confirmed_at"])).days
    return "confirmed today" if days == 0 else f"confirmed {days} days ago"


def match_chip(score):
    fg, bg = ("#145C40", "#DDF1E6") if score >= 75 else ("#7A4B00", "#FBEBC8") if score >= 55 else ("#3D4844", "#E6E9E5")
    return f'<span class="wn-badge" style="color:{fg};background:{bg}">{score}% match</span>'


# ---------------------------------------------------------------- job cards and list
def job_card(job, compact=False, m=None):
    with st.container(border=True):
        c1, c2 = st.columns([4, 1.25], vertical_alignment="top")
        skills = "".join(f'<span class="wn-chip">{esc(s.strip())}</span>' for s in (job.get("skills") or "").split(",")[:5]
                         if s.strip())
        c1.markdown(
            f'<div class="wn-title" style="font-size:19px;margin:0">{esc(job["title"])}</div>'
            f'<div style="margin:4px 0 4px"><b>{esc(job["company"])}</b> '
            + (VERIFIED if job.get("company_status") == "verified" else "") + '</div>'
            f'<div class="wn-kicker" style="font-size:11.5px;margin-bottom:4px">{esc(job_area(job))}</div>'
            f'<div class="wn-meta">{esc(job.get("location") or "")} · {esc(job.get("work_mode") or "")} · '
            f'{esc(job.get("job_type") or "")} · {exp_text(job)} · <b style="color:#1C2321">{salary_text(job)}</b></div>'
            + ("" if compact else f'<div style="margin-top:8px">{skills}</div>'), unsafe_allow_html=True)
        with c2:
            if m and m.get("eligible"):
                st.markdown(match_chip(m["score"]), unsafe_allow_html=True)
            st.caption(ago(job.get("published_at")) or "")
            st.page_link(PAGES["job"], label="View and apply", icon=":material/arrow_forward:", query_params={"id": job["id"]})


def page_jobs():
    user = wn_auth.current_user()
    areas = wn_db.choices(user["id"]) if user else []
    st.markdown('<h1 class="wn-serif" style="font-size:46px;margin-bottom:0">Jobs</h1>', unsafe_allow_html=True)
    st.caption("Work-from-home and office jobs from verified employers, matched by industry, function and level. "
               "Free for job seekers, always.")
    c1, c2 = st.columns([2.2, 1.2], vertical_alignment="bottom")
    search = c1.text_input("Job title, skill or company", value=st.query_params.get("q", ""), placeholder="e.g. WFM, payroll, ticketing")
    location = c2.text_input("Location", value=st.query_params.get("loc", ""), placeholder="City")
    f1, f2, f3, f4 = st.columns(4)
    start_fn = st.query_params.get("function") or st.query_params.get("category") or "All"
    fn_opts = ["All"] + FUNCTION_NAMES
    function = f1.selectbox("Function", fn_opts, index=fn_opts.index(start_fn) if start_fn in fn_opts else 0)
    ind_opts = ["All"] + INDUSTRIES
    start_ind = st.query_params.get("industry", "All")
    industry = f2.selectbox("Industry", ind_opts, index=ind_opts.index(start_ind) if start_ind in ind_opts else 0)
    level = f3.selectbox("Level", ["All"] + LEVELS)
    mode = f4.selectbox("Work mode", ["All"] + WORK_MODES)
    only_mine = False
    if areas:
        only_mine = st.toggle(f"Only jobs that fit my {len(areas)} job area(s), best match first", value=True)
    jobs = wn_db.list_jobs(search.strip() or None, function, mode, location.strip() or None, industry, level)
    cand = wn_db.candidate(user["id"]) if user else None
    rows = []
    for j in jobs:
        m = wn_match.match(user["id"], j, cand, areas) if areas else None
        if only_mine and not (m and m["eligible"]):
            continue
        rows.append((j, m))
    if only_mine:
        rows.sort(key=lambda t: -t[1]["score"])
    main, side = st.columns([2.6, 1], gap="large")
    with main:
        st.markdown(f"**{len(rows)} job{'s' if len(rows) != 1 else ''} found**")
        for j, m in rows:
            job_card(j, m=m)
        if not rows:
            st.info("No jobs match. Try other filters" + (", or turn off 'Only jobs that fit my job areas'." if only_mine else "."))
    with side:
        career_sidebar(user, areas)


def career_sidebar(user=None, areas=None):
    with st.container(border=True):
        st.markdown("**Get interview-ready**")
        if user and areas:
            st.caption("Your job areas: " + "; ".join(f"{a['function']} ({a['industry']})" for a in areas))
        else:
            st.caption("Choose up to 4 job areas (industry + function + level), upload your CV and take the written + video "
                       "demo interview. Employers see your score and real joining date.")
        st.page_link(PAGES["career"] if user else PAGES["account"], label="My job profile" if user else "Create my job profile",
                     icon=":material/person_add:")
    with st.container(border=True):
        st.markdown("**Hiring?**")
        st.caption("Post jobs and get candidates ranked by match %, interview score and joining date.")
        st.page_link(PAGES["employers"], label="For employers", icon=":material/business:")
    st.markdown(f'<div class="wn-note">{ZERO_FEE}</div>', unsafe_allow_html=True)


# ---------------------------------------------------------------- job page
def page_job():
    user = wn_auth.current_user()
    jid = _qp_int("id")
    job = wn_db.get_job(jid) if jid else None
    comp = wn_db.company_of(user["id"]) if user else None
    owner = comp and job and comp["id"] == job["company_id"]
    if not job or ((job["status"] != "published" or job["company_status"] != "verified")
                   and not owner and not wn_auth.is_staff(user)):
        st.warning("This job is not available.")
        st.page_link(PAGES["jobs"], label="Back to jobs", icon=":material/arrow_back:")
        return
    st.page_link(PAGES["jobs"], label="Jobs", icon=":material/arrow_back:")
    main, side = st.columns([2.2, 1], gap="large")
    fn = job.get("function") or job["category"]
    with main:
        st.markdown(f'<span class="wn-kicker">{esc(job_area(job))}</span>'
                    f'<h1 class="wn-serif" style="font-size:40px;line-height:1.1;margin:6px 0 8px">{esc(job["title"])}</h1>'
                    f'<p style="font-size:18px;margin:0 0 8px"><b>{esc(job["company"])}</b> '
                    + (VERIFIED if job["company_status"] == "verified" else "") + "</p>", unsafe_allow_html=True)
        st.markdown(f'<div class="wn-facts"><div><span>Industry</span><b>{esc(job.get("industry") or "-")}</b></div>'
                    f'<div><span>Function</span><b>{esc(fn)}</b></div>'
                    f'<div><span>Sub-role</span><b>{esc(job.get("subrole") or "-")}</b></div>'
                    f'<div><span>Level</span><b>{esc(job.get("level") or "-")}</b></div>'
                    f'<div><span>Location</span><b>{esc(job["location"])} · {esc(job["work_mode"])}</b></div>'
                    f'<div><span>Experience</span><b>{exp_text(job)}</b></div>'
                    f'<div><span>Salary</span><b>{salary_text(job)}</b></div>'
                    f'<div><span>Joining</span><b>within {job["max_notice_days"]} days</b></div></div>',
                    unsafe_allow_html=True)
        if job.get("industry_required"):
            st.caption(f"The employer needs experience in {job['industry']} for this role.")
        if job["status"] != "published":
            st.info(f"Preview only. Status: {job['status'].replace('_', ' ')}.")
        st.markdown("### About the role")
        st.markdown(job["description"])
        if job["skills"]:
            st.markdown("**Skills:** " + ", ".join(s.strip() for s in job["skills"].split(",") if s.strip()))
        if job["needs_interview"]:
            st.caption("This employer asks applicants to complete the Wordnest demo interview (written + video) for this job area.")
    with side:
        _apply_box(user, job, owner)
        st.write("")
        st.markdown(f'<div class="wn-note">{ZERO_FEE}</div>', unsafe_allow_html=True)
        if st.button("Report this job", icon=":material/flag:"):
            report_dialog("job", job["id"])


def _apply_box(user, job, owner):
    with st.container(border=True):
        st.markdown("**Apply for this job**")
        if owner:
            st.caption("This is your job post.")
            st.page_link(PAGES["employers"], label="See applicants", icon=":material/group:")
            return
        if not user:
            st.caption("Create a free account to apply. It takes one minute.")
            st.page_link(PAGES["account"], label="Sign in / Create account", icon=":material/login:")
            return
        applied = wn_db.q("SELECT status, created_at, match_score FROM applications WHERE job_id=? AND user_id=?",
                          (job["id"], user["id"]), one=True)
        if applied:
            st.success(f"You applied on {fmt_date(applied['created_at'])}. Status: **{applied['status']}**.")
            return
        cand = wn_db.candidate(user["id"])
        areas = wn_db.choices(user["id"])
        m = wn_match.match(user["id"], job, cand, areas)
        if not m["eligible"]:
            st.warning(m["reason"])
            st.caption(f"You can apply only within your job areas ({len(areas)} of {MAX_AREAS} used). This keeps applications "
                       "relevant for you and for employers.")
            st.page_link(PAGES["career"], label="Edit my job areas", icon=":material/tune:")
            return
        st.markdown(match_chip(m["score"]) + f' <span class="wn-meta">via your area: {esc(m["area"]["function"])} '
                    f'({esc(m["area"]["industry"])})</span>', unsafe_allow_html=True)
        with st.expander("How this match is calculated"):
            for name, got, out_of in m["parts"]:
                st.caption(f"{name}: {got} / {out_of}")
        pct, found, missing = wn_match.cv_job_match((cand or {}).get("cv_text"), job)
        if pct is not None:
            st.caption(f"Your CV mentions {pct}% of this job's skills." + (f" Missing: {', '.join(missing)}." if missing else ""))
        need = []
        if not cand or not cand.get("headline"):
            need.append("your profile and notice period")
        if cand and not cand.get("cv"):
            need.append("your CV")
        if job["needs_interview"] and not m.get("interview"):
            need.append(f"the demo interview for {m['area']['function']}")
        if need:
            st.caption("Before you apply, please complete: " + ", ".join(need) + ".")
            st.page_link(PAGES["career"], label="Complete my job profile", icon=":material/person:")
            return
        days = join_days(cand)
        st.caption(f"Your availability: {notice_text(cand)} ({fresh_text(cand)}).")
        if days is not None and days > (job["max_notice_days"] or 999):
            st.warning(f"The employer wants people who can join within {job['max_notice_days']} days; you can join in about "
                       f"{days} days. You can still apply.")
        iv = m.get("interview")
        if iv:
            st.caption(f"Your best demo interview score for this area: {int(iv['overall'])}/100 will be shared.")
        note = st.text_area("Short note to the employer (optional)", max_chars=500, key="apply_note")
        if st.button("Apply now", type="primary", width="stretch"):
            wn_db.x("INSERT OR IGNORE INTO applications(job_id, user_id, interview_id, note, match_score, created_at) "
                    "VALUES (?,?,?,?,?,?)", (job["id"], user["id"], iv["id"] if iv else None, note.strip(), m["score"], wn_db.now()))
            owner_id = wn_db.q("SELECT owner_id FROM companies WHERE id=?", (job["company_id"],), one=True)["owner_id"]
            wn_db.notify(owner_id, f"New applicant: {job['title']}",
                         f"{wn_auth.display_name(user)} applied ({m['score']}% match). See them in For employers.")
            wn_db.notify(user["id"], f"Applied: {job['title']}",
                         f"Your application to {job['company']} was sent with your profile, CV and interview.")
            st.rerun()


# ---------------------------------------------------------------- job seeker hub
def page_career():
    user = wn_auth.current_user()
    st.markdown('<h1 class="wn-serif" style="font-size:42px;margin-bottom:0">My job profile</h1>', unsafe_allow_html=True)
    st.caption("Choose up to 4 job areas, add your notice period, upload your CV and take the demo interview. Then apply "
               "in one click to jobs that fit.")
    if not user:
        st.info("Create a free account to build your job profile.")
        st.page_link(PAGES["account"], label="Sign in / Create account", icon=":material/login:")
        return
    cand = wn_db.candidate(user["id"]) or {}
    areas = wn_db.choices(user["id"])
    any_iv = wn_db.latest_interview(user["id"])
    steps = [("Job areas", bool(areas)), ("Profile and notice", bool(cand.get("headline"))), ("CV", bool(cand.get("cv"))),
             ("Demo interview", bool(any_iv)), ("Visible to employers", bool(cand.get("visible")))]
    cols = st.columns(5)
    for col, (label, done) in zip(cols, steps):
        col.markdown(f'<div class="wn-step-chip{" done" if done else ""}">{"✓" if done else "○"} {label}</div>',
                     unsafe_allow_html=True)
    if cand.get("confirmed_at"):
        age = (datetime.datetime.now() - datetime.datetime.fromisoformat(cand["confirmed_at"])).days
        if age >= 14:
            st.warning(f"Your availability was last confirmed {age} days ago. Employers see this. Please reconfirm.")
            if st.button("My notice period details are still correct"):
                wn_db.x("UPDATE candidates SET confirmed_at=? WHERE user_id=?", (wn_db.now(), user["id"]))
                st.rerun()
    if st.session_state.get("iv", {}).get("user") == user["id"]:
        _interview_runner(user, cand)
        return
    tabs = st.tabs(["1. Job areas", "2. Profile and notice period", "3. CV and ATS check", "4. Demo interviews",
                    "5. My applications"])
    with tabs[0]:
        _areas_tab(user, cand, areas)
    with tabs[1]:
        _profile_form(user, cand, areas)
    with tabs[2]:
        _cv_tab(user, cand)
    with tabs[3]:
        _interviews_tab(user, cand, areas)
    with tabs[4]:
        _applications_tab(user)


def _areas_tab(user, cand, areas):
    st.markdown(f"Pick up to **{MAX_AREAS} job areas**. Each one is an industry + function + sub-role + level. You can apply "
                "only to jobs in your areas, and you take one demo interview per area, so choose what you really do.")
    for a in areas:
        st_ = wn_match.attempt_status(user["id"], a["industry"], a["function"])
        with st.container(border=True):
            c1, c2, c3 = st.columns([3.2, 1.6, 1.4], vertical_alignment="center")
            c1.markdown(("<span class='wn-badge wn-free'>Primary</span> " if a["is_primary"] else "")
                        + f"**{esc(a['function'])}** · {esc(a['subrole'] or '')}  \n<span class='wn-meta'>"
                        f"{esc(a['industry'])} · {esc(a['level'])}</span>", unsafe_allow_html=True)
            c2.markdown("Interview: " + (f"**{int(st_['best'])}/100**" + (" ✓ passed" if st_["passed"] else "")
                                         if st_["best"] is not None else "not taken")
                        + f"  \n<span class='wn-meta'>{st_['used']} attempt(s)</span>", unsafe_allow_html=True)
            with c3:
                if not a["is_primary"] and st.button("Make primary", key=f"prim_{a['id']}"):
                    wn_db.x("UPDATE candidate_choices SET is_primary=CASE WHEN id=? THEN 1 ELSE 0 END WHERE user_id=?",
                            (a["id"], user["id"]))
                    st.rerun()
                if st.button("Remove", key=f"rm_{a['id']}"):
                    wn_db.x("DELETE FROM candidate_choices WHERE id=? AND user_id=?", (a["id"], user["id"]))
                    if a["is_primary"]:
                        wn_db.x("UPDATE candidate_choices SET is_primary=1 WHERE id=(SELECT MIN(id) FROM candidate_choices "
                                "WHERE user_id=?)", (user["id"],))
                    st.rerun()
    if len(areas) >= MAX_AREAS:
        st.info(f"You have {MAX_AREAS} job areas, the maximum. Remove one to add another.")
        return
    st.markdown(f"#### Add a job area ({len(areas)} of {MAX_AREAS})")
    c1, c2 = st.columns(2)
    ind = c1.selectbox("Industry", INDUSTRIES, key="add_ind")
    fn = c2.selectbox("Function", FUNCTION_NAMES, key="add_fn",
                      help="Core Operations = the main work of that industry, e.g. air ticketing in Travel.")
    c3, c4 = st.columns(2)
    sub = c3.selectbox("Sub-role", subroles(ind, fn), key=f"add_sub_{ind}_{fn}")
    suggested = suggest_level(cand.get("total_exp") or 0)
    lvl = c4.selectbox("Level", LEVELS, index=LEVELS.index(suggested), key="add_lvl",
                       format_func=lambda x: f"{x} ({LEVEL_YEARS[x]})")
    if cand.get("total_exp") is not None:
        st.caption(f"Suggested level from your {cand.get('total_exp') or 0:g} years of experience: {suggested}.")
    if st.button("Add job area", type="primary", icon=":material/add:"):
        if any(a["industry"] == ind and a["function"] == fn and a["subrole"] == sub for a in areas):
            st.error("You already have this job area.")
        else:
            wn_db.x("INSERT INTO candidate_choices(user_id, industry, function, subrole, level, is_primary, created_at) "
                    "VALUES (?,?,?,?,?,?,?)", (user["id"], ind, fn, sub, lvl, 0 if areas else 1, wn_db.now()))
            st.rerun()


def _profile_form(user, cand, areas):
    with st.form("cand_profile"):
        headline = st.text_input("Headline", value=cand.get("headline") or "",
                                 placeholder="e.g. WFM real-time analyst, 4 years, BPO voice process")
        c1, c2, c3 = st.columns(3)
        exp = c1.number_input("Total experience (years)", 0.0, 45.0, float(cand.get("total_exp") or 0), step=0.5)
        mode = c2.selectbox("Preferred work mode", WORK_MODES,
                            index=WORK_MODES.index(cand["work_mode"]) if cand.get("work_mode") in WORK_MODES else 0)
        loc = c3.text_input("City", value=cand.get("location") or "")
        c4, c5 = st.columns(2)
        role = c4.text_input("Current / last role", value=cand.get("current_role") or "")
        company = c5.text_input("Current / last company (hidden from that company)", value=cand.get("current_company") or "")
        skills = st.text_input("Key skills (comma separated)", value=cand.get("skills") or "",
                               placeholder="Forecasting, scheduling, Erlang, Excel, real-time monitoring")
        c7, c8 = st.columns(2)
        salary = c7.number_input("Expected salary (₹ per month)", 0, 1_000_000, int(cand.get("expected_salary") or 0), step=1000)
        phone = c8.text_input("Phone (shown only to employers you apply to)", value=cand.get("phone") or "")
        st.markdown("**Notice period and availability**")
        st.caption("Recruiters filter by joining date first. Accurate details get you more calls.")
        status = st.selectbox("Employment status", EMPLOYMENT_STATUS,
                              index=EMPLOYMENT_STATUS.index(cand["employment_status"]) if cand.get("employment_status") in EMPLOYMENT_STATUS else 0)
        n1, n2 = st.columns(2)
        notice = n1.number_input("Notice period in your contract (days)", 0, 180, int(cand.get("notice_days") or 0), step=15)
        maxserve = n2.number_input("Earliest you could join if needed (days)", 0, 180,
                                   int(cand.get("max_notice_can_serve") or cand.get("notice_days") or 0), step=5,
                                   help="For example if your employer may release you early, or a new employer buys out your notice.")
        r1, r2, r3 = st.columns(3)
        resigned = r1.checkbox("I have resigned", value=bool(cand.get("resigned")))
        rdate = r2.date_input("Resignation submitted on", value=_d(cand.get("resignation_date")), format="DD/MM/YYYY")
        lwd = r3.date_input("Last working day", value=_d(cand.get("last_working_day"), 30), format="DD/MM/YYYY")
        reasons = ["Not applicable"] + SHORTFALL_REASONS
        reason = st.selectbox("If you leave before your full notice period, why?", reasons,
                              index=reasons.index(cand["shortfall_reason"]) if cand.get("shortfall_reason") in reasons else 0)
        visible = st.checkbox("Show my profile, CV and interviews (including videos) to verified employers searching for "
                              "candidates. You can turn this off any time.", value=bool(cand.get("visible")))
        st.caption("Your current company is never shown to that company. Phone and email are shared only when you apply.")
        saved = st.form_submit_button("Save and confirm my details", type="primary")
    if not saved:
        return
    errors = []
    if len(headline.strip()) < 8:
        errors.append("Please write a headline (at least 8 characters).")
    shortfall, served_reason = 0, None
    if resigned:
        if lwd < rdate:
            errors.append("Last working day cannot be before the resignation date.")
        shortfall = max(notice - (lwd - rdate).days, 0)
        if shortfall > 0:
            if reason == "Not applicable":
                errors.append(f"Your last day is {shortfall} days before your full notice ends. Please choose a reason.")
            served_reason = reason
    for e in errors:
        st.error(e)
    if errors:
        return
    primary = next((a for a in areas if a["is_primary"]), None)
    vals = (headline.strip(), primary["function"] if primary else None, exp, role.strip(), company.strip(), skills.strip(),
            loc.strip(), mode, int(salary), status, int(notice), int(resigned), rdate.isoformat() if resigned else None,
            lwd.isoformat() if resigned else None, int(maxserve), served_reason, phone.strip(), int(visible), wn_db.now(),
            wn_db.now(), user["id"])
    wn_db.x("INSERT INTO candidates(headline, category, total_exp, current_role, current_company, skills, location, work_mode, "
            "expected_salary, employment_status, notice_days, resigned, resignation_date, last_working_day, max_notice_can_serve, "
            "shortfall_reason, phone, visible, confirmed_at, updated_at, user_id) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?) "
            "ON CONFLICT(user_id) DO UPDATE SET headline=excluded.headline, category=excluded.category, total_exp=excluded.total_exp, "
            "current_role=excluded.current_role, current_company=excluded.current_company, skills=excluded.skills, "
            "location=excluded.location, work_mode=excluded.work_mode, expected_salary=excluded.expected_salary, "
            "employment_status=excluded.employment_status, notice_days=excluded.notice_days, resigned=excluded.resigned, "
            "resignation_date=excluded.resignation_date, last_working_day=excluded.last_working_day, "
            "max_notice_can_serve=excluded.max_notice_can_serve, shortfall_reason=excluded.shortfall_reason, phone=excluded.phone, "
            "visible=excluded.visible, confirmed_at=excluded.confirmed_at, updated_at=excluded.updated_at", vals)
    st.session_state["toast"] = "Profile saved." + (f" Notice shortfall of {shortfall} days recorded." if shortfall else "")
    st.rerun()


def _d(iso, plus=0):
    try:
        return datetime.date.fromisoformat(iso)
    except (TypeError, ValueError):
        return datetime.date.today() + datetime.timedelta(days=plus)


def _cv_tab(user, cand):
    if not cand.get("headline"):
        st.info("Please save your profile (tab 2) first.")
        return
    if cand.get("cv"):
        st.markdown(f"Current CV: **{esc(cand['cv_name'])}**")
        st.download_button("Download my CV", cand["cv"], file_name=cand["cv_name"] or "cv.pdf", mime="application/pdf")
    up = st.file_uploader("Upload your CV (PDF, up to 5 MB)", type=["pdf"])
    if up and st.button("Upload and check my CV", type="primary"):
        data = up.getvalue()
        if len(data) > 5 * 1024 * 1024:
            st.error("Please upload a PDF smaller than 5 MB.")
            return
        text = wn_jobs_ai.cv_text(data)
        if len(text) < 50:
            st.error("We could not read text from this PDF (it may be a scanned image). Export your CV from Word as PDF. "
                     "Many company ATS systems cannot read scanned CVs either.")
            return
        with st.spinner("Checking your CV..."):
            review = wn_jobs_ai.review_cv(text)
        wn_db.x("UPDATE candidates SET cv=?, cv_name=?, cv_text=?, cv_review=?, updated_at=? WHERE user_id=?",
                (data, up.name, text, json.dumps(review), wn_db.now(), user["id"]))
        st.rerun()
    if cand.get("cv_review"):
        r = json.loads(cand["cv_review"])
        show_cv_review(r)
        threshold = wn_db.get_setting_num("ats_threshold")
        if (r.get("score") or 0) < threshold:
            with st.container(border=True):
                st.markdown(f"**Your ATS readiness score is below {int(threshold)}.** Use the free tips above, or get expert help:")
                c = st.columns(2)
                c[0].page_link(PAGES["services"], label=f"Expert CV review · {rupees(price('cv_review'))}",
                               query_params={"service": "cv_review"}, icon=":material/rate_review:")
                c[1].page_link(PAGES["services"], label=f"ATS-ready CV rewrite · {rupees(price('cv_rewrite'))}",
                               query_params={"service": "cv_rewrite"}, icon=":material/edit_document:")
                st.caption(SERVICES_NOTE)


def show_cv_review(r):
    c1, c2 = st.columns([1, 3])
    c1.metric("ATS readiness score", f"{int(r.get('score', 0))}/100")
    c2.markdown(f"{esc(r.get('summary', ''))}  \n<span class='wn-meta'>Checked by: {esc(r.get('engine', 'basic'))}. "
                "Every company's ATS is different; this score checks readability, contact details, skills and structure. "
                "Each job page also shows how well your CV matches that job's skills.</span>", unsafe_allow_html=True)
    if r.get("skills"):
        st.markdown("".join(f'<span class="wn-chip">{esc(s)}</span>' for s in r["skills"]), unsafe_allow_html=True)
    if r.get("strengths"):
        st.markdown("**Strengths**\n" + "\n".join(f"- {esc(s)}" for s in r["strengths"]))
    if r.get("improve"):
        st.markdown("**How to improve (free tips)**\n" + "\n".join(f"- {esc(s)}" for s in r["improve"]))
    if r.get("red_flags"):
        st.markdown("**Check these**\n" + "\n".join(f"- {esc(s)}" for s in r["red_flags"]))


# ---------------------------------------------------------------- demo interviews
def _interviews_tab(user, cand, areas):
    if not areas:
        st.info("Add at least one job area first (tab 1). You take one interview per job area.")
        return
    if not cand.get("headline"):
        st.info("Please save your profile (tab 2) first.")
        return
    done = st.session_state.pop("iv_done", None)
    pick = st.selectbox("Job area", areas, format_func=lambda a: area_label(a["industry"], a["function"], a["subrole"], a["level"]))
    s = wn_match.attempt_status(user["id"], pick["industry"], pick["function"])
    if done:
        last = wn_db.q("SELECT * FROM interviews WHERE id=?", (done,), one=True)
        if last and last["overall"] >= s["pass_mark"]:
            st.success(f"Well done! You scored {int(last['overall'])}/100, above the pass mark of {int(s['pass_mark'])}.")
        elif last:
            st.warning(f"You scored {int(last['overall'])}/100. The pass mark is {int(s['pass_mark'])}. "
                       + (f"You have {s['left']} free attempt(s) left for this area." if s["left"] else ""))
    c1, c2, c3 = st.columns(3)
    c1.metric("Best score", f"{int(s['best'])}/100" if s["best"] is not None else "-")
    c2.metric("Pass mark", f"{int(s['pass_mark'])}/100")
    c3.metric("Free attempts used", f"{min(s['used'], s['free'])} of {s['free']}")
    if s["offer_help"]:
        with st.container(border=True):
            st.markdown(f"**You have used your {s['free']} free attempts without reaching the pass mark.** An expert can help "
                        "you prepare. " + (f"Your next free retake opens on {s['next_date'].strftime('%d %b %Y')}."
                                           if s["next_date"] and not s["can_start"] else "A free retake is available now."))
            c = st.columns(2)
            c[0].page_link(PAGES["services"], label=f"1:1 mock interview · {rupees(price('mock_interview'))}",
                           query_params={"service": "mock_interview"}, icon=":material/video_call:")
            c[1].page_link(PAGES["services"], label=f"Coaching pack · {rupees(price('interview_coaching'))}",
                           query_params={"service": "interview_coaching"}, icon=":material/school:")
            st.caption(SERVICES_NOTE)
    st.markdown("### How the demo interview works")
    st.markdown("- **Part 1, written:** 5 questions for your industry, function and level (about 2 minutes each)\n"
                "- **Part 2, video:** 3 questions spoken by our interviewer; you answer on camera (up to 2 minutes each, "
                "one re-record allowed)\n"
                f"- Pass mark **{int(s['pass_mark'])}/100**. You have **{s['free']} free attempts** per job area, then one free "
                f"retake every {int(wn_db.get_setting_num('retake_days'))} days\n"
                "- Employers you apply to see your best score, written answers and videos")
    honest = st.checkbox("I will answer myself, without help from another person or an AI tool.", key=f"honest_{pick['id']}")
    st.caption(wn_ai.status_text())
    disabled = not honest or not s["can_start"]
    if st.button("Start interview", type="primary", disabled=disabled):
        qs = wn_match.build_interview(pick["industry"], pick["function"], pick["level"])
        for k in [k for k in st.session_state if str(k).startswith(("iv_ans_", "iv_voice_"))]:
            del st.session_state[k]
        st.session_state["iv"] = {"user": user["id"], "area": dict(pick), "qs": qs, "i": 0, "answers": [], "audio": {},
                                  "stage": "written", "videos": {}, "vqs": [], "vi": 0, "started": wn_db.now(),
                                  "t": time.time(), "nonce": int(time.time())}
        st.rerun()
    past = wn_db.area_interviews(user["id"], pick["industry"], pick["function"])
    if past:
        st.markdown("### Your attempts for this area")
        for n, iv in enumerate(past):
            with st.expander(f"{fmt_date(iv['finished_at'])} · {int(iv['overall'])}/100" + (" · latest" if n == 0 else "")):
                show_interview(iv, own=True, nested=True)


def _interview_runner(user, cand):
    iv = st.session_state["iv"]
    a = iv["area"]
    st.markdown(f"#### Demo interview · {esc(area_label(a['industry'], a['function'], a['subrole'], a['level']))}",
                unsafe_allow_html=True)
    if iv["stage"] == "written":
        i, qs = iv["i"], iv["qs"]
        st.progress(i / (len(qs) + 3), text=f"Part 1, written · question {i + 1} of {len(qs)}")
        st.markdown(f'<div class="wn-question">{esc(qs[i][0])}</div>', unsafe_allow_html=True)
        text = st.text_area("Your answer", height=180, key=f"iv_ans_{iv['nonce']}_{i}",
                            placeholder="Answer in your own words. Use a real example: what happened, what you did, the result.")
        voice = st.audio_input("Or record your answer by voice (optional)", key=f"iv_voice_{iv['nonce']}_{i}")
        c1, c2 = st.columns([1, 3])
        if c1.button("Next", type="primary"):
            answer = text.strip()
            audio = voice.getvalue() if voice else None
            if audio and not answer:
                with st.spinner("Turning your recording into text..."):
                    answer = wn_ai.transcribe(audio, voice.type or "audio/wav") or ""
                if not answer:
                    answer = "(Voice answer recorded. Text not available because AI transcription is off.)"
            if not answer:
                st.error("Please type or record an answer.")
                return
            iv["answers"].append({"q": qs[i][0], "keywords": qs[i][1], "answer": answer,
                                  "seconds": int(time.time() - iv["t"]), "voice": bool(audio)})
            if audio:
                iv["audio"][i] = audio
            iv["t"] = time.time()
            if i + 1 < len(qs):
                iv["i"] += 1
            else:
                iv["stage"] = "video_intro"
                iv["vqs"] = wn_match.build_video_questions(a["industry"], a["function"], a["level"], [x["q"] for x in iv["answers"]])
            st.rerun()
        if c2.button("Cancel interview"):
            st.session_state.pop("iv", None)
            st.rerun()
    elif iv["stage"] == "video_intro":
        st.progress(len(iv["qs"]) / (len(iv["qs"]) + 3), text="Part 2, video")
        st.markdown("### Part 2: video answers")
        st.markdown("Our interviewer will **ask 3 questions out loud**. Answer each on camera in up to **2 minutes**. "
                    "You can watch your answer and record once more before submitting.\n\n"
                    "**Tips:** sit in a quiet, well-lit place, look at the camera, and use a real example.")
        ok = st.checkbox("I agree that my video answers are saved to my profile and shown to employers I apply to, and to "
                         "verified employers if my profile is visible. I can delete them by deleting the interview.")
        c1, c2, c3 = st.columns([1.2, 1.4, 2])
        if c1.button("Start video round", type="primary", disabled=not ok):
            iv["stage"] = "video"
            st.rerun()
        if c2.button("Skip video (no camera)"):
            _finish_interview(user, iv)
        st.caption("Without the video round, employers see only your written answers.")
    elif iv["stage"] == "video":
        import wn_video
        vi = iv["vi"]
        st.progress((len(iv["qs"]) + vi) / (len(iv["qs"]) + 3), text=f"Part 2, video · question {vi + 1} of {len(iv['vqs'])}")
        out = wn_video.record_answer(iv["vqs"][vi], vi, len(iv["vqs"]), key=f"vid_{iv['nonce']}_{vi}")
        if out and out[0] == "error":
            st.error("Your camera or microphone could not start. Allow access in the browser, or skip the video round.")
            if st.button("Skip the rest of the video round"):
                _finish_interview(user, iv)
        elif out:
            iv["videos"][vi] = out
            if vi + 1 < len(iv["vqs"]):
                iv["vi"] += 1
                st.rerun()
            _finish_interview(user, iv)


def _finish_interview(user, iv):
    a = iv["area"]
    label = f"{a['industry']} · {a['function']}"
    with st.spinner("Scoring your interview..."):
        written = wn_jobs_ai.score_interview(label, iv["answers"])
        vids = []
        can_watch = "gemini" in wn_ai.providers()
        for vi, (data, mime, secs) in sorted(iv["videos"].items()):
            r = wn_jobs_ai.score_video_answer(iv["vqs"][vi], data, mime) if can_watch else None
            vids.append((vi, data, mime, secs, r))
        overall, video_pct = wn_jobs_ai.combine(written, [v[4] for v in vids])
    result = dict(written)
    result.update({"written_overall": written["overall"], "video_overall": video_pct, "overall": overall,
                   "videos": len(vids), "video_scored": video_pct is not None})
    qa = [{k: x[k] for k in ("q", "answer", "seconds", "voice")} for x in iv["answers"]]
    iid = wn_db.x("INSERT INTO interviews(user_id, category, qa, result, overall, engine, started_at, finished_at, industry, "
                  "function, subrole, level) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                  (user["id"], label, json.dumps(qa), json.dumps(result), overall, written["engine"], iv["started"],
                   wn_db.now(), a["industry"], a["function"], a["subrole"], a["level"]))
    for qi, audio in iv["audio"].items():
        wn_db.x("INSERT INTO interview_audio(interview_id, q_index, audio) VALUES (?,?,?)", (iid, qi, audio))
    for vi, data, mime, secs, r in vids:
        wn_db.x("INSERT INTO interview_video(interview_id, q_index, question, video, mime, seconds, score, feedback, transcript) "
                "VALUES (?,?,?,?,?,?,?,?,?)", (iid, vi, iv["vqs"][vi], data, mime, secs, (r or {}).get("score"),
                                               (r or {}).get("feedback"), (r or {}).get("transcript")))
    s = wn_match.attempt_status(user["id"], a["industry"], a["function"])
    msg = f"Your {a['function']} demo interview scored {overall}/100 (pass mark {int(s['pass_mark'])})."
    if s["offer_help"]:
        msg += " You have used your free attempts; expert mock interviews are available in Career services if you want help."
    wn_db.notify(user["id"], "Interview scored", msg)
    st.session_state.pop("iv", None)
    st.session_state["iv_done"] = iid
    st.rerun()


def show_interview(iv, own=False, nested=False):
    r = json.loads(iv["result"]) if iv.get("result") else {}
    qa = json.loads(iv["qa"])
    c1, c2, c3, c4 = st.columns([1, 1, 1, 2.4])
    c1.metric("Overall", f"{int(iv['overall'] or 0)}/100")
    c2.metric("Written", f"{int(r.get('written_overall', iv['overall'] or 0))}/100")
    c3.metric("Video", f"{int(r['video_overall'])}/100" if r.get("video_overall") is not None
              else ("Watch" if r.get("videos") else "-"))
    c4.markdown(f"{esc(r.get('summary', ''))}  \n<span class='wn-meta'>{esc(iv.get('category') or '')} · scored by "
                f"{esc(r.get('engine', ''))}{'' if r.get('video_scored') or not r.get('videos') else ' (videos not auto-scored)'}"
                f"</span>", unsafe_allow_html=True)
    if r.get("strengths"):
        st.markdown("**Strengths:** " + "; ".join(esc(s) for s in r["strengths"]))
    if r.get("improve"):
        st.markdown("**To improve:** " + "; ".join(esc(s) for s in r["improve"]))
    if r.get("flags") and not own:
        st.warning("Reviewer notes: " + "; ".join(esc(s) for s in r["flags"]))
    videos = wn_db.q("SELECT q_index, question, video, mime, seconds, score, feedback, transcript FROM interview_video "
                     "WHERE interview_id=? ORDER BY q_index", (iv["id"],))
    if videos:
        st.markdown("**Video answers**")
        cols = st.columns(min(len(videos), 3))
        for col, v in zip(cols, videos):
            with col:
                st.caption(f"V{v['q_index'] + 1}. {v['question']}")
                st.video(v["video"], format=v["mime"] or "video/webm")
                st.caption(f"{v['seconds']} sec" + (f" · score {v['score']}/5 · {v['feedback']}" if v["score"] else ""))
    if nested:
        st.markdown("**Written questions and answers**")
    box = st.container() if nested else st.expander("Written questions and answers")
    with box:
        audios = {x["q_index"]: x["audio"] for x in wn_db.q("SELECT q_index, audio FROM interview_audio WHERE interview_id=?",
                                                              (iv["id"],))}
        scores = r.get("answers") or []
        for n, x in enumerate(qa):
            sc = scores[n] if n < len(scores) else {}
            st.markdown(f"**Q{n + 1}. {esc(x['q'])}**  \n<span class='wn-meta'>{x.get('seconds', 0)} sec · score "
                        f"{sc.get('score', '-')}/5</span>", unsafe_allow_html=True)
            st.write(x["answer"])
            if n in audios:
                st.audio(audios[n])
            if sc.get("feedback"):
                st.caption(f"Feedback: {sc['feedback']}")


def _applications_tab(user):
    apps = wn_db.q("SELECT a.status, a.created_at, a.match_score, j.id, j.title, c.name AS company FROM applications a "
                   "JOIN jobs j ON j.id=a.job_id JOIN companies c ON c.id=j.company_id WHERE a.user_id=? ORDER BY a.id DESC",
                   (user["id"],))
    if not apps:
        st.caption("You have not applied to any jobs yet.")
        st.page_link(PAGES["jobs"], label="Browse jobs that fit my areas", icon=":material/work:")
    for ap in apps:
        c1, c2, c3, c4 = st.columns([3, 1, 1, 1])
        c1.markdown(f"**{esc(ap['title'])}** · {esc(ap['company'])}  \n<span class='wn-meta'>Applied {fmt_date(ap['created_at'])}</span>",
                    unsafe_allow_html=True)
        c2.markdown(match_chip(ap["match_score"] or 0), unsafe_allow_html=True)
        c3.markdown(f"**{ap['status'].title()}**")
        c4.page_link(PAGES["job"], label="View job", query_params={"id": ap["id"]})
    views = wn_db.q("SELECT c.name, MAX(v.viewed_at) AS at FROM profile_views v JOIN companies c ON c.id=v.company_id "
                    "WHERE v.user_id=? GROUP BY c.name ORDER BY at DESC", (user["id"],))
    if views:
        st.markdown("**Employers who viewed your profile**")
        for v in views:
            st.caption(f"{v['name']} · {fmt_date(v['at'])}")


# ---------------------------------------------------------------- career services (optional, paid)
def page_services():
    user = wn_auth.current_user()
    st.markdown('<h1 class="wn-serif" style="font-size:42px;margin-bottom:0">Career services</h1>', unsafe_allow_html=True)
    st.caption("Expert help with your CV and interviews, from professionals in your function.")
    st.markdown(f'<div class="wn-note">{SERVICES_NOTE} Jobs, applications, the CV check and your free interview attempts '
                'stay free.</div>', unsafe_allow_html=True)
    if user:
        cand = wn_db.candidate(user["id"]) or {}
        tips = []
        for a in wn_db.choices(user["id"]):
            s = wn_match.attempt_status(user["id"], a["industry"], a["function"])
            if s["offer_help"]:
                tips.append(f"Below the pass mark after {s['free']} attempts in {a['function']}: a 1:1 mock interview may help.")
        if cand.get("cv_review"):
            sc = json.loads(cand["cv_review"]).get("score") or 0
            if sc < wn_db.get_setting_num("ats_threshold"):
                tips.append(f"Your ATS readiness score is {int(sc)}: an expert CV review or rewrite may help.")
        for t in tips:
            st.info(t)
    want = st.query_params.get("service")
    st.write("")
    cols = st.columns(len(SERVICES))
    for col, (sid, title, _, desc) in zip(cols, SERVICES):
        with col.container(border=True):
            if sid == want:
                st.markdown('<span class="wn-badge wn-free">Suggested for you</span>', unsafe_allow_html=True)
            st.markdown(f"**{esc(title)}**")
            st.markdown(f'<div class="wn-price">{rupees(price(sid))}</div>', unsafe_allow_html=True)
            st.caption(desc)
            if st.button("Book", key=f"book_{sid}", type="primary" if sid == want else "secondary", width="stretch"):
                book_dialog(sid)
    if user:
        mine = wn_db.q("SELECT * FROM service_orders WHERE user_id=? ORDER BY id DESC", (user["id"],))
        if mine:
            st.markdown("### My bookings")
            for o in mine:
                st.markdown(f"**{esc(o['title'])}** · {rupees(o['price'])} · {esc(o['preferred_slot'] or '')} · "
                            f"**{o['status'].title()}**  \n<span class='wn-meta'>Ref {esc(o['payment_ref'])} · "
                            f"{fmt_date(o['created_at'])}</span>", unsafe_allow_html=True)
    st.caption("Refunds: full refund if you cancel at least 24 hours before your session, or if we cannot schedule it within "
               "7 days. Invoices are issued by SHROOP Global.")


@st.dialog("Book a career service", width="medium")
def book_dialog(sid):
    import uuid
    user = wn_auth.current_user()
    title = next(t for s, t, _, _ in SERVICES if s == sid)
    st.markdown(f"### {esc(title)}")
    if not user:
        st.write("Please sign in or create a free account to book.")
        st.page_link(PAGES["account"], label="Sign in / Create account", icon=":material/login:")
        return
    areas = wn_db.choices(user["id"])
    area = st.selectbox("For which job area?", ["General"] + [area_label(a["industry"], a["function"], a["subrole"], a["level"])
                                                              for a in areas])
    c1, c2 = st.columns(2)
    day = c1.date_input("Preferred date", value=datetime.date.today() + datetime.timedelta(days=2),
                        min_value=datetime.date.today() + datetime.timedelta(days=1), format="DD/MM/YYYY")
    slot = c2.selectbox("Preferred time", ["10:00–11:00", "12:00–13:00", "15:00–16:00", "18:00–19:00", "20:00–21:00"])
    notes = st.text_area("Anything we should know? (optional)", max_chars=500)
    st.metric("Price (incl. GST)", rupees(price(sid)))
    st.info("Demo mode: no money is charged. The live site takes payment through Razorpay and issues a GST invoice.")
    st.caption(SERVICES_NOTE)
    if st.button(f"Pay {rupees(price(sid))} (demo) and book", type="primary", width="stretch"):
        ref = "SVC-" + uuid.uuid4().hex[:8].upper()
        wn_db.x("INSERT INTO service_orders(user_id, service, title, price, area, preferred_slot, notes, payment_ref, created_at) "
                "VALUES (?,?,?,?,?,?,?,?,?)", (user["id"], sid, title, price(sid), area, f"{day.strftime('%d %b %Y')} {slot}",
                                               notes.strip(), ref, wn_db.now()))
        wn_db.notify(user["id"], f"Booked: {title}", f"We will confirm your session for {day.strftime('%d %b %Y')} {slot}. Ref {ref}.")
        for adm in wn_db.q("SELECT id FROM users WHERE role='admin'"):
            wn_db.notify(adm["id"], "New career service booking", f"{title} for {user['email']} ({area}).")
        st.session_state["toast"] = "Booked! See My bookings below."
        st.rerun()


# ---------------------------------------------------------------- what employers see
def candidate_view(uid, company_id=None, contact=False, ctx="v", job=None):
    u = wn_db.q("SELECT id, name, email FROM users WHERE id=?", (uid,), one=True)
    c = wn_db.candidate(uid)
    if not u or not c:
        st.caption("Profile not available.")
        return
    if company_id and not wn_db.q("SELECT 1 FROM profile_views WHERE company_id=? AND user_id=? AND viewed_at>?",
                                  (company_id, uid, (datetime.datetime.now() - datetime.timedelta(days=1)).isoformat()), one=True):
        wn_db.x("INSERT INTO profile_views(company_id, user_id, viewed_at) VALUES (?,?,?)", (company_id, uid, wn_db.now()))
    st.markdown(f"### {esc(u['name'])}")
    st.markdown(f"**{esc(c['headline'])}**")
    areas = wn_db.choices(uid)
    if areas:
        st.markdown("**Job areas:** " + " · ".join(f"{esc(a['function'])} ({esc(a['industry'])}, {esc(a['level'])})"
                                                   for a in areas), unsafe_allow_html=True)
    st.markdown(f'<div class="wn-facts"><div><span>Experience</span><b>{c["total_exp"]:g} years</b></div>'
                f'<div><span>Current role</span><b>{esc(c["current_role"] or "-")}</b></div>'
                f'<div><span>City</span><b>{esc(c["location"] or "-")}</b></div>'
                f'<div><span>Work mode</span><b>{esc(c["work_mode"])}</b></div>'
                f'<div><span>Expected</span><b>{"₹{:,}/month".format(c["expected_salary"]) if c["expected_salary"] else "-"}</b></div>'
                f'</div>', unsafe_allow_html=True)
    st.markdown(f"**Availability:** {notice_text(c)} · can join in about **{join_days(c)} days** · _{fresh_text(c)}_")
    if c["skills"]:
        st.markdown("".join(f'<span class="wn-chip">{esc(s.strip())}</span>' for s in c["skills"].split(",") if s.strip()),
                    unsafe_allow_html=True)
    if contact:
        st.markdown(f"**Contact:** {esc(u['email'])}" + (f" · {esc(c['phone'])}" if c["phone"] else ""))
    fn = (job.get("function") or job.get("category")) if job else None
    iv = wn_db.best_interview(uid, job.get("industry"), fn) if job else wn_db.best_interview(uid)
    if iv:
        st.markdown(f"#### Demo interview · {esc(iv['category'])} · {fmt_date(iv['finished_at'])}")
        show_interview(iv, nested=True)
    else:
        st.caption("No demo interview for this area yet.")
    if c["cv"]:
        st.markdown("#### CV")
        if c["cv_review"]:
            r = json.loads(c["cv_review"])
            st.caption(f"ATS readiness score {int(r.get('score', 0))}/100 · {r.get('summary', '')}")
        if job:
            pct, found, missing = wn_match.cv_job_match(c.get("cv_text"), job)
            if pct is not None:
                st.caption(f"CV covers {pct}% of this job's skills" + (f"; missing {', '.join(missing)}" if missing else ""))
        st.download_button("Download CV", c["cv"], file_name=c["cv_name"] or "cv.pdf", mime="application/pdf",
                           key=f"cv_{ctx}_{uid}")


# ---------------------------------------------------------------- employers
def page_employers():
    user = wn_auth.current_user()
    st.markdown('<h1 class="wn-serif" style="font-size:42px;margin-bottom:0">For employers</h1>', unsafe_allow_html=True)
    st.caption("Post jobs by industry, function and level. Get candidates ranked by match %, written + video interview scores "
               "and real joining dates, before you make a single call.")
    if not user:
        c1, c2, c3 = st.columns(3)
        for col, (t, d) in zip((c1, c2, c3), [
            ("Precise matching", "Candidates choose at most 4 job areas, so only people who do this work can apply."),
            ("Watch before you call", "Written answers, video answers and an ATS-checked CV for every applicant."),
            ("Real joining dates", "Notice period, resignation and last working day, reconfirmed every 14 days.")]):
            with col.container(border=True):
                st.markdown(f"**{t}**")
                st.caption(d)
        st.page_link(PAGES["account"], label="Create an account to start hiring", icon=":material/login:")
        return
    comp = wn_db.company_of(user["id"])
    if not comp or comp["status"] == "rejected":
        if comp:
            st.error(f"Your company was not verified. Note: {comp['admin_note'] or '-'}. You can apply again.")
        _company_form(user)
        return
    if comp["status"] == "pending":
        st.info(f"**{esc(comp['name'])}** is waiting for verification. We check your GSTIN/CIN and work email, usually within "
                "one working day. You will get a message in My dashboard.")
        return
    st.markdown(f"**{esc(comp['name'])}** {VERIFIED}", unsafe_allow_html=True)
    tabs = st.tabs(["My jobs and applicants", "Post a job", "Find candidates"])
    with tabs[0]:
        _my_jobs(comp)
    with tabs[1]:
        _post_job(user, comp)
    with tabs[2]:
        _find_candidates(comp)


def _company_form(user):
    st.markdown("### Register your company")
    with st.form("company"):
        c1, c2 = st.columns(2)
        name = c1.text_input("Company name (as registered)")
        site = c2.text_input("Website")
        c3, c4, c5 = st.columns(3)
        email = c3.text_input("Work email (company domain)", value=user["email"])
        gst = c4.text_input("GSTIN")
        cin = c5.text_input("CIN / registration no. (optional)")
        city = st.text_input("City")
        about = st.text_area("About the company", max_chars=800)
        pledge = st.checkbox("We will never ask candidates for any payment, and we agree to the Wordnest employer terms.")
        sent = st.form_submit_button("Submit for verification", type="primary")
    if sent:
        if len(name.strip()) < 3 or not (gst.strip() or cin.strip()) or not pledge:
            st.error("Please add the company name, a GSTIN or CIN, and accept the pledge.")
            return
        wn_db.x("INSERT INTO companies(owner_id, name, website, work_email, gstin, cin, city, about, created_at) "
                "VALUES (?,?,?,?,?,?,?,?,?)", (user["id"], name.strip(), site.strip(), email.strip(), gst.strip().upper(),
                                               cin.strip().upper(), city.strip(), about.strip(), wn_db.now()))
        for a in wn_db.q("SELECT id FROM users WHERE role='admin'"):
            wn_db.notify(a["id"], "Company to verify", f"{name.strip()} registered as an employer.")
        st.rerun()


def _post_job(user, comp):
    msg = st.session_state.pop("job_msg", None)
    if msg:
        st.success(msg)
    n = st.session_state.get("job_n", 0)
    st.markdown("**1. Job area**")
    c1, c2, c3, c4 = st.columns(4)
    ind = c1.selectbox("Industry", INDUSTRIES, key=f"pj_ind_{n}")
    fn = c2.selectbox("Function", FUNCTION_NAMES, key=f"pj_fn_{n}")
    sub = c3.selectbox("Sub-role", subroles(ind, fn), key=f"pj_sub_{n}_{ind}_{fn}")
    lvl = c4.selectbox("Level", LEVELS, index=1, key=f"pj_lvl_{n}", format_func=lambda x: f"{x} ({LEVEL_YEARS[x]})")
    ind_req = st.checkbox(f"Candidates must have experience in {ind} (leave unticked if {fn} skills from any industry are fine)",
                          key=f"pj_req_{n}")
    st.markdown("**2. Job details**")
    with st.form(f"job_form_{n}"):
        title = st.text_input("Job title", placeholder="e.g. WFM Real-time Analyst (US shift)")
        c1, c2, c3 = st.columns(3)
        mode = c1.selectbox("Work mode", WORK_MODES)
        jtype = c2.selectbox("Job type", JOB_TYPES)
        loc = c3.text_input("Location", value=comp["city"] or "")
        c4, c5, c6 = st.columns(3)
        emin = c4.number_input("Min experience (years)", 0, 30, 0)
        emax = c5.number_input("Max experience (years)", 0, 40, 3)
        notice = c6.number_input("Must join within (days)", 0, 180, 30, step=15)
        s1, s2 = st.columns(2)
        smin = s1.number_input("Salary from (₹/month)", 0, 1_000_000, 20000, step=1000)
        smax = s2.number_input("Salary to (₹/month)", 0, 1_000_000, 30000, step=1000)
        skills = st.text_input("Skills (comma separated; used for matching)")
        desc = st.text_area("Job description", height=200,
                            placeholder="What the person will do, shift timings, who they report to, what you offer.")
        needs_iv = st.checkbox("Ask applicants to complete the demo interview (written + video) for this job area", value=True)
        sent = st.form_submit_button("Check and publish", type="primary")
    if not sent:
        return
    if len(title.strip()) < 5 or len(desc.split()) < 30 or (smax and smin > smax) or emax < emin:
        st.error("Please add a title, a description of at least 30 words, and check the salary and experience ranges.")
        return
    with st.spinner("Checking the job post for scams and unfair requirements..."):
        rep = wn_moderation.review(f"{title}\n{ind} / {fn} / {sub} / {lvl}\n{loc}\nSalary {smin}-{smax} per month\n{skills}\n{desc}",
                                   "job")
    status = {"block": "ai_blocked", "review": "pending", "pass": "published"}[rep["decision"]]
    jid = wn_db.x("INSERT INTO jobs(company_id, title, category, industry, function, subrole, level, industry_required, location, "
                  "work_mode, job_type, exp_min, exp_max, salary_min, salary_max, skills, description, max_notice_days, "
                  "needs_interview, status, ai_decision, ai_report, created_at, published_at) "
                  "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                  (comp["id"], title.strip(), fn, ind, fn, sub, lvl, int(ind_req), loc.strip(), mode, jtype, int(emin), int(emax),
                   int(smin) or None, int(smax) or None, skills.strip(), desc.strip(), int(notice), int(needs_iv), status,
                   rep["decision"], json.dumps(rep), wn_db.now(), wn_db.now() if status == "published" else None))
    wn_db.log_moderation("job", jid, rep["decision"], rep.get("engine", "rules"), rep)
    if status == "published":
        st.session_state["job_msg"] = f"Published: {title.strip()}"
        st.session_state["job_n"] = n + 1
        st.rerun()
    st.markdown("#### Review result")
    show_review(rep)
    st.warning("Not published yet: " + ("blocked by the review. Please edit the post." if status == "ai_blocked"
                                         else "an editor will check it shortly."))


def _my_jobs(comp):
    jobs = wn_db.q("SELECT j.*, c.name AS company, (SELECT COUNT(*) FROM applications a WHERE a.job_id=j.id) AS n FROM jobs j "
                   "JOIN companies c ON c.id=j.company_id WHERE j.company_id=? "
                   "ORDER BY (j.status='published') DESC, n DESC, j.id DESC", (comp["id"],))
    if not jobs:
        st.caption("No jobs yet. Use 'Post a job'.")
        return
    pick = st.selectbox("Job", jobs, format_func=lambda j: f"{j['title']} · {j['status']} · {j['n']} applicant(s)")
    st.caption(job_area(pick))
    c = st.columns([1, 1, 3])
    c[0].page_link(PAGES["job"], label="View post", query_params={"id": pick["id"]})
    if pick["status"] == "published" and c[1].button("Close job"):
        wn_db.x("UPDATE jobs SET status='closed' WHERE id=?", (pick["id"],))
        st.rerun()
    apps = wn_db.q("SELECT a.*, u.name, c.headline, c.total_exp, c.employment_status, c.notice_days, c.resigned, "
                   "c.last_working_day, c.max_notice_can_serve, c.resignation_date, c.shortfall_reason, c.confirmed_at "
                   "FROM applications a JOIN users u ON u.id=a.user_id LEFT JOIN candidates c ON c.user_id=a.user_id "
                   "WHERE a.job_id=?", (pick["id"],))
    if not apps:
        st.caption("No applicants yet.")
        return
    for a in apps:
        iv = wn_db.best_interview(a["user_id"], pick.get("industry"), pick.get("function") or pick["category"])
        a["score"] = iv["overall"] if iv else None
        a["days"] = join_days(a)
    f1, f2, f3 = st.columns(3)
    only_ok = f1.toggle(f"Can join within {pick['max_notice_days']} days")
    min_match = f2.slider("Minimum match %", 0, 100, 0, step=5)
    min_score = f3.slider("Minimum interview score", 0, 100, 0, step=5)
    apps.sort(key=lambda a: (-(a["match_score"] or 0), -(a["score"] or 0)))
    shown = 0
    for a in apps:
        if (only_ok and (a["days"] is None or a["days"] > pick["max_notice_days"])) or (a["match_score"] or 0) < min_match \
                or (a["score"] or 0) < min_score:
            continue
        shown += 1
        with st.container(border=True):
            k1, k2, k3, k4, k5 = st.columns([2.5, 0.9, 1, 1, 0.9], vertical_alignment="center")
            k1.markdown(f"**{esc(a['name'])}** · {esc(a['headline'] or '')}  \n<span class='wn-meta'>"
                        f"{(a['total_exp'] or 0):g} yrs · {notice_text(a)} · applied {fmt_date(a['created_at'])}</span>",
                        unsafe_allow_html=True)
            k2.markdown(match_chip(a["match_score"] or 0), unsafe_allow_html=True)
            k3.metric("Interview", f"{int(a['score'])}/100" if a["score"] is not None else "-")
            k4.metric("Joins in", f"{a['days']} days" if a["days"] is not None else "-")
            k5.markdown(f"**{a['status'].title()}**")
            if a["note"]:
                st.caption(f"Note: {a['note']}")
            if st.toggle("Show full profile, videos and CV", key=f"open_{a['id']}"):
                candidate_view(a["user_id"], comp["id"], contact=True, ctx=f"app{a['id']}", job=pick)
            b = st.columns(4)
            for col, (label, val) in zip(b, [("Shortlist", "shortlisted"), ("Reject", "rejected"), ("Hired", "hired")]):
                if col.button(label, key=f"{val}_{a['id']}"):
                    wn_db.x("UPDATE applications SET status=? WHERE id=?", (val, a["id"]))
                    wn_db.notify(a["user_id"], f"Update on {pick['title']}", f"{comp['name']} marked your application as {val}.")
                    st.rerun()
    if not shown:
        st.caption("No applicants match these filters.")


def _find_candidates(comp):
    st.caption("People who chose to be visible to verified employers. Contact details are shared when they apply to your job.")
    f1, f2, f3 = st.columns(3)
    fn = f1.selectbox("Function", ["All"] + FUNCTION_NAMES, key="fc_fn")
    ind = f2.selectbox("Industry", ["All"] + INDUSTRIES, key="fc_ind")
    lvl = f3.selectbox("Level", ["All"] + LEVELS, key="fc_lvl")
    f4, f5, f6 = st.columns(3)
    max_join = f4.number_input("Can join within (days)", 0, 180, 90, step=15)
    min_score = f5.slider("Min interview score", 0, 100, 0, step=5, key="fc_score")
    kw = f6.text_input("Skill or keyword", key="fc_kw")
    rows = wn_db.q("SELECT c.*, u.name FROM candidates c JOIN users u ON u.id=c.user_id WHERE c.visible=1 AND u.status='active'")
    out = []
    for r in rows:
        areas = wn_db.choices(r["user_id"])
        fit = [a for a in areas if (fn == "All" or a["function"] == fn) and (ind == "All" or a["industry"] == ind)
               and (lvl == "All" or a["level"] == lvl)]
        if not fit:
            continue
        iv = wn_db.best_interview(r["user_id"], fit[0]["industry"], fit[0]["function"])
        score = iv["overall"] if iv else None
        d = join_days(r)
        if (score or 0) < min_score or (d is not None and d > max_join):
            continue
        if kw and kw.lower() not in f"{r['headline']} {r['skills']} {r['current_role']}".lower():
            continue
        out.append((r, fit[0], score, d))
    out.sort(key=lambda t: -(t[2] or 0))
    st.markdown(f"**{len(out)} candidate(s)**")
    for r, a, score, d in out:
        with st.container(border=True):
            k1, k2, k3 = st.columns([3, 1, 1], vertical_alignment="center")
            k1.markdown(f"**{esc(r['name'])}** · {esc(r['headline'])}  \n<span class='wn-meta'>{esc(a['function'])} · "
                        f"{esc(a['industry'])} · {esc(a['level'])} · {(r['total_exp'] or 0):g} yrs · {esc(r['location'] or '')}</span>",
                        unsafe_allow_html=True)
            k2.metric("Interview", f"{int(score)}/100" if score is not None else "-")
            k3.metric("Joins in", f"{d} days" if d is not None else "-")
            if st.toggle("View profile", key=f"fc_open_{r['user_id']}"):
                candidate_view(r["user_id"], comp["id"], contact=False, ctx="find",
                               job={"industry": a["industry"], "function": a["function"]})
