resource "aws_s3_bucket" "eureka_ci_config" {
  bucket = "eureka-ci-config-${var.environment}"

  tags = merge(var.tags, {
    Name        = "eureka-ci-config-${var.environment}"
    Environment = var.environment
  })
}

resource "aws_s3_bucket_versioning" "eureka_ci_config" {
  bucket = aws_s3_bucket.eureka_ci_config.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "eureka_ci_config" {
  bucket = aws_s3_bucket.eureka_ci_config.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "eureka_ci_config" {
  bucket = aws_s3_bucket.eureka_ci_config.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_object" "repository_config" {
  bucket = aws_s3_bucket.eureka_ci_config.id
  key    = "config/repositories.json"
  source = "${path.module}/../config/repositories.json"
  etag   = filemd5("${path.module}/../config/repositories.json")

  tags = merge(var.tags, {
    Name        = "repository-config-${var.environment}"
    Environment = var.environment
  })
}