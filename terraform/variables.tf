variable "project_id" {
  description = "Your GCP project ID"
  type        = string
  default     = "tech-trends-489801"
}

variable "region" {
  description = "GCP region for all resources"
  type        = string
  default     = "us-central1"
}

variable "gcs_bucket_name" {
  description = "Name of the GCS bucket (must be globally unique)"
  type        = string
  default     = "tech-trends-bucket-489801"
}

variable "credentials_file" {
  description = "Path to the GCP service account JSON key"
  type        = string
  default     = "../keys/service-account.json"
}
