# 🔭 GitHub Tech Trends Pipeline

An end-to-end data engineering project that tracks GitHub developer activity trends using a fully automated batch pipeline — built as the capstone project for the [DataTalksClub Data Engineering Zoomcamp](https://github.com/DataTalksClub/data-engineering-zoomcamp).

## 📊 Dashboard

[View Live Dashboard →](https://lookerstudio.google.com/reporting/76c9eb76-17e3-457d-9f9c-c210599abaa3)

<img width="1666" height="964" alt="image" src="https://github.com/user-attachments/assets/39e2987d-a6a1-4c0d-b770-f2d7933a006d" />


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
  prod.fct_daily_summary
  prod.fct_repo_activity
  prod.fct_hourly_activity
        ↓
  Looker Studio Dashboard

  Orchestrated by Kestra (daily at 6am UTC)
  Infrastructure provisioned by Terraform
```

### Bruin Branch (bruin-migration)

```
GitHub Archive (gharchive.org)
        ↓
  raw.ingest_github        (Bruin Python asset)
        ↓
  raw.load_to_bigquery     (Bruin Python asset)
        ↓
  prod.stg_github_events   (Bruin bq.sql asset + quality checks)
        ↓
  prod.fct_daily_summary
  prod.fct_repo_activity   (Bruin bq.sql assets — run in parallel)
  prod.fct_hourly_activity
        ↓
  Looker Studio Dashboard

  Everything orchestrated by Bruin (single tool)
  Infrastructure provisioned by Terraform
```

---

## 🛠️ Tech Stack

| Layer | Main Branch | Bruin Branch |
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
│   │   │   ├── sources.yml     # Source definitions + quality tests
│   │   │   └── stg_github_events.sql
│   │   └── marts/
│   │       ├── fct_daily_summary.sql
│   │       ├── fct_repo_activity.sql
│   │       └── fct_hourly_activity.sql
│   └── dbt_project.yml
├── github-pipeline/            # Bruin pipeline (bruin-migration branch)
│   ├── pipeline.yml
│   └── assets/
│       ├── ingest_github.py
│       ├── load_to_bigquery.py
│       ├── stg_github_events.sql
│       ├── fct_daily_summary.sql
│       ├── fct_repo_activity.sql
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

# Default (no date set) ingests yesterday automatically
uv run python ingestion/github_ingest.py
uv run python ingestion/gcs_to_bigquery.py
```

### 7. Backfill historical data via GitHub Actions
A GitHub Actions workflow is included for bulk backfills — runs on GitHub's servers so you don't need to keep your laptop on:
1. Go to **Actions → Backfill GitHub Archive Data → Run workflow**
2. Edit `.github/workflows/backfill.yml` to change the date list
3. Trigger and close your laptop — check back when it's done

### 8. Start Kestra (orchestration)
```bash
docker-compose up -d
# Open http://localhost:8080
# Import kestra/flows/github_pipeline.yml
# Add GCP_SA_KEY_B64 to Kestra KV Store
```

### 9. Run dbt transformations
```bash
cd dbt
uv run dbt build   # runs models + quality tests
```

### 10. Run with Bruin (bruin-migration branch)
```bash
git checkout bruin-migration
cd github-pipeline

# Install Bruin
curl -LsSf https://raw.githubusercontent.com/bruin-data/bruin/refs/heads/main/install.sh | sh

# Run full pipeline for a specific date
bruin run --start-date 2025-12-01 --end-date 2025-12-01 .

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

Data covers **November 2024 → March 2026**, ingested at 2 dates per week frequency.

---

## 💡 Key Findings

- **PushEvent dominates at 84.7%** of all GitHub activity
- **12PM UTC is consistently the busiest hour** — aligns with European afternoon + US morning overlap
- **GitHub activity dropped ~30%** after May 2025 compared to early 2025
- **n8n-io/n8n** was among the most starred repos — AI automation tools exploded in 2025
- **Stars spike at 12PM UTC** — when developers browse during lunch

---

## 🔧 Potential Improvements

- Add Stack Overflow survey data for salary/language trend analysis
- Implement streaming pipeline with Kafka for real-time event processing
- Deploy Kestra to GCP Cloud Run for production orchestration
- Add incremental dbt models instead of full refreshes
- Add CI/CD pipeline to automatically run dbt tests on push

