# 🔭 GitHub Tech Trends Pipeline

An end-to-end data engineering project that tracks GitHub developer activity trends using a fully automated batch pipeline — built as the capstone project for the [DataTalksClub Data Engineering Zoomcamp](https://github.com/DataTalksClub/data-engineering-zoomcamp).

## 📊 Dashboard

<img width="986" height="562" alt="image" src="https://github.com/user-attachments/assets/2e7f4d1f-e664-43c5-81b4-e19a58cb21b1" />

[View Live Dashboard →](https://lookerstudio.google.com/reporting/76c9eb76-17e3-457d-9f9c-c210599abaa3)


**The dashboard answers:**
- Which repositories are trending (most starred/forked)?
- What time of day is GitHub most active?
- How have push, star, and fork trends changed over time?
- What is the breakdown of developer activity by event type?

---

## 🌿 Branches

| Branch | Description |
|---|---|
| `main` | Primary pipeline using Kestra + dbt + Python scripts |
| `bruin-migration` | Alternative pipeline using Bruin (single tool replacing Kestra + dbt) |

---

## 🏗️ Architecture

### Main Branch (Kestra + dbt)

```
GitHub Archive (gharchive.org)
        ↓
  Python Ingestion Scripts
  (download hourly .json.gz → parse → Parquet)
        ↓
  GCS Bucket (Data Lake)
  gs://tech-trends-bucket-489801/raw/github/
        ↓
  BigQuery Raw Layer
  raw.github_events
        ↓
  dbt Transformations
  staging → marts
        ↓
  BigQuery Production Layer
  prod.stg_github_events    (incremental table)
  prod.fct_daily_summary    (incremental, partitioned by event_date, clustered by event_type)
  prod.fct_repo_activity    (partitioned by last_seen, clustered by repo_owner)
  prod.fct_hourly_activity  (table)
        ↓
  Looker Studio Dashboard

  Orchestrated by Kestra (daily at 6am UTC)
  Infrastructure provisioned by Terraform
  Backfills via GitHub Actions
```

### Bruin Pipeline (github-pipeline/)

```
GitHub Archive (gharchive.org)
        ↓
  raw.ingest_github        (Bruin Python asset)
        ↓
  raw.load_to_bigquery     (Bruin Python asset — delete+insert idempotent)
        ↓
  prod.stg_github_events   (Bruin bq.sql — merge strategy + 4 quality checks)
        ↓
  prod.fct_daily_summary    (partitioned by event_date, clustered by event_type)
  prod.fct_repo_activity    (partitioned by last_seen, clustered by repo_owner)
  prod.fct_hourly_activity  (Bruin bq.sql assets — run in parallel)
        ↓
  Looker Studio Dashboard

  Everything orchestrated by Bruin (single tool — no Kestra, no dbt)
  Infrastructure provisioned by Terraform
```

---

## 🛠️ Tech Stack

| Layer | Main Branch | Bruin Pipeline |
|---|---|---|
| Cloud | GCP (BigQuery, GCS) | GCP (BigQuery, GCS) |
| Infrastructure as Code | Terraform | Terraform |
| Orchestration | Kestra | Bruin |
| Transformation | dbt Core | Bruin |
| Data Lake | Google Cloud Storage | Google Cloud Storage |
| Data Warehouse | BigQuery | BigQuery |
| Dashboard | Looker Studio | Looker Studio |
| Language | Python 3.12 | Python 3.12 |
| Dependency Management | uv | uv |
| CI/CD | GitHub Actions | GitHub Actions |

---

## 📁 Project Structure

```
Tech-Trends-/
├── ingestion/
│   ├── github_ingest.py        # Downloads GH Archive data → GCS
│   ├── gcs_to_bigquery.py      # Loads GCS Parquet → BigQuery (delete-insert)
│   └── requirements.txt
├── terraform/
│   ├── main.tf                 # GCS bucket + BigQuery datasets
│   ├── variables.tf
│   └── outputs.tf
├── kestra/
│   └── flows/
│       └── github_pipeline.yml # Daily Kestra orchestration flow
├── dbt/
│   ├── models/
│   │   ├── staging/
│   │   │   ├── sources.yml           # Source definitions + quality tests
│   │   │   └── stg_github_events.sql # incremental
│   │   └── marts/
│   │       ├── fct_daily_summary.sql    # incremental + partitioned
│   │       ├── fct_repo_activity.sql    # partitioned + clustered
│   │       └── fct_hourly_activity.sql
│   └── dbt_project.yml
├── github-pipeline/            # Bruin pipeline
│   ├── pipeline.yml
│   └── assets/
│       ├── ingest_github.py
│       ├── load_to_bigquery.py
│       ├── stg_github_events.sql   # merge strategy + quality checks
│       ├── fct_daily_summary.sql   # partitioned + clustered
│       ├── fct_repo_activity.sql   # partitioned + clustered
│       └── fct_hourly_activity.sql
├── .github/
│   └── workflows/
│       └── backfill.yml        # GitHub Actions backfill workflow
├── .bruin.yml                  # Bruin GCP connection config
├── pyproject.toml              # uv dependency management
└── docker-compose.yml          # Runs Kestra locally
```

---

## 🚀 Reproducing This Project

### Prerequisites
- GCP account with a project created
- GitHub Codespaces or Linux environment
- Docker installed

### 1. Clone the repo
```bash
git clone https://github.com/Amar-Ag/Tech-Trends-
cd Tech-Trends-
```

### 2. Set up environment variables
```bash
cp .env.example .env
# Fill in your actual values in .env
```

### 3. Set up GCP credentials
```bash
# Create a service account with Storage Admin + BigQuery Admin roles
# Download the JSON key to keys/service-account.json
mkdir keys
# Place your service-account.json in the keys/ folder
export GOOGLE_APPLICATION_CREDENTIALS="keys/service-account.json"
```

### 4. Provision infrastructure with Terraform
```bash
cd terraform
terraform init
terraform apply
```

This creates:
- GCS bucket: `tech-trends-bucket-{project-id}`
- BigQuery datasets: `raw` and `prod`

### 5. Install dependencies
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
uv sync
```

### 6. Run ingestion manually
```bash
# Ingest a specific date
INGEST_DATE=2025-12-01 uv run python ingestion/github_ingest.py
INGEST_DATE=2025-12-01 uv run python ingestion/gcs_to_bigquery.py

# Default — ingests yesterday automatically
uv run python ingestion/github_ingest.py
uv run python ingestion/gcs_to_bigquery.py
```

### 7. Backfill historical data via GitHub Actions
A GitHub Actions workflow is included for bulk backfills — runs on GitHub's servers so you don't need to keep your system on or have an active session:
1. Edit `.github/workflows/backfill.yml` to set your date list
2. Go to **Actions → Backfill GitHub Archive Data → Run workflow**
3. Close your system and check back when done ✅

### 8. Run dbt transformations

**Normal daily run (incremental — only processes new data):**
```bash
cd dbt
uv run dbt build
```

**After a backfill (full refresh — reprocesses all data):**
```bash
cd dbt
uv run dbt build --full-refresh
```

> ⚠️ Always run `dbt build --full-refresh` after backfilling historical dates.
> The incremental models filter on `max(created_at)` so they will skip
> historical rows unless you force a full rebuild.

### 9. Start Kestra (orchestration)
```bash
docker-compose up -d
# Open http://localhost:8080
# Import kestra/flows/github_pipeline.yml
# Add GCP_SA_KEY_B64 to Kestra UI → Namespace → KV Store
```

### 10. Run with Bruin pipeline
```bash
# Install Bruin
curl -LsSf https://raw.githubusercontent.com/bruin-data/bruin/refs/heads/main/install.sh | sh

cd github-pipeline

# Run full pipeline for a specific date
bruin run --start-date 2025-12-01 --end-date 2025-12-01 .

# Run with full refresh
bruin run --start-date 2025-12-01 --end-date 2025-12-01 . --full-refresh

# View asset lineage
bruin lineage assets/stg_github_events.sql
```

### 11. View dashboard
Connect Looker Studio to BigQuery `prod` dataset and build charts from:
- `fct_daily_summary`
- `fct_hourly_activity`
- `fct_repo_activity`

---

## 📈 Data Source

**GitHub Archive** (gharchive.org) — free hourly dumps of all public GitHub events since 2011. This project ingests 4 event types:

- `WatchEvent` — repository starred
- `ForkEvent` — repository forked
- `PushEvent` — code pushed
- `PullRequestEvent` — PR opened/closed/merged

Data covers **November 2024 → March 2026**, sampled at 2 dates per week frequency (~121 total dates, ~350M events).

---

## 💡 Key Findings

- **PushEvent dominates at 84.6%** of all GitHub activity — developers push code far more than they star or fork
- **GitHub activity dropped ~30% after May 2025** — visible trend from ~3.5M to ~2.5M events per day
- **12PM UTC is consistently the busiest hour** across all 16 months — European afternoon + US morning overlap
- **codecrafters-io/build-your-own-x** was the most starred repo with 34,786 stars — learning resources dominate
- **n8n-io/n8n** had the most forks (9,875) — AI automation tools are being self-hosted heavily
- **deepseek-ai/DeepSeek-V3** at #4 with 22,781 stars — the Chinese AI model that shocked the industry in late 2024
- **langflow-ai/langflow** at #7 — AI workflow and agent tools exploded in popularity throughout 2025
- Data covers **Nov 2024 → Mar 2026** across 121 sampled dates at 2-per-week frequency

---

## 🔧 Potential Improvements

- Add Stack Overflow survey data for salary/language trend analysis
- Implement streaming pipeline with Kafka for real-time event processing
- Deploy Kestra to GCP Cloud Run for production orchestration
- Add partitioning to `raw.github_events` table (currently implemented on mart tables only)
- Add CI/CD pipeline to run dbt tests automatically on every push


