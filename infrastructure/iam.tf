resource "aws_iam_role" "lambda_role" {
  name = "${var.project_name}-lambda-role"

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

  tags = {
    Project     = var.project_name
    Environment = var.environment
  }
}

resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "lambda_permissions" {
  name = "${var.project_name}-lambda-permissions"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "ReadFromS3"
        Effect = "Allow"
        Action = "s3:GetObject"
        Resource = "${aws_s3_bucket.claims_bucket.arn}/*"
      },
      {
        Sid    = "WriteToDynamoDB"
        Effect = "Allow"
        Action = "dynamodb:PutItem"
        Resource = aws_dynamodb_table.claims_table.arn
      },
      {
        Sid    = "ReadFromDynamoDB"
        Effect = "Allow"
        Action = "dynamodb:GetItem"
        Resource = aws_dynamodb_table.claims_table.arn
      },
      {
        Sid    = "SendToSQS"
        Effect = "Allow"
        Action = "sqs:SendMessage"
        Resource = aws_sqs_queue.claims_queue.arn
      },
      {
        Sid    = "ReadFromSQS"
        Effect = "Allow"
        Action = [
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes"
        ]
        Resource = aws_sqs_queue.claims_queue.arn
      },
      {
        Sid      = "PublishToSNS"
        Effect   = "Allow"
        Action   = "sns:Publish"
        Resource = aws_sns_topic.rejections.arn
      }
    ]
  })
}