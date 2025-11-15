variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}
variable "datalake_bucket" {}
variable "raw_prefix" {}
variable "predictions_prefix" {}
