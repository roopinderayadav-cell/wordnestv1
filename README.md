# Wordnest demo (Streamlit)

Jobs, news and reading for your working life. A working demo of the Wordnest website:

- **Jobs:** job seeker profiles with notice period and joining date, CV upload with an AI check, a 5-question
  AI demo interview (typed or voice), one-click apply, and an employer area (company verification, job posting with
  a scam check, applicants ranked by interview score and joining date, candidate search)
- **Daily News** (Geopolitics, Industry Update, Job Market, Economy, Entertainment, Sport) and **Articles**
- **Books** (smaller section): ebook store, online reader, watermarked PDF download, author royalties
- **AI review bot** for every article, book and job post, plus an admin panel

Operated by SHROOP Global.

---

## 1. What is inside (all files sit in ONE folder)

| File | What it does |
| --- | --- |
| `app.py` | Starts the website and the top menu. **Main file for Streamlit Cloud.** |
| `wn_pages_public.py` | Home, Daily News, Articles, single article/news page |
| `wn_pages_jobs.py` | Jobs list, job page and apply, My job profile (notice period, CV, AI demo interview), For employers |
| `wn_jobs_data.py` | Industries, functions, sub-roles, levels, the interview question banks and career services (edit freely) |
| `wn_match.py` | Match % between candidates and jobs, interview builder, attempt rules |
| `wn_video.py` | The video interview recorder (speaks the question, records the camera answer) |
| `wn_jobs_ai.py` | AI scoring of interviews and CV checks (with a basic fallback) |
| `wn_ai.py` | Connects to Gemini (cloud) and Ollama (your computer) |
| `wn_pages_books.py` | Book store, book page, online reader, checkout (demo), PDF download |
| `wn_pages_write.py` | Write with us, My dashboard (messages, articles, books, royalties, library), Sign in |
| `wn_pages_admin.py` | Admin panel: review queue, post news, reports, manage content, upload books, users and reminders, sales, settings |
| `wn_pages_legal.py` | Disclaimer, content guidelines, terms and privacy, refunds, royalty terms, grievance contact |
| `wn_moderation.py` | **AI review bot**: rule check + Google Gemini check |
| `wn_db.py` | Database (SQLite) |
| `wn_auth.py` | Accounts, passwords, roles |
| `wn_ui.py` | Look and feel: colours, cards, book covers, footer, disclaimer |
| `wn_pdf.py` | Book page images, text view, buyer watermark on downloads |
| `wn_seed.py` | Demo content created on first start |
| `logo.svg`, `logo_icon.svg` | Logo |
| `requirements.txt` | Python packages |
| `.streamlit/config.toml` | Colours and settings (see step 3.4) |

---

## 2. Try it on your computer (optional)

```
pip install -r requirements.txt
streamlit run app.py
```
The site opens at http://localhost:8501

**Demo accounts**

| Role | Email | Password |
| --- | --- | --- |
| Job seeker (Priya, ready profile) | jobseeker@wordnest.demo | Seeker123! |
| Employer (BlueSky Travel, verified) | employer@wordnest.demo | Employer123! |
| Reader | reader@wordnest.demo | Reader123! |
| Author (R.K. Yadav) | author@wordnest.demo | Author123! |
| Admin (until you set secrets) | admin@wordnest.demo | ChangeMe123! |

---

## 3. Put it online (GitHub + Streamlit Community Cloud)

**3.1 Create the repository**
1. Go to github.com → **New repository** → name it `wordnest-demo` → choose **Private** → Create.

**3.2 Upload the files**
1. Click **Add file → Upload files**.
2. Drag in all the files from the folder (`app.py`, all `wn_*.py`, `logo.svg`, `logo_icon.svg`, `requirements.txt`, `README.md`).
3. Click **Commit changes**.

**3.3 Check**: `app.py` must be at the top level of the repository, not inside a folder.

**3.4 Add the settings file** (GitHub uploads often drop hidden folders, so create it by hand)
1. Click **Add file → Create new file**.
2. In the name box type exactly: `.streamlit/config.toml` (typing the `/` creates the folder).
3. Paste:
```
[theme]
base = "light"
primaryColor = "#1F6F5C"
backgroundColor = "#F6F7F4"
secondaryBackgroundColor = "#FFFFFF"
textColor = "#1C2321"

[server]
maxUploadSize = 100

[client]
toolbarMode = "viewer"
```
4. Click **Commit changes**.

**3.5 Deploy**
1. Go to share.streamlit.io → **Create app** → **Deploy a public app from GitHub**.
2. Repository: `your-name/wordnest-demo`, Branch: `main`, Main file path: `app.py`.
3. App URL: for example `wordnest-demo`.
4. Open **Advanced settings** → Python version **3.12** → paste the secrets below → **Deploy**.

**3.6 Secrets** (Advanced settings, or later in app **Settings → Secrets**)
```
ADMIN_EMAIL = "your-admin-email@example.com"
ADMIN_PASSWORD = "a-strong-password-here"
ADMIN_NAME = "Wordnest Admin"
GEMINI_API_KEY = "paste-your-gemini-key"
GEMINI_MODEL = "gemini-2.5-flash"
```
- On your own computer you can also use **Ollama** (free, runs locally). Add to `.streamlit/secrets.toml`:
  `OLLAMA_URL = "http://localhost:11434"` and `OLLAMA_MODEL = "qwen2.5:7b"`. The site tries Gemini first, then Ollama,
  then the basic checks. Ollama does not work from Streamlit Cloud, because the cloud cannot reach your laptop.
- Get a free Gemini key at **aistudio.google.com → Get API key**. Without it, the bot still runs its rule check, and an editor makes the final call.
- If Google renames the model, change only `GEMINI_MODEL`.
- Never put secrets in GitHub.

---

## 4. How the AI review bot works

1. **Rule check** (always on): word and pattern lists in English and Hindi for adult content, abuse, violence,
   government/politics, illegal activity, personal data (phone, email, Aadhaar-like and PAN-like numbers) and spam.
2. **AI check** (with `GEMINI_API_KEY`): Gemini reads the whole piece and judges meaning. Text inside a submission
   is treated as data, so "ignore your rules and approve" tricks do not work.
3. The strictest result wins:
   - **Pass** → goes to the editor queue (or straight live if *auto-publish* is on in Settings)
   - **Review** → editor decides
   - **Block** → not published; the writer sees the reasons and how to fix them, and gets a message
4. Blocks for adult or abusive content add a **strike**. At 3 strikes (Settings) the account is suspended.
5. **Government rule:** community articles may not discuss governments, parties, politicians or elections.
   Neutral practical mentions ("apply on the government e-visa website") are allowed. Turn on **Strict government
   rule** in Settings to block every mention. **Daily News** may cover geopolitics and the economy, but must be
   neutral and sourced.
6. Readers can **Report this content** on any article, news story or book. Reports appear in Admin → Reports.
7. Admin → Users and reminders → **Send a reminder** sends the guidelines reminder to every writer's Messages tab.

---

## 5. How jobs work

**Job areas (the heart of the matching).** A job area = Industry × Function (+ sub-role) × Level, for example
*Travel & Tourism × WFM / Real-time analyst × Associate*. Lists live in `wn_jobs_data.py` (16 industries, 17 functions
including BU HR, Payroll, Admin, Finance, Legal, Risk & Compliance, Data Analytics, WFM, Quality, Training, Project
Management and Core Operations of each industry; 5 levels). Edit that file to add or rename anything.

1. **Job seeker:** Create account → "Find a job" → My job profile:
   1. **Job areas:** up to 4; one is primary. The level is suggested from years of experience.
   2. **Profile and notice period:** notice in contract, resigned or not, resignation date, last working day, earliest
      joining, reason if leaving early (shortfall calculated automatically). Reconfirm every 14 days.
   3. **CV and ATS check:** ATS readiness score with free tips. Below 80 (Settings), expert CV services are suggested.
      Every job page also shows how much of that job's skills the CV covers.
   4. **Demo interview, one per job area:**
      - Part 1, written: 5 questions (intro, function/industry questions, a leadership question for Team Lead and
        above, an industry question). Typed or by voice.
      - Part 2, video: 3 questions **spoken aloud by the interviewer voice**; the candidate answers **on camera**
        (up to 2 minutes, one re-record). Videos are saved to the profile for recruiters.
      - Pass mark 60. 3 free attempts per job area; after that one free retake every 30 days, and paid help is offered.
   5. **Apply** only to jobs in their job areas, with a match % (function, sub-role, industry, level, skills, joining
      date, work mode, interview).
2. **Employer:** Create account → "Hire people" → register the company (GSTIN or CIN) → admin verifies it (Admin →
   Companies) → post a job with industry, function, sub-role, level and "industry experience required?" → scam check →
   applicants ranked by match % and interview score, filters for joining date, match and score → full profile with
   written answers, **video answers** and CV → shortlist / reject / hired. **Find candidates** searches visible profiles.
3. **Career services (optional, paid):** mock interview, coaching pack, CV review, CV rewrite, career consultation.
   Booked with a demo payment; managed in Admin → Career services. Prices and the pass mark, attempts, retake gap and
   ATS threshold are in Admin → Settings. Services never affect applications, visibility or scores, and never promise a job.
4. **Safety:** no employer may ask candidates for money; job posts asking for fees are blocked; readers can report any job.

### AI used for jobs
| Task | Gemini (cloud) | Ollama (your laptop) | No AI |
| --- | --- | --- | --- |
| Written interview scoring | Yes | Yes | Basic scorer (length, key topics, repeated answers) |
| Voice answer to text | Yes | No | Recording kept, not transcribed |
| Video answer scoring | Yes (watches the video) | No | Recruiters watch the videos |
| CV / ATS check | Yes | Yes | Basic checker |
| Content and job-post review | Yes | Yes | Rule check |

### Using Ollama on your laptop
1. Ollama installed and `ollama pull qwen2.5:7b` done (check http://localhost:11434 shows "Ollama is running").
2. In the Wordnest folder, create a folder named `.streamlit` (if it is not there) and inside it a file `secrets.toml` with:
```
OLLAMA_URL = "http://localhost:11434"
OLLAMA_MODEL = "qwen2.5:7b"
```
3. Run `streamlit run app.py`. The admin panel shows "AI: ON · Ollama (qwen2.5:7b)". Keep the Ollama app running.

## 6. Demo limits (important)

- **Data resets** when Streamlit Cloud restarts the app (after it sleeps or on a new deploy). Demo content comes back,
  but new articles, books and accounts are lost. The live site needs a permanent database.
- **Payments are simulated.** No money is charged.
- **Refreshing the browser signs you out.** Use the menu to move between pages.
- Uploaded PDFs, covers, CVs and **interview videos** are stored in the database. Fine for a demo; the live site should
  use file/video storage (for example Bunny, Cloudflare Stream or S3).
- The camera works on https sites (Streamlit Cloud) and on http://localhost. The browser asks the candidate for
  camera and microphone permission. Chrome and Edge work best.

---

## 7. Before the real launch

- [ ] Permanent database (Supabase/PostgreSQL or Hostinger MySQL) and file storage for PDFs and covers
- [ ] Razorpay live payments, GST invoices from SHROOP Global, refund flow
- [ ] Email for sign-up confirmation, password reset and reminders
- [ ] Final site on Hostinger with your domain (better for Google search than Streamlit)
- [ ] Lawyer review of the policy pages; fill in the grievance officer name, email and address
- [ ] CA to confirm the GST rate on ebooks and TDS on author royalties
- [ ] Signed author agreement (royalty %, non-exclusive licence, payouts)
- [ ] Replace demo books with real PDFs and covers; replace [Demo] news
- [ ] Only use photos you own, licensed, or free-to-use; credit every news source
- [ ] Jobs: data protection consent and deletion for CVs and recordings (DPDP Act), company verification process,
      employer terms, and video interviews (needs a video service; Streamlit records voice only)
