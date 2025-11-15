resource "aws_s3_bucket" "datalake" {
  bucket = "s3-${var.environment}-datalake-lympha-01"

  force_destroy = true

  tags = {
    Name        = "Lympha Data Lake"
    Environment = var.environment
  }
}

output "datalake_bucket_name" {
  value = aws_s3_bucket.datalake.bucket
}

output "datalake_bucket_arn" {
  value = aws_s3_bucket.datalake.arn
}

output "raw_prefix" {
  value = "raw/"
}

output "curated_prefix" {
  value = "curated/"
}

output "predictions_prefix" {
  value = "predictions/"
}
