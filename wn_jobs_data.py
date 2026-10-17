"""Wordnest Jobs - industries, functions (with sub-roles), levels, interview question banks and career services.

How a job area works:  Industry  ×  Function (+ sub-role)  ×  Level
  e.g.  Travel & Tourism  ×  WFM (Workforce Management) / Real-time analyst  ×  Associate
A job seeker picks up to 4 job areas. A job post has exactly one.

How an interview is built (5 questions):
  - "Introduce yourself" (general)
  - 2 or 3 questions from the FUNCTION bank (Core Operations uses the industry's own bank)
  - 1 leadership question for Team Lead and above
  - 1 question about the INDUSTRY
Each question has a few keywords, used only by the basic scorer when AI is off.
Edit these lists freely: add questions, industries or sub-roles; the site picks them up automatically.
"""

INDUSTRIES = ["Travel & Tourism", "BPO / BPM / KPO", "IT & Software", "Banking & Financial Services", "Insurance",
              "Healthcare & Pharma", "E-commerce & Retail", "Logistics & Supply Chain", "Telecom", "Education & EdTech",
              "Hospitality", "Manufacturing", "Consulting & Professional Services", "Legal Services",
              "Media & Entertainment", "Real Estate & Construction"]

CORE_SUBROLES = {
    "Travel & Tourism": ["Air ticketing & reservations", "Refunds & reissues", "Hotel & car bookings",
                         "Visa & documentation", "Corporate travel desk", "Travel fulfilment"],
    "BPO / BPM / KPO": ["Voice process", "Non-voice / back office", "Chat & email process", "Collections"],
    "IT & Software": ["Software development", "Testing / QA", "DevOps & cloud"],
    "Banking & Financial Services": ["Loan operations", "KYC operations", "Payments & cards"],
    "Insurance": ["Claims processing", "Underwriting support", "Policy servicing"],
    "Healthcare & Pharma": ["Medical coding", "Medical billing", "Pharmacovigilance"],
    "E-commerce & Retail": ["Order management", "Catalog management", "Store operations"],
    "Logistics & Supply Chain": ["Shipment tracking", "Warehouse operations", "Procurement"],
}
DEFAULT_CORE_SUBROLES = ["Operations executive", "Operations specialist"]

FUNCTIONS = {
    "Core Operations": [],  # sub-roles come from the industry (CORE_SUBROLES)
    "Customer Support": ["Voice support", "Chat & email support", "Escalations desk"],
    "Sales & Business Development": ["Inside sales", "Field sales", "Key accounts", "Business development"],
    "BU HR / HR Business Partner": ["HR business partner", "Employee relations", "HR operations"],
    "Recruitment / Talent Acquisition": ["Volume hiring", "Lateral hiring", "Campus hiring"],
    "Payroll": ["Payroll processing", "Statutory compliance (PF, ESI, PT)", "Payroll audit"],
    "Admin & Facilities": ["Office administration", "Facilities management", "Transport desk"],
    "Finance & Accounts": ["Accounts payable", "Accounts receivable", "General ledger & reporting",
                           "Taxation (GST, TDS)"],
    "Legal": ["Lawyer / Advocate", "Legal counsel", "Contracts & documentation"],
    "Risk & Compliance": ["Operational risk", "Compliance", "Internal audit", "Fraud prevention"],
    "Data Analytics": ["Data analyst", "MIS & reporting", "Business intelligence"],
    "WFM (Workforce Management)": ["Forecasting", "Scheduling", "Real-time analyst", "Capacity planning"],
    "Quality": ["Quality analyst", "Quality lead", "Process excellence (Lean / Six Sigma)"],
    "Training": ["Process trainer", "Soft-skills trainer", "Training lead"],
    "Project Management": ["Project coordinator", "Project manager", "PMO", "Transition / migration"],
    "IT Support": ["Desktop support", "Application support", "Network & security"],
    "Marketing": ["Digital marketing", "Content", "Brand & events"],
}

LEVELS = ["Fresher / Entry", "Associate / Senior Associate", "Team Lead / SME", "Manager", "Senior Leadership"]
LEVEL_YEARS = {"Fresher / Entry": "0–1 years", "Associate / Senior Associate": "1–4 years", "Team Lead / SME": "3–7 years",
               "Manager": "6–12 years", "Senior Leadership": "12+ years"}

WORK_MODES = ["Work from home", "Work from office", "Hybrid"]
JOB_TYPES = ["Full-time", "Part-time", "Contract", "Internship"]
EMPLOYMENT_STATUS = ["Employed, not resigned", "Serving notice period", "Available now (not working)", "Fresher"]
SHORTFALL_REASONS = ["Early release agreed with employer", "New employer will buy out notice", "Leave balance adjusted",
                     "Contract ending", "Other"]
MAX_AREAS = 4


def subroles(industry, function):
    if function == "Core Operations":
        return CORE_SUBROLES.get(industry, DEFAULT_CORE_SUBROLES)
    return FUNCTIONS.get(function, [])


def suggest_level(years):
    years = float(years or 0)
    if years < 1:
        return LEVELS[0]
    if years < 4:
        return LEVELS[1]
    if years < 7:
        return LEVELS[2]
    if years < 12:
        return LEVELS[3]
    return LEVELS[4]


def area_label(industry, function, subrole=None, level=None):
    parts = [industry, function + (f" · {subrole}" if subrole else "")]
    if level:
        parts.append(level)
    return " → ".join(parts)


# ---------------------------------------------------------------- question banks: (question, keywords)
FUNCTION_QUESTIONS = {
    "Customer Support": [
        ("A customer has been transferred three times and is now angry. What do you say in the first 30 seconds?",
         ["sorry", "understand", "name", "help", "own", "listen"]),
        ("How do you handle a request you are not allowed to approve?", ["explain", "policy", "alternative", "escalate", "polite"]),
        ("Many chats are waiting. How do you keep quality while working faster?", ["template", "priority", "accurate", "focus", "quality"]),
        ("Describe a time you turned an unhappy customer into a satisfied one.", ["listen", "solution", "follow", "result"]),
        ("How do you protect a customer's personal and card details while helping them?", ["verify", "privacy", "mask", "card", "security"]),
    ],
    "Sales & Business Development": [
        ("Sell us a product or service you know well in under one minute.", ["benefit", "customer", "value", "price", "problem"]),
        ("A client says your price is too high. How do you respond?", ["value", "understand", "compare", "option", "discount"]),
        ("How do you plan your week to meet a monthly target?", ["target", "pipeline", "follow up", "leads", "plan"]),
        ("Tell us about a deal you lost and what you learnt.", ["lost", "learn", "reason", "improve"]),
        ("How do you keep an existing client coming back?", ["relationship", "service", "follow up", "trust", "feedback"]),
    ],
    "BU HR / HR Business Partner": [
        ("Attrition in one team has doubled in three months. How do you find the cause and what do you do?",
         ["exit interviews", "data", "manager", "survey", "action plan", "engagement"]),
        ("An employee complains about their manager. What are your first steps?", ["listen", "confidential", "document", "policy", "investigate"]),
        ("How do you support a business head during an appraisal cycle?", ["calibration", "ratings", "fair", "data", "communication"]),
        ("How would you handle a performance improvement plan for a long-serving employee?",
         ["goals", "support", "document", "review", "fair"]),
        ("Which HR numbers do you share with business leaders every month, and why?",
         ["attrition", "headcount", "absenteeism", "engagement", "hiring"]),
    ],
    "Recruitment / Talent Acquisition": [
        ("You must hire 50 agents in 3 weeks. How do you plan it?", ["sourcing", "pipeline", "referral", "drive", "assessment", "offer"]),
        ("How do you screen 200 applications for 5 openings fairly and quickly?", ["criteria", "shortlist", "fair", "skills", "time"]),
        ("A candidate accepts the offer but does not join. How do you reduce such drop-outs?",
         ["engage", "follow up", "backup", "offer", "notice"]),
        ("How do you judge whether a hiring source is working?", ["conversion", "quality", "cost", "time to hire", "data"]),
        ("How do you write a job post that attracts the right people?", ["clear", "skills", "salary", "shift", "responsibilities"]),
    ],
    "Payroll": [
        ("Walk us through a monthly payroll cycle from attendance to salary credit.",
         ["attendance", "inputs", "deductions", "validation", "approval", "bank file"]),
        ("How are PF, ESI and professional tax deducted and paid, and what are the due dates you track?",
         ["pf", "esi", "professional tax", "due date", "challan", "return"]),
        ("An employee says their salary is short this month. What do you check?",
         ["payslip", "attendance", "lop", "deduction", "arrears"]),
        ("How do you calculate TDS on salary and handle investment declarations?",
         ["tds", "regime", "declaration", "proof", "form 16"]),
        ("How do you process a full and final settlement?", ["notice", "leave encashment", "gratuity", "recovery", "clearance"]),
    ],
    "Admin & Facilities": [
        ("Plan the setup of a new 100-seat office floor.", ["layout", "vendors", "it", "safety", "budget", "timeline"]),
        ("How do you manage cab transport for night-shift employees safely?",
         ["routing", "guard", "female", "tracking", "vendor", "escalation"]),
        ("How do you control the monthly admin budget?", ["budget", "vendor", "negotiate", "track", "approval"]),
        ("A fire drill shows people took too long to evacuate. What do you do?", ["drill", "training", "marshals", "signage", "review"]),
        ("How do you choose and review a housekeeping or security vendor?", ["sla", "quotation", "audit", "feedback", "contract"]),
    ],
    "Finance & Accounts": [
        ("Walk us through how you reconcile a bank statement with the books.", ["entries", "match", "difference", "pending", "adjust"]),
        ("An invoice amount does not match the purchase order. What do you do?", ["check", "vendor", "approval", "hold", "document"]),
        ("How do you make sure GST is charged and recorded correctly?", ["gst", "rate", "invoice", "input credit", "return"]),
        ("How do you meet a month-end closing deadline?", ["checklist", "plan", "reconcile", "deadline", "accruals"]),
        ("Which accounting software and Excel functions do you use most?", ["tally", "sap", "excel", "vlookup", "pivot"]),
    ],
    "Legal": [
        ("A business team needs a vendor contract signed today. How do you review it quickly but safely?",
         ["indemnity", "liability", "termination", "payment", "confidentiality", "risk"]),
        ("What are the key clauses you check in a services agreement?",
         ["scope", "liability", "indemnity", "termination", "jurisdiction", "data"]),
        ("How do you explain a legal risk to a non-lawyer manager?", ["simple", "risk", "options", "impact", "recommend"]),
        ("How do you handle a legal notice received by the company?", ["timeline", "facts", "reply", "counsel", "record"]),
        ("What does the company need to do to handle personal data lawfully in India?",
         ["consent", "dpdp", "purpose", "security", "breach", "deletion"]),
    ],
    "Risk & Compliance": [
        ("How do you identify and rate operational risks in a process?", ["process map", "likelihood", "impact", "controls", "register"]),
        ("A control failed and a customer lost money. What are your steps?", ["contain", "root cause", "report", "fix", "control"]),
        ("How do you prepare a team for an external audit?", ["evidence", "checklist", "samples", "walkthrough", "gaps"]),
        ("How would you detect fraud in refunds or payments?", ["pattern", "threshold", "maker checker", "alerts", "review"]),
        ("How do you make compliance practical for busy frontline teams?", ["simple", "training", "checklist", "automate", "examples"]),
    ],
    "Data Analytics": [
        ("A manager asks why productivity dropped last month. How do you find the answer with data?",
         ["data", "trend", "segment", "root cause", "dashboard"]),
        ("Which Excel or SQL techniques do you use most? Give an example.", ["pivot", "vlookup", "xlookup", "sql", "join", "group by"]),
        ("How do you make sure your report numbers are correct?", ["validate", "source", "reconcile", "check", "sample"]),
        ("Design a daily dashboard for an operations head. What goes on it?",
         ["kpi", "volume", "sla", "quality", "trend", "simple"]),
        ("Explain a finding to someone who does not like numbers.", ["story", "simple", "chart", "impact", "recommendation"]),
    ],
    "WFM (Workforce Management)": [
        ("How do you forecast call or transaction volume for next month?",
         ["history", "trend", "seasonality", "events", "forecast accuracy"]),
        ("How do you build schedules that meet service level with the fewest agents?",
         ["erlang", "intervals", "shrinkage", "occupancy", "shifts"]),
        ("Real-time: the queue is spiking and service level is falling. What do you do in the next 15 minutes?",
         ["real time", "breaks", "overtime", "skills", "communicate", "adherence"]),
        ("What is shrinkage and how do you plan for it?", ["shrinkage", "leave", "training", "breaks", "planned", "unplanned"]),
        ("How do you measure and improve schedule adherence?", ["adherence", "conformance", "report", "coaching", "team lead"]),
    ],
    "Quality": [
        ("How do you build a quality audit form for a new process?", ["parameters", "weightage", "critical", "calibration", "sop"]),
        ("Quality scores are good but customer complaints are rising. What do you do?",
         ["calibration", "voc", "root cause", "sample", "parameters"]),
        ("How do you give feedback to an agent who keeps making the same error?", ["specific", "example", "coaching", "action", "follow up"]),
        ("How do you run a calibration session between QA and operations?", ["sample", "score", "discuss", "align", "variance"]),
        ("Tell us about a process improvement you led. What changed?", ["root cause", "fishbone", "pareto", "action", "result"]),
    ],
    "Training": [
        ("Plan a two-week new-hire training for a process.", ["curriculum", "sop", "system", "practice", "assessment", "nesting"]),
        ("How do you keep a classroom of freshers engaged?", ["activity", "role play", "examples", "questions", "breaks"]),
        ("How do you measure whether training worked?", ["assessment", "certification", "nesting", "quality", "productivity"]),
        ("A batch is failing the final assessment. What do you do?", ["analyse", "gaps", "refresher", "one to one", "feedback"]),
        ("How do you train people on a process change quickly?", ["update", "huddle", "quiz", "job aid", "refresher"]),
    ],
    "Project Management": [
        ("How do you plan a new project or a process transition?", ["scope", "plan", "milestones", "raci", "risks", "stakeholders"]),
        ("The project is two weeks behind. What do you do?", ["critical path", "re-plan", "resources", "escalate", "communicate"]),
        ("How do you manage a stakeholder who keeps changing requirements?", ["change request", "impact", "sign off", "priority"]),
        ("Which status report do you send weekly, and what is on it?", ["rag", "milestones", "risks", "issues", "next steps"]),
        ("Tell us about a project that went wrong and what you learnt.", ["issue", "learn", "lessons", "improve"]),
    ],
    "IT Support": [
        ("A user says 'the system is slow'. How do you find the cause?", ["questions", "logs", "network", "reproduce", "check"]),
        ("How do you make sure a fix does not break something else?", ["test", "review", "backup", "staging", "rollback"]),
        ("What do you do when you are stuck on a problem for more than an hour?", ["search", "document", "ask", "team"]),
        ("How do you keep passwords and customer data safe in your work?", ["access", "encrypt", "password", "privacy", "least"]),
        ("How do you prioritise many tickets at once?", ["priority", "impact", "sla", "communicate", "queue"]),
    ],
    "Marketing": [
        ("How would you get the first 1,000 users for a new website?", ["audience", "content", "social", "seo", "ads", "measure"]),
        ("Which numbers tell you a campaign worked?", ["reach", "clicks", "conversion", "cost", "roi"]),
        ("Write a one-line message for a product you like, and explain why it works.", ["benefit", "audience", "clear", "action"]),
        ("How do you plan a month of social media content?", ["calendar", "themes", "audience", "format", "schedule"]),
        ("Tell us about a campaign that did not work and what you changed.", ["learn", "test", "change", "result"]),
    ],
}

CORE_QUESTIONS = {
    "Travel & Tourism": [
        ("A traveller missed a non-refundable flight and calls you upset. Walk us through what you do, step by step.",
         ["calm", "fare rule", "options", "reissue", "refund", "taxes", "confirm"]),
        ("What is the difference between a refund, a reissue and a revalidation of an air ticket?",
         ["refund", "reissue", "revalidation", "fare", "date", "penalty"]),
        ("Your queue has 40 schedule-change records before the morning shift. How do you prioritise them?",
         ["departure", "urgent", "priority", "date", "time", "customer"]),
        ("A booking is close to its ticketing time limit and the customer has not confirmed. What do you do?",
         ["time limit", "reminder", "cancel", "fare", "confirm"]),
        ("How do you check fare rules before telling a customer whether a change is allowed?",
         ["fare rules", "penalty", "change", "validity", "explain"]),
    ],
    "BPO / BPM / KPO": [
        ("How do you keep your average handling time low without hurting quality?", ["aht", "quality", "process", "notes", "shortcuts"]),
        ("What is an SLA and what do you do when your queue is at risk of missing it?", ["sla", "priority", "escalate", "backlog", "team lead"]),
        ("A process document is unclear on a case you are handling. What do you do?", ["sop", "ask", "escalate", "document", "consistent"]),
        ("How do you stay accurate in a repetitive back-office task?", ["checklist", "focus", "double check", "breaks", "quality"]),
        ("Can you work night or rotational shifts? How do you manage it?", ["yes", "sleep", "routine", "health"]),
    ],
    "Banking & Financial Services": [
        ("Walk us through the KYC checks for a new customer.", ["identity", "address", "documents", "verification", "risk"]),
        ("A customer disputes a card transaction. What happens next?", ["dispute", "chargeback", "evidence", "timeline", "block"]),
        ("How do you spot a suspicious transaction?", ["pattern", "amount", "location", "alert", "report"]),
        ("How do you process a loan application accurately and on time?", ["documents", "eligibility", "verification", "credit", "tat"]),
        ("Why is confidentiality so important in banking operations?", ["privacy", "trust", "regulation", "data", "fraud"]),
    ],
    "IT & Software": [
        ("Explain a project you built or supported to a non-technical person.", ["problem", "users", "built", "result", "simple"]),
        ("How do you make sure your code does not break something else?", ["test", "review", "ci", "staging", "rollback"]),
        ("How do you estimate how long a task will take?", ["break down", "unknowns", "buffer", "past", "communicate"]),
        ("How do you handle a production bug reported at night?", ["severity", "logs", "fix", "rollback", "postmortem"]),
        ("Which languages and tools are you strongest in, and how did you learn them?", ["python", "java", "sql", "project", "learn"]),
    ],
}
GENERIC_CORE_QUESTIONS = [
    ("Describe the main steps of your current or last job, from start to finish of a typical task.",
     ["steps", "check", "system", "customer", "complete"]),
    ("How do you make sure your work is accurate and on time?", ["checklist", "plan", "priority", "check", "deadline"]),
    ("Tell us about a problem you solved at work. What did you do and what was the result?", ["problem", "steps", "result", "learn"]),
    ("How do you handle a sudden increase in workload?", ["priority", "communicate", "plan", "help", "overtime"]),
    ("Which tools or systems do you use daily, and how well do you know them?", ["excel", "system", "software", "tools", "daily"]),
]

LEADERSHIP_QUESTIONS = [
    ("Your team missed its target two months in a row. What do you do in the next 30 days?",
     ["data", "root cause", "coaching", "plan", "review", "huddle"]),
    ("A top performer tells you they want to resign. What do you do this week?", ["listen", "reason", "growth", "retain", "succession"]),
    ("How do you give difficult feedback to a team member?", ["private", "specific", "example", "support", "follow up"]),
    ("How do you build a roster or plan when two people call in sick?", ["priority", "cover", "overtime", "communicate", "backup"]),
    ("How do you handle an angry client escalation as a leader?", ["listen", "own", "action plan", "timeline", "follow up"]),
]

INDUSTRY_QUESTIONS = [
    "In your own words, how does a company in {industry} earn money, and what matters most to its customers?",
    "What is one big change or trend in {industry} right now, and how could it affect a role like yours?",
    "What would you do in your first month to learn how a new {industry} company works?",
]
INDUSTRY_KEYWORDS = ["customer", "revenue", "service", "cost", "quality", "technology", "learn", "process"]

GENERAL_QUESTIONS = [
    ("Introduce yourself: your current or last role, your experience and what you are looking for next.",
     ["experience", "role", "years", "looking", "skills"]),
]

# ---------------------------------------------------------------- paid career services (optional; prices editable in Admin)
SERVICES = [
    ("mock_interview", "1:1 mock interview with an expert", 799,
     "45-minute video call with an experienced professional from your function. Real questions, honest feedback, "
     "and a written improvement plan."),
    ("interview_coaching", "Interview coaching pack (3 sessions)", 1999,
     "Three 45-minute sessions over two weeks: answer structure, your examples, confidence, and a final mock interview."),
    ("cv_review", "Expert CV review", 499,
     "Line-by-line comments on your CV and a keyword list for your job areas, within 48 hours."),
    ("cv_rewrite", "ATS-ready CV rewrite", 999,
     "We rewrite your CV in a clean, ATS-friendly format focused on your job areas, with one round of changes."),
    ("career_consult", "Career consultation", 1499,
     "60 minutes on choosing the right job areas, level and salary, and a 30-day job search plan."),
]

SKILL_WORDS = ["amadeus", "sabre", "galileo", "gds", "ticketing", "refund", "reissue", "fares", "pnr", "customer service",
               "voice", "chat", "email support", "crm", "salesforce", "zendesk", "excel", "advanced excel", "vlookup",
               "xlookup", "pivot", "power bi", "tableau", "sql", "python", "java", "javascript", "react", "aws", "azure",
               "tally", "sap", "gst", "tds", "pf", "esi", "payroll", "accounts payable", "accounts receivable",
               "reconciliation", "recruitment", "onboarding", "hrbp", "employee relations", "communication",
               "team management", "leadership", "quality", "calibration", "sla", "aht", "wfm", "forecasting",
               "scheduling", "real time", "erlang", "process improvement", "six sigma", "lean", "training",
               "project management", "pmp", "agile", "risk", "compliance", "audit", "kyc", "contracts", "litigation",
               "sales", "lead generation", "negotiation", "english", "hindi"]
