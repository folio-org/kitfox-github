# SQS Queue for check suite events
resource "aws_sqs_queue" "check_suite" {
  name                       = "${var.app_name}-check-suite-queue"
  visibility_timeout_seconds = var.sqs_visibility_timeout
  message_retention_seconds  = 86400  # 1 day
  max_message_size           = 262144 # 256 KB
  receive_wait_time_seconds  = 10     # Long polling

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.check_suite_dlq.arn
    maxReceiveCount     = var.sqs_max_receive_count
  })

  tags = var.tags
}

# Dead Letter Queue for check suite events
resource "aws_sqs_queue" "check_suite_dlq" {
  name                      = "${var.app_name}-check-suite-dlq"
  message_retention_seconds = 1209600 # 14 days

  tags = var.tags
}

# DLQ alerting
resource "aws_sns_topic" "check_suite_dlq_alerts" {
  name = "${var.app_name}-check-suite-dlq-alerts"
  tags = var.tags
}

resource "aws_sns_topic_subscription" "check_suite_dlq_alerts_email" {
  for_each  = toset(var.dlq_alarm_emails)
  topic_arn = aws_sns_topic.check_suite_dlq_alerts.arn
  protocol  = "email"
  endpoint  = each.value
}

resource "aws_cloudwatch_metric_alarm" "check_suite_dlq_not_empty" {
  alarm_name        = "${var.app_name}-check-suite-dlq-not-empty"
  alarm_description = "Messages present in ${aws_sqs_queue.check_suite_dlq.name} (failed webhook processing / workflow dispatch)"
  namespace         = "AWS/SQS"
  metric_name       = "ApproximateNumberOfMessagesVisible"
  dimensions = {
    QueueName = aws_sqs_queue.check_suite_dlq.name
  }
  statistic           = "Maximum"
  period              = 60
  evaluation_periods  = 1
  comparison_operator = "GreaterThanThreshold"
  threshold           = 0
  treat_missing_data  = "notBreaching"
  alarm_actions       = [aws_sns_topic.check_suite_dlq_alerts.arn]
  ok_actions          = [aws_sns_topic.check_suite_dlq_alerts.arn]
  tags                = var.tags
}

# SQS Queue Policy
resource "aws_sqs_queue_policy" "check_suite_policy" {
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