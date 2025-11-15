data "aws_region" "current" {}
data "aws_caller_identity" "current" {}

data "aws_ecr_repository" "lambda_repository" {
  name = "ecr-v2-${var.lambda_function_name}"
}

data "aws_ecr_image" "lambda_image" {
  repository_name = "ecr-v2-${var.lambda_function_name}"
  image_tag       = "latest"
}

### lambda
resource "aws_iam_role" "lambda_exec" {
  name = "${var.lambda_function_name}-exec-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Agregar esta política para MLflow access desde Lambda
resource "aws_iam_policy" "lambda_inference_policy" {
  name        = "policy-${var.lambda_function_name}"
  description = "Policy for Lambda to do inference"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "sagemaker:*"
          # "sagemaker:DescribeMLflowTrackingServer",
          # "sagemaker:GetMLflowTrackingServerStatus",
          # "sagemaker:ListMLflowTrackingServers"
        ]
        Resource = [
          module.sagemaker.aws_sagemaker_mlflow_tracking_server.mlflow_server.arn,
          "arn:aws:sagemaker:${data.aws_region.current.id}:${data.aws_caller_identity.current.account_id}:mlflow-tracking-server/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "sagemaker-mlflow:*"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket",
          "s3:GetBucketLocation",
          "s3:GetBucketVersioning"
        ]
        Resource = [
          module.sagemaker.aws_s3_bucket.mlflow_artifacts.arn,
          "${module.sagemaker.aws_s3_bucket.mlflow_artifacts.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "logs:DescribeLogGroups",
          "logs:DescribeLogStreams",
          "logs:GetLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })
}

# Attach la nueva política al rol de Lambda
resource "aws_iam_role_policy_attachment" "lambda_inference_policy_attachment" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = aws_iam_policy.lambda_inference_policy.arn
}

resource "aws_lambda_function" "inference_lambda" {
  function_name    = var.lambda_function_name
  role             = aws_iam_role.lambda_exec.arn
  image_uri        = "${data.aws_ecr_repository.lambda_repository.repository_url}:latest"
  package_type     = "Image"
  timeout          = var.timeout_seconds
  memory_size      = var.memory_size
  source_code_hash = data.aws_ecr_image.lambda_image.image_digest

  environment {
    variables = {
      MLFLOW_TRACKING_URI        = module.sagemaker.aws_sagemaker_mlflow_tracking_server.mlflow_server.tracking_server_url
      MLFLOW_TRACKING_SERVER_ARN = module.sagemaker.aws_sagemaker_mlflow_tracking_server.mlflow_server.arn
      GIT_PYTHON_REFRESH         = "quiet"
    }
  }
  depends_on = [
    aws_iam_role_policy_attachment.lambda_basic_execution,
    aws_iam_role_policy_attachment.lambda_inference_policy_attachment
  ]
}

output "lambda_function_arn" {
  value = aws_lambda_function.inference_lambda.arn
}

