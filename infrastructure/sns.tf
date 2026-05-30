resource "aws_sns_topic" "rejections" {
  name = "${var.project_name}-rejections"

  tags = {
    Project     = var.project_name
    Environment = var.environment
  }
}

resource "aws_sns_topic_subscription" "email_alert" {
  topic_arn = aws_sns_topic.rejections.arn
  protocol  = "email"
  endpoint  = var.alert_email
}