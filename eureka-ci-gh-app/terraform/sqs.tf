resource "aws_sqs_queue" "check_suite_dlq" {
  name                      = "eureka-ci-check-suite-dlq-${var.environment}"
  message_retention_seconds = 1209600  # 14 days

  tags = merge(var.tags, {
    Name        = "eureka-ci-check-suite-dlq-${var.environment}"
    Environment = var.environment
  })
}

resource "aws_sqs_queue" "check_suite" {
  name                       = "eureka-ci-check-suite-${var.environment}"
  visibility_timeout_seconds = var.sqs_visibility_timeout
  message_retention_seconds  = 86400  # 1 day

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.check_suite_dlq.arn
    maxReceiveCount     = var.sqs_max_receive_count
  })

  tags = merge(var.tags, {
    Name        = "eureka-ci-check-suite-${var.environment}"
    Environment = var.environment
  })
}

resource "aws_sqs_queue_policy" "check_suite" {
  queue_url = aws_sqs_queue.check_suite.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
        Action = [
          "sqs:SendMessage",
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes"
        ]
        Resource = aws_sqs_queue.check_suite.arn
      }
    ]
  })
}