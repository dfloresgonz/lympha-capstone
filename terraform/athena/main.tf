resource "aws_s3_bucket" "results" {
  bucket = "s3-${var.environment}-lympha-athena-results-01"
}

resource "aws_athena_workgroup" "primary" {
  name = "lympha-${var.environment}"

  configuration {
    result_configuration {
      output_location = "s3://${aws_s3_bucket.results.bucket}/"
    }
  }
}

output "athena_workgroup" {
  value = aws_athena_workgroup.primary.name
}
