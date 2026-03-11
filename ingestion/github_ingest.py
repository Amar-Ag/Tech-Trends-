import gzip
import io
import json
import logging
import os
import base64
from datetime import datetime, timedelta

import pandas as pd
import requests
from google.cloud import storage
from google.oauth2 import service_account
from dotenv import load_dotenv

load_dotenv()

# ── Configuration ────────────────────────────────────────────────
GCS_BUCKET = os.environ.get("GCS_BUCKET", "tech-trends-bucket-489801")
GH_ARCHIVE_BASE_URL = "https://data.gharchive.org"

RELEVANT_EVENT_TYPES = {
    "WatchEvent",
    "ForkEvent",
    "PushEvent",
    "PullRequestEvent",
}

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


# ── Credentials ──────────────────────────────────────────────────
def get_credentials():
    key_b64 = os.environ.get("GCP_SA_KEY_B64")
    if key_b64:
        key_b64 = key_b64.strip()
        key_bytes = base64.b64decode(key_b64)
        key_str = key_bytes.decode("utf-8", errors="ignore").strip()
        # show what's around the problem area
        print(f"Total length: {len(key_str)}")
        print(f"Chars 2370-2390: {repr(key_str[2370:2390])}")
        print(f"Last 20 chars: {repr(key_str[-20:])}")
        info = json.loads(key_str)
        return service_account.Credentials.from_service_account_info(info)
    return None

# ── Core Functions ───────────────────────────────────────────────

def build_url(date: datetime, hour: int) -> str:
    return f"{GH_ARCHIVE_BASE_URL}/{date.strftime('%Y-%m-%d')}-{hour}.json.gz"


def download_and_parse(url: str) -> list:
    logger.info(f"Downloading: {url}")
    response = requests.get(url, timeout=60, stream=True)

    if response.status_code == 404:
        logger.warning(f"No data for: {url} (404 — skipping)")
        return []

    response.raise_for_status()

    events = []
    with gzip.open(io.BytesIO(response.content), "rt", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
                if event.get("type") in RELEVANT_EVENT_TYPES:
                    events.append(flatten_event(event))
            except json.JSONDecodeError:
                continue

    logger.info(f"  → Parsed {len(events)} relevant events")
    return events


def flatten_event(event: dict) -> dict:
    repo_name = event.get("repo", {}).get("name", "")
    owner, _, repo = repo_name.partition("/")

    return {
        "event_id":    event.get("id"),
        "event_type":  event.get("type"),
        "actor_login": event.get("actor", {}).get("login"),
        "actor_id":    event.get("actor", {}).get("id"),
        "repo_id":     event.get("repo", {}).get("id"),
        "repo_name":   repo_name,
        "repo_owner":  owner,
        "repo_slug":   repo,
        "payload":     json.dumps(event.get("payload", {})),
        "created_at":  event.get("created_at"),
    }


def upload_to_gcs(df: pd.DataFrame, bucket_name: str, gcs_path: str) -> None:
    logger.info(f"Uploading {len(df)} rows → gs://{bucket_name}/{gcs_path}")

    buffer = io.BytesIO()
    df.to_parquet(buffer, index=False, engine="pyarrow")
    buffer.seek(0)

    # use decoded credentials if available, otherwise use key file
    credentials = get_credentials()
    client = storage.Client(credentials=credentials)

    bucket = client.bucket(bucket_name)
    blob = bucket.blob(gcs_path)
    blob.upload_from_file(buffer, content_type="application/octet-stream")

    logger.info(f"  → Upload complete")


def ingest_hour(date: datetime, hour: int, bucket_name: str) -> int:
    url = build_url(date, hour)
    events = download_and_parse(url)

    if not events:
        return 0

    df = pd.DataFrame(events)
    df["created_at"] = pd.to_datetime(df["created_at"], utc=True)
    df["actor_id"]   = pd.to_numeric(df["actor_id"], errors="coerce")
    df["repo_id"]    = pd.to_numeric(df["repo_id"], errors="coerce")

    year  = date.strftime("%Y")
    month = date.strftime("%m")
    day   = date.strftime("%d")

    gcs_path = f"raw/github/year={year}/month={month}/day={day}/hour={hour:02d}.parquet"
    upload_to_gcs(df, bucket_name, gcs_path)

    del df
    return len(events)


def ingest_day(date: datetime, bucket_name: str = GCS_BUCKET) -> None:
    logger.info(f"Starting ingestion for {date.strftime('%Y-%m-%d')}")
    total_events = 0

    for hour in range(24):
        count = ingest_hour(date, hour, bucket_name)
        total_events += count
        logger.info(f"  Hour {hour:02d} done — running total: {total_events:,} events")

    logger.info(f"✅ Ingestion complete. Total events: {total_events:,}")


# ── Entry Point ──────────────────────────────────────────────────

if __name__ == "__main__":
    date_str = os.environ.get("INGEST_DATE")
    if date_str:
        target_date = datetime.strptime(date_str, "%Y-%m-%d")
    else:
        target_date = datetime.utcnow() - timedelta(days=1)

    ingest_day(target_date)