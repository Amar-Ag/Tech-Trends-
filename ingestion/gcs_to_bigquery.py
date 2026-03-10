from google.cloud import bigquery
import os

from dotenv import load_dotenv
load_dotenv()  # reads .env automatically

PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "tech-trends-489801")
DATASET    = os.environ.get("BQ_DATASET", "raw")
TABLE      = os.environ.get("BQ_TABLE", "github_events")
GCS_BUCKET = os.environ.get("GCS_BUCKET", "tech-trends-bucket-489801")

def load_gcs_to_bigquery(date_str: str) -> None:
    """
    Load a single day's parquet files from GCS into BigQuery.
    date_str format: "2024-11-01"
    """
    client = bigquery.Client(project=PROJECT_ID)

    gcs_uri = f"gs://{GCS_BUCKET}/raw/github/year={date_str[:4]}/month={date_str[5:7]}/day={date_str[8:10]}/*.parquet"

    table_ref = f"{PROJECT_ID}.{DATASET}.{TABLE}"

    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.PARQUET,
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
    )

    job = client.load_table_from_uri(
        gcs_uri,
        table_ref,
        job_config=job_config,
    )
    job.result()

    print(f"✅ Loaded {job.output_rows} rows into {PROJECT_ID}.{DATASET}.{TABLE}")


if __name__ == "__main__":
    date_str = os.environ.get("INGEST_DATE", "2024-11-01")
    load_gcs_to_bigquery(date_str)