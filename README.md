# 🔭 GitHub Tech Trends Pipeline

An end-to-end data engineering project that tracks GitHub developer activity trends using a fully automated batch pipeline.

## 📊 Dashboard

[View Live Dashboard →](https://lookerstudio.google.com/reporting/76c9eb76-17e3-457d-9f9c-c210599abaa3)

<img width="1666" height="964" alt="image" src="https://github.com/user-attachments/assets/39e2987d-a6a1-4c0d-b770-f2d7933a006d" />


**The dashboard answers:**
- Which repositories are trending (most starred/forked)?
- What time of day is GitHub most active?
- How have push, star, and fork trends changed over time?
- What is the breakdown of developer activity by event type?

---

## 🏗️ Architecture

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

  Everything orchestrated by Kestra (daily at 6am UTC)
  Infrastructure provisioned by Terraform
```

---

## 🛠️ Tech Stack

| Layer | Tool |
|---|---|
| Cloud | GCP (BigQuery, GCS) |
| Infrastructure as Code | Terraform |
| Orchestration | Kestra |
| Data Lake | Google Cloud Storage |
| Data Warehouse | BigQuery |
| Transformations | dbt Core |
| Dashboard | Looker Studio |
| Language | Python 3.12 |
| Dependency Management | uv |

---

## 📁 Project Structure

```
Tech-Trends-/
├── ingestion/
│   ├── github_ingest.py        # Downloads GH Archive data → GCS
│   ├── gcs_to_bigquery.py      # Loads GCS Parquet files → BigQuery
│   └── requirements.txt
├── terraform/
│   ├── main.tf                 # GCS bucket + BigQuery datasets
│   ├── variables.tf
│   └── outputs.tf
├── kestra/
│   └── flows/
│       └── github_pipeline.yml # Daily orchestration flow
├── dbt/
│   ├── models/
│   │   ├── staging/
│   │   │   ├── sources.yml
│   │   │   └── stg_github_events.sql
│   │   └── marts/
│   │       ├── fct_daily_summary.sql
│   │       ├── fct_repo_activity.sql
│   │       └── fct_hourly_activity.sql
│   └── dbt_project.yml
├── pyproject.toml
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
INGEST_DATE=2024-11-01 uv run python ingestion/github_ingest.py
INGEST_DATE=2024-11-01 uv run python ingestion/gcs_to_bigquery.py
```

### 7. Start Kestra (orchestration)
```bash
docker-compose up -d
# Open http://localhost:8080
# Import kestra/flows/github_pipeline.yml
```

### 8. Run dbt transformations
```bash
cd dbt
uv run dbt run
```

### 9. View dashboard
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

Data covers **November 2024 → present**, ingested daily.

---

## 💡 Key Findings

- **PushEvent dominates at 86%** of all GitHub activity
- **12PM UTC is the busiest hour** — aligns with European afternoon + US morning overlap
- **microsoft/markitdown** was the most starred repo in the dataset
- Stars spike at **3PM UTC** — when developers browse after finishing morning work

---

## 🔧 Potential Improvements

- Add Stack Overflow survey data for salary/language trend analysis
- Implement streaming pipeline with Kafka for real-time event processing
- Add dbt tests for data quality checks
- Deploy Kestra to GCP Cloud Run for production orchestration
