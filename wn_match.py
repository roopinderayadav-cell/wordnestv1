"""Wordnest Jobs - matching job seekers to jobs, building interviews and the attempt rules.

Match score (0-100) for a candidate and a job:
  Function matches one of the candidate's job areas ........ required (else not eligible)
  Industry required by the employer and not in that area ... not eligible
  Function ................................................. 20
  Sub-role ................................................. 10
  Industry ................................................. 20 (5 if a different industry)
  Level .................................................... 15 (8 if one level away)
  Skills overlap (job skills found in profile + CV) ........ 15
  Can join within the employer's deadline .................. 10
  Work mode / location ...................................... 5
  Passed the demo interview for this area ................... 5
"""
import datetime
import random
import re

import wn_db
from wn_jobs_data import (CORE_QUESTIONS, FUNCTION_QUESTIONS, GENERAL_QUESTIONS, GENERIC_CORE_QUESTIONS,
                          INDUSTRY_KEYWORDS, INDUSTRY_QUESTIONS, LEADERSHIP_QUESTIONS, LEVELS)


def _skills(text):
    return [s.strip().lower() for s in (text or "").split(",") if s.strip()]


def cv_job_match(cv_text, job):
    """Share of the job's listed skills that appear in the CV (job-specific ATS-style check)."""
    skills = _skills(job.get("skills"))
    if not skills or not cv_text:
        return None, [], skills
    low = cv_text.lower()
    found = [s for s in skills if re.search(r"(?<![\w])" + re.escape(s) + r"(?![\w])", low)]
    return round(len(found) / len(skills) * 100), found, [s for s in skills if s not in found]


def join_days(c):
    if not c:
        return None
    if c.get("employment_status") in ("Available now (not working)", "Fresher"):
        return 0
    if c.get("resigned") and c.get("last_working_day"):
        try:
            return max((datetime.date.fromisoformat(c["last_working_day"]) - datetime.date.today()).days, 0)
        except ValueError:
            pass
    nd = c.get("notice_days") or 0
    if c.get("max_notice_can_serve"):
        nd = min(nd, c["max_notice_can_serve"])
    return nd


def best_area_for(areas, job):
    """The candidate's job area that fits this job best (or None)."""
    fn = job.get("function") or job.get("category")
    same_fn = [a for a in areas if a["function"] == fn]
    if not same_fn:
        return None
    exact = [a for a in same_fn if a["industry"] == job.get("industry")]
    return (exact or same_fn)[0]


def eligibility(areas, job):
    """Returns (eligible, reason, area)."""
    fn = job.get("function") or job.get("category")
    area = best_area_for(areas, job)
    if not areas:
        return False, "Add your job areas in My job profile first.", None
    if not area:
        return False, f"This job is in {fn}, which is not one of your job areas.", None
    if job.get("industry_required") and area["industry"] != job.get("industry"):
        return False, f"The employer needs experience in {job.get('industry')} for {fn}.", None
    return True, "", area


def match(user_id, job, cand=None, areas=None):
    """Full match result for a candidate and a job."""
    cand = cand if cand is not None else wn_db.candidate(user_id)
    areas = areas if areas is not None else wn_db.choices(user_id)
    ok, reason, area = eligibility(areas, job)
    if not ok:
        return {"eligible": False, "score": 0, "reason": reason, "parts": [], "area": None}
    parts = [("Function", 20, 20)]
    parts.append(("Sub-role", 10 if not job.get("subrole") or job.get("subrole") == area.get("subrole") else 4, 10))
    parts.append(("Industry", 20 if area["industry"] == job.get("industry") else 5, 20))
    try:
        gap = abs(LEVELS.index(area["level"]) - LEVELS.index(job.get("level") or area["level"]))
    except ValueError:
        gap = 1
    parts.append(("Level", 15 if gap == 0 else 8 if gap == 1 else 0, 15))
    skills = _skills(job.get("skills"))
    have = f"{(cand or {}).get('skills') or ''} {(cand or {}).get('headline') or ''} {(cand or {}).get('cv_text') or ''}".lower()
    hit = sum(1 for s in skills if s in have)
    parts.append(("Skills", round(15 * hit / len(skills)) if skills else 8, 15))
    d = join_days(cand)
    limit = job.get("max_notice_days") or 90
    parts.append(("Joining date", 10 if d is not None and d <= limit else 4 if d is not None and d <= limit + 30 else 0, 10))
    mode_ok = job.get("work_mode") == "Work from home" or (cand or {}).get("work_mode") == job.get("work_mode") or \
        ((cand or {}).get("location") or "").lower() in (job.get("location") or "").lower()
    parts.append(("Work mode / city", 5 if mode_ok else 2, 5))
    iv = wn_db.best_interview(user_id, area["industry"], area["function"])
    passed = iv and (iv["overall"] or 0) >= wn_db.get_setting_num("pass_mark")
    parts.append(("Demo interview passed", 5 if passed else 0, 5))
    return {"eligible": True, "score": int(sum(p[1] for p in parts)), "reason": "", "parts": parts, "area": area,
            "interview": iv}


# ---------------------------------------------------------------- interviews
def build_interview(industry, function, level, n=5):
    """5 questions: intro + function/industry core + leadership (TL and above) + industry."""
    if function == "Core Operations":
        bank = CORE_QUESTIONS.get(industry, GENERIC_CORE_QUESTIONS)
    else:
        bank = FUNCTION_QUESTIONS.get(function, GENERIC_CORE_QUESTIONS)
    leader = level in LEVELS[2:]
    core = random.sample(bank, min(len(bank), 2 if leader else 3))
    qs = [GENERAL_QUESTIONS[0]] + core
    if leader:
        qs.append(random.choice(LEADERSHIP_QUESTIONS))
    qs.append((random.choice(INDUSTRY_QUESTIONS).format(industry=industry), INDUSTRY_KEYWORDS))
    return qs[:n]


def build_video_questions(industry, function, level, used_questions):
    """3 spoken questions for the camera round, different from the written ones."""
    if function == "Core Operations":
        bank = CORE_QUESTIONS.get(industry, GENERIC_CORE_QUESTIONS)
    else:
        bank = FUNCTION_QUESTIONS.get(function, GENERIC_CORE_QUESTIONS)
    unused = [q for q, _ in bank if q not in used_questions] or [q for q, _ in bank]
    qs = [f"Please introduce yourself on camera in under two minutes: your experience, your strongest skill, "
          f"and why you want a role in {function}.", random.choice(unused)]
    if level in LEVELS[2:]:
        lead = [q for q, _ in LEADERSHIP_QUESTIONS if q not in used_questions]
        qs.append(random.choice(lead or [q for q, _ in LEADERSHIP_QUESTIONS]))
    else:
        ind = [t.format(industry=industry) for t in INDUSTRY_QUESTIONS]
        qs.append(random.choice([q for q in ind if q not in used_questions] or ind))
    return qs


def attempt_status(user_id, industry, function):
    """How many free attempts are left for a job area, and whether paid help should be offered."""
    pass_mark = wn_db.get_setting_num("pass_mark")
    free = int(wn_db.get_setting_num("free_attempts"))
    days = int(wn_db.get_setting_num("retake_days"))
    ivs = wn_db.area_interviews(user_id, industry, function)
    best = max((i["overall"] or 0 for i in ivs), default=None)
    passed = best is not None and best >= pass_mark
    used = len(ivs)
    can_start, next_date = True, None
    if not passed and used >= free:
        last = datetime.datetime.fromisoformat(ivs[0]["finished_at"])
        next_dt = last + datetime.timedelta(days=days)
        can_start = datetime.datetime.now() >= next_dt
        next_date = next_dt.date()
    return {"used": used, "free": free, "left": max(free - used, 0), "best": best, "passed": passed,
            "pass_mark": pass_mark, "can_start": can_start, "next_date": next_date,
            "offer_help": (not passed) and used >= free}
