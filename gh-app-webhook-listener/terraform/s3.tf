# S3 bucket for application configuration
resource "aws_s3_bucket" "app_config" {
  bucket = "${var.app_name}-config-${data.aws_caller_identity.current.account_id}"

  tags = var.tags
}

# S3 bucket versioning
resource "aws_s3_bucket_versioning" "app_config_versioning" {
  bucket = aws_s3_bucket.app_config.id

  versioning_configuration {
    status = "Enabled"
  }
}

# S3 bucket encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "app_config_encryption" {
  bucket = aws_s3_bucket.app_config.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# S3 bucket public access block
resource "aws_s3_bucket_public_access_block" "app_config_public_access" {
  bucket = aws_s3_bucket.app_config.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# S3 bucket policy
resource "aws_s3_bucket_policy" "app_config_policy" {
  bucket = aws_s3_bucket.app_config.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          AWS = aws_iam_role.lambda_execution_role.arn
        }
        Action = [
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.app_config.arn,
          "${aws_s3_bucket.app_config.arn}/*"
        ]
      }
    ]
  })
}

# Upload default workflow configuration
resource "aws_s3_object" "default_workflow_config" {
  bucket = aws_s3_bucket.app_config.id
  key    = "workflows/default.json"
  source = "../config/workflows.json"
  etag   = filemd5("../config/workflows.json")

  tags = var.tags
}