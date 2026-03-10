terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

# ── Provider ─────────────────────────────────────────────────────
# Tells Terraform to use GCP with our service account key
provider "google" {
  credentials = file(var.credentials_file)
  project     = var.project_id
  region      = var.region
}

# ── GCS Bucket (Data Lake) ────────────────────────────────────────
# This is where ingestion scripts upload raw Parquet files
resource "google_storage_bucket" "data_lake" {
  name          = var.gcs_bucket_name
  location      = var.region
  force_destroy = true   # allows bucket deletion even if it has files (useful during dev)

  # Auto-delete raw files after 90 days to save storage costs
  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type = "Delete"
    }
  }

  # Versioning off — we don't need history for raw ingestion files
  versioning {
    enabled = false
  }
}

# ── BigQuery Dataset: raw ─────────────────────────────────────────
# Landing zone — ingestion scripts load data here directly from GCS
# No transformations, just raw data as-is
resource "google_bigquery_dataset" "raw" {
  dataset_id    = "raw"
  friendly_name = "Raw Data"
  description   = "Raw ingested data from GitHub Archive and Stack Overflow Survey"
  location      = var.region

  # Auto-delete tables after 90 days (keeps costs low during dev)
  default_table_expiration_ms = 7776000000  # 90 days in milliseconds
}

# ── BigQuery Dataset: prod ────────────────────────────────────────
# Production zone — dbt writes transformed models here
# This is what your Looker Studio dashboard reads from
resource "google_bigquery_dataset" "prod" {
  dataset_id    = "prod"
  friendly_name = "Production Data"
  description   = "Transformed data produced by dbt — used by the dashboard"
  location      = var.region
}
