import os
import base64
import json
from dotenv import load_dotenv
from google.cloud import bigquery
from google.oauth2 import service_account

load_dotenv()

# ── Configuration ────────────────────────────────────────────────
PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "tech-trends-489801")
DATASET    = os.environ.get("BQ_DATASET", "raw")
TABLE      = os.environ.get("BQ_TABLE", "github_events")
GCS_BUCKET = os.environ.get("GCS_BUCKET", "tech-trends-bucket-489801")


# ── Credentials ──────────────────────────────────────────────────
def get_credentials():
    key_b64 = os.environ.get("GCP_SA_KEY_B64")
    if key_b64:
        key_b64 = key_b64.strip()
        key_bytes = base64.b64decode(key_b64 + "==")
        info = json.loads(key_bytes.decode("utf-8", errors="ignore"))
        return service_account.Credentials.from_service_account_info(info)
    return None


# ── Load Function ────────────────────────────────────────────────
def load_gcs_to_bigquery(date_str: str) -> None:
    """
    Load a single day's parquet files from GCS into BigQuery.
    date_str format: "2024-11-01"
    """
    credentials = get_credentials()
    client = bigquery.Client(project=PROJECT_ID, credentials=credentials)

    year  = date_str[:4]
    month = date_str[5:7]
    day   = date_str[8:10]

    gcs_uri   = f"gs://{GCS_BUCKET}/raw/github/year={year}/month={month}/day={day}/*.parquet"
    table_ref = f"{PROJECT_ID}.{DATASET}.{TABLE}"

    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.PARQUET,
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
    )

    job = client.load_table_from_uri(gcs_uri, table_ref, job_config=job_config)
    job.result()

    print(f"✅ Loaded {job.output_rows} rows into {PROJECT_ID}.{DATASET}.{TABLE}")


# ── Entry Point ──────────────────────────────────────────────────
if __name__ == "__main__":
    date_str = os.environ.get("INGEST_DATE", "2024-11-01")
    load_gcs_to_bigquery(date_str)