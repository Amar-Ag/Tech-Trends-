"""
stackoverflow_ingest.py
─────────────────────────────────────────────────────────────────
Downloads the Stack Overflow Annual Developer Survey CSV from
the official source and uploads it to GCS as Parquet.

The survey is released once per year (usually May/June).
This script is designed to run once per year via a Kestra schedule,
or manually when the new survey drops.

Source: https://survey.stackoverflow.co/
The CSV files are publicly available as zip archives.

GCS path:
  gs://<bucket>/raw/stackoverflow/year=YYYY/survey_responses.parquet
─────────────────────────────────────────────────────────────────
"""

import io
import logging
import os
import zipfile

import pandas as pd
import requests
from google.cloud import storage

from dotenv import load_dotenv
load_dotenv()  # reads .env automatically

# ── Configuration ────────────────────────────────────────────────
GCS_BUCKET = os.environ.get("GCS_BUCKET", "your-tech-trends-bucket")

# Direct download URLs for recent survey years
# Add new years here when they're released
SURVEY_URLS = {
    "2024": "https://cdn.stackoverflow.co/files/jo7n4k8s/production/49915bfd46d0902c3564fd9a06b509d08a20488c.zip",
    "2023": "https://cdn.stackoverflow.co/files/jo7n4k8s/production/19fe1a8a-b810-4d5f-9e16-24e2c1b4d5e0.zip",
}

# The columns we actually care about — survey has 80+ columns, we only need these
# Adjust column names if they differ between survey years
COLUMNS_TO_KEEP = [
    "ResponseId",
    "MainBranch",           # Professional developer or not
    "Employment",           # Full-time, part-time, etc.
    "RemoteWork",           # Remote, hybrid, in-person
    "EdLevel",              # Education level
    "YearsCode",            # Years coding total
    "YearsCodePro",         # Years coding professionally
    "DevType",              # Job title / role
    "OrgSize",              # Company size
    "Country",              # Country of residence
    "LanguageHaveWorkedWith",  # Languages used this year
    "LanguageWantToWorkWith",  # Languages they want to use
    "DatabaseHaveWorkedWith",
    "PlatformHaveWorkedWith",  # Cloud/hosting platforms
    "FrameworkHaveWorkedWith",
    "AISearchHaveWorkedWith",  # AI tools used
    "ConvertedCompYearly",  # Annual salary in USD
    "JobSat",               # Job satisfaction
    "Age",
    "Gender",
    "Currency",
]

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


# ── Core Functions ───────────────────────────────────────────────

def download_survey_zip(year: str) -> bytes:
    """Download the survey zip file for the given year."""
    url = SURVEY_URLS.get(year)
    if not url:
        raise ValueError(
            f"No URL configured for year {year}. "
            f"Available years: {list(SURVEY_URLS.keys())}"
        )

    logger.info(f"Downloading Stack Overflow {year} survey from: {url}")
    response = requests.get(url, timeout=120)
    response.raise_for_status()
    logger.info(f"  → Downloaded {len(response.content) / 1_000_000:.1f} MB")
    return response.content


def extract_survey_csv(zip_bytes: bytes) -> pd.DataFrame:
    """
    Extract the main survey CSV from the zip archive.
    The zip usually contains: survey_results_public.csv + schema CSV + readme
    We want survey_results_public.csv
    """
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        # Find the main results file (not the schema)
        csv_files = [f for f in zf.namelist() if "public" in f.lower() and f.endswith(".csv")]
        logger.info(f"  → Files in zip: {zf.namelist()}")

        if not csv_files:
            raise FileNotFoundError("Could not find survey_results_public.csv in zip archive")

        target_file = csv_files[0]
        logger.info(f"  → Extracting: {target_file}")

        with zf.open(target_file) as f:
            df = pd.read_csv(f, low_memory=False)

    logger.info(f"  → Raw shape: {df.shape[0]:,} rows × {df.shape[1]} columns")
    return df


def clean_survey_data(df: pd.DataFrame, year: str) -> pd.DataFrame:
    """
    Select relevant columns and do light cleaning.
    We keep this minimal — heavy transformation happens in dbt.
    """
    # Only keep columns that exist in this year's survey
    # (column names sometimes change between years)
    available_cols = [c for c in COLUMNS_TO_KEEP if c in df.columns]
    missing_cols   = [c for c in COLUMNS_TO_KEEP if c not in df.columns]

    if missing_cols:
        logger.warning(f"  ⚠ Columns not found in {year} survey (may have been renamed): {missing_cols}")

    df = df[available_cols].copy()

    # Add survey year as a column — critical for year-over-year analysis in dbt
    df["survey_year"] = int(year)

    # Standardise salary: convert to numeric, nullify non-responses
    if "ConvertedCompYearly" in df.columns:
        df["ConvertedCompYearly"] = pd.to_numeric(df["ConvertedCompYearly"], errors="coerce")
        # Remove extreme outliers (likely input errors: >$5M annual)
        df.loc[df["ConvertedCompYearly"] > 5_000_000, "ConvertedCompYearly"] = None

    logger.info(f"  → Cleaned shape: {df.shape[0]:,} rows × {df.shape[1]} columns")
    return df


def upload_to_gcs(df: pd.DataFrame, bucket_name: str, gcs_path: str) -> None:
    """Convert DataFrame to Parquet and upload to GCS."""
    logger.info(f"Uploading → gs://{bucket_name}/{gcs_path}")

    buffer = io.BytesIO()
    df.to_parquet(buffer, index=False, engine="pyarrow")
    buffer.seek(0)

    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(gcs_path)
    blob.upload_from_file(buffer, content_type="application/octet-stream")

    logger.info(f"  → Upload complete ({len(df):,} rows)")


def ingest_survey(year: str, bucket_name: str = GCS_BUCKET) -> None:
    """
    Full ingestion pipeline for one survey year:
      1. Download zip
      2. Extract CSV
      3. Clean & filter columns
      4. Upload Parquet to GCS
    """
    logger.info(f"Starting Stack Overflow survey ingestion for year: {year}")

    zip_bytes = download_survey_zip(year)
    raw_df    = extract_survey_csv(zip_bytes)
    clean_df  = clean_survey_data(raw_df, year)

    gcs_path = f"raw/stackoverflow/year={year}/survey_responses.parquet"
    upload_to_gcs(clean_df, bucket_name, gcs_path)

    logger.info(f"Done. Survey {year} ingested successfully.")


# ── Entry Point ──────────────────────────────────────────────────

if __name__ == "__main__":
    """
    Run manually:   python stackoverflow_ingest.py
    Default:        ingests 2024 survey
    Override year:  set env var SURVEY_YEAR=2023
    """
    year = os.environ.get("SURVEY_YEAR", "2024")
    ingest_survey(year)