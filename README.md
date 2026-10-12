# Instantly Outbound Analytics

An automated pipeline that pulls cold-email campaign data out of Instantly.ai, models it in BigQuery with Dataform, and reports on it in Looker Studio. Instantly has no native Looker Studio connector, so this project builds one end to end.

**[View the live dashboard →](LINK_HERE)**

---

## Why I built this

Instantly's built-in reporting shows campaign totals, but it can't answer the questions that drive decisions:

- Which email in the sequence actually earns replies?
- Are "replies" real interest, or auto-replies and unsubscribes?
- Is the lead pipeline still being fed, or are we just following up on old leads?
- Does targeting by job title make a difference?

This pipeline answers those questions automatically every day.

---

## Architecture

```
                 ┌─────────────────────────── daily batch (GitHub Actions) ───────────────────────────┐
Instantly API v2 ─► Python extract scripts ─► BigQuery: instantly_raw ─► Dataform ─► Looker Studio
                                                                       (triggered after the load)
                                                     ▲
Instantly webhooks ─► Cloud Run function ────────────┘  (real-time events → webhook_events)
```

| Layer | Tool | What it does |
|---|---|---|
| Extract | Python (`requests`, `pandas`) | Pulls daily analytics, step analytics, leads, and replies from the Instantly API v2, with pagination and rate-limit handling |
| Orchestrate | GitHub Actions | Runs `run_pipeline.py` daily, then starts the Dataform workflow and waits for it to finish; credentials are stored as GitHub Secrets |
| Load | `google-cloud-bigquery` | Loads CSVs into `instantly_raw` (full refresh, `WRITE_TRUNCATE`) |
| Real-time | Cloud Run function | Receives Instantly webhooks, checks a shared-secret header, and stores raw JSON in a partitioned table |
| Transform | Dataform (SQLX) | Staging → marts layers, with data-quality assertions |
| Report | Looker Studio | Three-page dashboard: Overview, Sequence, Replies & Leads |

---

## Data model

**`instantly_raw`**: source data as received (`daily_analytics`, `steps_analytics`, `leads`, `replies`, `webhook_events`)

**`instantly_staging`**: cleaned, typed, one row per entity
- `stg_daily`: a date spine, so days with no sends show as 0 instead of being missing
- `stg_steps`: step/variant performance (step 0 → "Email 1", variant 0 → "A")
- `stg_leads`: lead status flags with **no PII** (emails and names stay in raw)
- `stg_replies`: rule-based reply classification (see below)

**`instantly_marts`**: tables the dashboard reads
- `mart_weekly_funnel`: weekly sends, new leads, replies, and running totals (completed weeks only)
- `mart_step_performance`: emails sent, replies, and auto-replies by email step and variant
- `mart_reply_categories`: reply counts by category and step
- `mart_lead_segments`: leads and reply rate by job-title group

**Assertions** (`instantly_assertions`): uniqueness and not-null checks on primary keys and required fields. If an assertion fails, the run fails instead of quietly publishing bad numbers.

---

## Design decisions worth calling out

**Reply classification is rule-based.** Instantly's `is_auto_reply` field came back empty for every reply, so `stg_replies` classifies each reply with regex on the subject and body (auto-reply, unsubscribe request) and falls back to Instantly's `i_status` for not-interested, wrong-person, and interested. Anything unmatched lands in "Needs review" so it gets noticed instead of hidden.

**Rates are ratios of sums, never averages of rates.** Every reply rate in Looker is a calculated field (`SUM(replies) / SUM(denominator)`), so it stays correct when the data is filtered or totaled.

**Two reply rates, clearly labeled.** *Per lead* (replies ÷ leads contacted) measures campaign reach; *per email* (replies ÷ emails sent) measures how efficient each send is. They answer different questions, and both are labeled with their denominator.

**Each step triggers the next.** GitHub's scheduled runs can start hours late, so a fixed time gap between the load and Dataform meant Dataform sometimes transformed the previous day's data. GitHub Actions now starts the Dataform run itself once the load finishes, and the job fails if Dataform fails.

**Partial weeks are excluded.** The current week is filtered out of the weekly funnel, so the trend line doesn't fake a drop-off every Monday.

**PII stays in the raw layer.** Staging and mart tables carry IDs and categories, not names or email addresses.

---

## Findings (as of October 2026)

| Metric | Value |
|---|---|
| Emails sent | 4,583 |
| Leads contacted | 1,078 |
| Reply rate (per lead) | 0.93% |
| Reply rate (per email) | 0.22% |
| Positive replies | **0** |

1. **The pipeline stopped being fed.** No new leads have been added since the end of August, so every email since then has been a follow-up and volume is declining week over week. **Action:** add new leads before optimizing anything else.
2. **Follow-ups matter, but not all of them.** Emails 2–5 produced 6 of the 10 replies, so a one-email campaign would have missed most of the conversations. Email 5 has produced **zero** real replies across 777 sends. **Action:** cut the sequence to 4 emails, or rewrite email 5.
3. **Every real reply was negative.** All 9 human replies were "not interested" or unsubscribe requests. The problem is the offer or the targeting, not deliverability. **Action:** test a new angle before scaling volume.
4. **Job title didn't change the outcome.** Doctors/chiropractors (1.50%) and owners/founders (1.41%) reply at nearly the same rate, so title targeting isn't the lever here.
5. **List quality issues show up in the data.** One mis-targeted lead (a talent agency, not a clinic) produced 4 of the auto-replies on its own.
6. **The A/B test is too small to call.** Variants B and C of email 1 have 90 sends each, which isn't enough to separate signal from noise.

---

## Data notes and reconciliation

- **Reply counts:** Instantly reports 10 replies and 12 auto-replies, while this pipeline classifies 9 real replies and 13 auto-replies. The one-reply difference is definitional and most likely comes from a reply that Instantly counts as human but that matches this pipeline's auto-reply rules.
- **"Leads who replied"** on the Replies & Leads page counts any reply, including auto-replies, so it's useful for comparing segments but isn't a measure of interest.
- **Leads:** 1,078 leads are contacted in the analytics endpoint vs. 1,079 lead records, most likely because one lead was added but never sent to.

---

## Running it

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# create a .env file with:
#   INSTANTLY_API_KEY=...
#   GCP_PROJECT_ID=...
#   GOOGLE_APPLICATION_CREDENTIALS=gcp-key.json
python run_pipeline.py
```

The Instantly API key only needs **read-only** scope. The service account needs BigQuery Data Editor and Job User.

### Maintenance rule (Dataform)

The Dataform run started by GitHub Actions uses the **production release config**, which compiles from the `main` branch. After any SQLX change:

1. Commit → **Push to default branch**
2. Release configurations → production → **New compilation**

If you skip step 2, the schedule keeps running the old code.

---

## Roadmap

- [ ] `stg_webhook_events`: model real-time events (sends, opens, bounces) and exclude test payloads
- [ ] Move secrets to Google Secret Manager
- [ ] Alert (Slack or email) when a reply is classified as Interested

---

## Repo structure

```
├── daily_analytics.py       # GET /campaigns/analytics/daily
├── steps_analytics.py       # GET /campaigns/analytics/steps
├── leads.py                 # POST /leads/list (paginated)
├── replies.py               # GET /emails (received, rate-limited)
├── load_to_bigquery.py      # CSV → instantly_raw
├── run_pipeline.py          # runs all of the above in order
├── trigger_dataform.py      # starts the Dataform run after the load and waits for the result
├── webhook/main.py          # Cloud Run webhook receiver
└── .github/workflows/daily_pipeline.yml
```

The Dataform SQLX models (sources, staging, marts, and assertions) live in a Google Cloud Dataform repository.
