"""Wordnest - policy pages. These are starting drafts: have them reviewed by a lawyer before launch."""
import streamlit as st

import wn_db

POLICIES = {
    "disclaimer": ("Disclaimer", """
Wordnest is a platform where members of the public can publish articles and ebooks. **Views, opinions and claims in
community articles and books belong only to their authors.** Wordnest and its operator, SHROOP Global, do not endorse,
support or take responsibility for content written by users, and are not liable for any loss arising from it.

We do not allow sexual or adult content, abusive or hateful language, violence, illegal activity, other people's
personal data, or political content about governments, parties or politicians. Every submission is checked by an
automated AI review bot and an editor before it goes live. Automated checks can make mistakes, so we also act on
reports from readers: use **Report this content** on any article or book.

**Daily News** stories are short summaries written by Wordnest editors from the sources named on each story. They are
for general information only and are not professional, financial, legal or medical advice. Please check the original
source before acting on any information.

Writers are solely responsible for making sure their work is original and lawful. Wordnest may edit for formatting,
refuse, or remove any content at any time without notice.
"""),
    "guidelines": ("Content guidelines", """
**Write about real life: travel, careers, food, family, technology, stories and ideas.** Please keep it original,
respectful and safe.

**Not allowed (blocked by our AI review bot):**
- Sexual, pornographic or adult content of any kind
- Abuse, slurs or hate against any person, religion, caste, community, gender or nationality
- Content about governments, political parties, politicians or elections, including opinions, praise or criticism
  (neutral practical mentions, such as "apply on the official government e-visa website", are fine)
- Threats, violence, terrorism, self-harm, drugs, gambling, scams or other illegal activity
- Other people's phone numbers, emails, ID numbers or addresses
- Text, photos or chapters copied from other writers, websites or books

**How review works**
1. When you submit, our AI review bot reads your work in seconds and either passes it, asks for an editor's check, or
   blocks it with reasons and suggestions.
2. An editor approves everything before it goes live.
3. Blocked submissions for adult or abusive content count as a **strike**. After 3 strikes, the account is suspended.

**Good writing tips:** a clear title, a one-line summary, short paragraphs, and your own photos.
"""),
    "terms": ("Terms of use and privacy", """
**Terms of use (draft).** By using Wordnest you agree to follow the Content guidelines, to publish only work you own,
and that you are responsible for what you publish. You keep the copyright in your work and give Wordnest a
non-exclusive licence to display, promote and sell it on Wordnest. We may suspend accounts that break the guidelines.
Ebooks are licensed for personal reading only; sharing or reselling them is not allowed.

**Privacy (draft).** We collect your name, email, pen name, the content you submit, purchases and reading progress to run
the service. Payment details are handled by our payment partner, not stored by Wordnest. We do not sell your data.
You can ask us to correct or delete your account at any time through the grievance contact. Submissions are processed
by an AI service (Google Gemini) for safety review. We follow India's Digital Personal Data Protection Act, 2023.
"""),
    "refunds": ("Refunds", """
Ebooks are digital and are delivered instantly, so purchases are generally not refundable. We will refund in full if:
- you were charged twice for the same book,
- the file is damaged or cannot be opened and we cannot fix it within 7 days, or
- the book is removed from Wordnest within 7 days of your purchase.

Write to the grievance contact with your payment reference within 30 days of purchase.
"""),
    "royalty": ("Royalty terms for authors", None),
    "grievance": ("Grievance and contact", """
**Grievance Officer** (as required under India's IT Rules for platforms that host user content)

- Name: [Grievance Officer name]
- Email: [grievance email address]
- Address: SHROOP Global, [address], Uttar Pradesh, India

We acknowledge complaints within 24 hours and resolve them as quickly as possible within the time limits set by law.
To report content, use **Report this content** on the page, or email the officer with the link and the reason.

**General contact:** [contact email]

Wordnest is operated by SHROOP Global. GSTIN: [GSTIN]
"""),
}


def _royalty_text():
    roy = int(wn_db.get_setting_num("royalty_pct"))
    gst = wn_db.get_setting_num("gst_pct")
    fee = wn_db.get_setting_num("gateway_fee_pct")
    ex = wn_db.money_split(299)
    return f"""
**You keep {roy}% of the net revenue from every sale of your ebook.**

- **Net revenue** = the price paid, minus GST included in the price (currently {gst:g}%) and the payment gateway
  fee (about {fee:g}%).
- **Example:** a ₹299 ebook → GST ₹{ex['gst']:.2f}, gateway fee ₹{ex['fee']:.2f}, net ₹{ex['net']:.2f} →
  **your royalty ₹{ex['author']:.2f}**, Wordnest ₹{ex['platform']:.2f}.
- **You keep the copyright.** The licence to Wordnest is non-exclusive: you can also sell your book elsewhere.
- **You set the price** (or make it free). Free books still build your readership.
- **Payment:** monthly, by bank transfer, once your balance is ₹500 or more, with a statement of every sale.
  Tax (TDS) is deducted where the law requires; please add your PAN in your profile before your first payout.
- **Leaving:** you can remove your book at any time. Readers who already bought it keep access.

Wordnest is operated by SHROOP Global. These terms are a draft; the signed author agreement is the final document.
"""


def page_policies():
    keys = list(POLICIES)
    start = st.query_params.get("p", "disclaimer")
    pick = st.segmented_control("Policy", keys, default=start if start in keys else "disclaimer", required=True,
                                format_func=lambda k: POLICIES[k][0], label_visibility="collapsed")
    title, body = POLICIES[pick]
    st.markdown(f'<h1 class="wn-serif" style="font-size:42px">{title}</h1>', unsafe_allow_html=True)
    st.markdown(_royalty_text() if pick == "royalty" else body)
    st.caption("Last updated: October 2026 · Draft for the demo; to be reviewed by a lawyer before launch.")
