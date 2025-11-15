data "aws_region" "current" {}
data "aws_caller_identity" "current" {}

resource "aws_s3_bucket" "mlflow_artifacts" {
  bucket = "s3-mlflow-artifacts-${var.tracking_server_name}-01"

  tags = {
    Name        = "MLflow Artifacts"
    Environment = var.environment
  }
}

resource "aws_s3_bucket_versioning" "mlflow_artifacts_versioning" {
  bucket = aws_s3_bucket.mlflow_artifacts.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "mlflow_artifacts_encryption" {
  bucket = aws_s3_bucket.mlflow_artifacts.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "mlflow_artifacts_pab" {
  bucket = aws_s3_bucket.mlflow_artifacts.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_iam_role" "mlflow_tracking_server_role" {
  name = "${var.tracking_server_name}-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "sagemaker.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name        = "${var.tracking_server_name}-role"
    Environment = var.environment
  }
}

resource "aws_iam_policy" "mlflow_s3_access" {
  name        = "policy-${var.tracking_server_name}-s3-access"
  description = "Policy for MLflow tracking server S3 access"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket",
          "s3:GetBucketLocation",
          "s3:GetBucketVersioning",
          "s3:ListBucketVersions",
          "s3:GetObjectVersion",
          "s3:DeleteObjectVersion",
          "s3:PutBucketVersioning",
          "glue:*",
          "athena:*",
        ]
        Resource = [
          aws_s3_bucket.mlflow_artifacts.arn,
          "${aws_s3_bucket.mlflow_artifacts.arn}/*",
          "*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:DescribeLogStreams"
        ]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect = "Allow"
        Action = [
          "sagemaker:*"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_policy" "mlflow_ui_access" {
  name        = "${var.tracking_server_name}-ui-access"
  description = "Policy for MLflow UI access"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "sagemaker-mlflow:AccessUI",
          "sagemaker-mlflow:GetTrackingServer",
          "sagemaker-mlflow:ListTrackingServers"
        ]
        Resource = aws_sagemaker_mlflow_tracking_server.mlflow_server.arn
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "mlflow_s3_access_attachment" {
  role       = aws_iam_role.mlflow_tracking_server_role.name
  policy_arn = aws_iam_policy.mlflow_s3_access.arn
}

resource "aws_iam_role_policy_attachment" "sagemaker_execution_role_policy" {
  role       = aws_iam_role.mlflow_tracking_server_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSageMakerFullAccess"
}

resource "aws_iam_role_policy_attachment" "sagemaker_studio_mlflow_access" {
  role       = aws_iam_role.mlflow_tracking_server_role.name
  policy_arn = aws_iam_policy.mlflow_ui_access.arn
}

resource "aws_sagemaker_mlflow_tracking_server" "mlflow_server" {
  tracking_server_name = var.tracking_server_name
  role_arn             = aws_iam_role.mlflow_tracking_server_role.arn

  tracking_server_size = var.tracking_server_size

  artifact_store_uri = "s3://${aws_s3_bucket.mlflow_artifacts.bucket}/mlflow-artifacts"

  automatic_model_registration = true

  weekly_maintenance_window_start = "Tue:03:00"

  tags = {
    Name        = var.tracking_server_name
    Environment = var.environment
    Service     = "MLflow"
  }

  depends_on = [
    aws_iam_role_policy_attachment.mlflow_s3_access_attachment,
    aws_iam_role_policy_attachment.sagemaker_execution_role_policy
  ]
}

# Outputs
output "mlflow_tracking_server_arn" {
  description = "ARN del MLflow tracking server"
  value       = aws_sagemaker_mlflow_tracking_server.mlflow_server.arn
}

output "mlflow_tracking_server_url" {
  description = "URL del MLflow tracking server"
  value       = aws_sagemaker_mlflow_tracking_server.mlflow_server.tracking_server_url
}

output "mlflow_tracking_server_name" {
  description = "Nombre del MLflow tracking server"
  value       = aws_sagemaker_mlflow_tracking_server.mlflow_server.tracking_server_name
}

output "s3_artifacts_bucket" {
  description = "S3 bucket para artefactos de MLflow"
  value       = aws_s3_bucket.mlflow_artifacts.bucket
}

output "s3_artifacts_uri" {
  description = "URI completa para artefactos de MLflow"
  value       = "s3://${aws_s3_bucket.mlflow_artifacts.bucket}/mlflow-artifacts"
}
