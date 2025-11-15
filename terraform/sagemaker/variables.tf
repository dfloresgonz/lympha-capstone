# Variables
variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-2"
}

variable "tracking_server_name" {
  description = "Nombre del MLflow tracking server"
  type        = string
  default     = "mlflow-tracking-server-lympha-01"
}

variable "tracking_server_size" {
  description = "Tamaño del MLflow tracking server"
  type        = string
  default     = "Small"

  validation {
    condition     = contains(["Small", "Medium", "Large"], var.tracking_server_size)
    error_message = "tracking_server_size must be one of: Small, Medium, Large."
  }
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "sagemaker_endpoint_name" {
  description = "The name of the SageMaker endpoint"
  type        = string
  default     = "mlflow-sagemaker-endpoint"
}
