# These print useful info after `terraform apply` finishes

output "gcs_bucket_name" {
  description = "Name of the created GCS bucket"
  value       = google_storage_bucket.data_lake.name
}

output "gcs_bucket_url" {
  description = "Full GCS URL of the data lake bucket"
  value       = "gs://${google_storage_bucket.data_lake.name}"
}

output "bigquery_raw_dataset" {
  description = "BigQuery raw dataset ID"
  value       = google_bigquery_dataset.raw.dataset_id
}

output "bigquery_prod_dataset" {
  description = "BigQuery prod dataset ID"
  value       = google_bigquery_dataset.prod.dataset_id
}
