# Package the Lambda functions as zip files
data "archive_file" "ingestion_zip" {
  type        = "zip"
  source_file = "${path.module}/../lambda/ingestion/handler.py"
  output_path = "${path.module}/../function.zip"
}

data "archive_file" "rules_engine_zip" {
  type        = "zip"
  source_file = "${path.module}/../lambda/rules_engine/handler.py"
  output_path = "${path.module}/../rules-engine.zip"
}

data "archive_file" "query_zip" {
  type        = "zip"
  source_file = "${path.module}/../lambda/query/handler.py"
  output_path = "${path.module}/../query.zip"
}

# Ingestion Lambda
resource "aws_lambda_function" "ingestion" {
  function_name    = "${var.project_name}-ingestion"
  role             = aws_iam_role.lambda_role.arn
  handler          = "handler.handler"
  runtime          = "python3.12"
  filename         = data.archive_file.ingestion_zip.output_path
  source_code_hash = data.archive_file.ingestion_zip.output_base64sha256

  environment {
    variables = {
      DYNAMODB_TABLE = var.dynamodb_table_name
      SQS_QUEUE_URL  = aws_sqs_queue.claims_queue.url
    }
  }

  tags = {
    Project     = var.project_name
    Environment = var.environment
  }
}

# Rules Engine Lambda
resource "aws_lambda_function" "rules_engine" {
  function_name    = "${var.project_name}-rules-engine"
  role             = aws_iam_role.lambda_role.arn
  handler          = "handler.handler"
  runtime          = "python3.12"
  filename         = data.archive_file.rules_engine_zip.output_path
  source_code_hash = data.archive_file.rules_engine_zip.output_base64sha256

  environment {
    variables = {
      DYNAMODB_TABLE = var.dynamodb_table_name
      SNS_TOPIC_ARN  = aws_sns_topic.rejections.arn
    }
  }

  tags = {
    Project     = var.project_name
    Environment = var.environment
  }
}

# Query Lambda
resource "aws_lambda_function" "query" {
  function_name    = "${var.project_name}-query"
  role             = aws_iam_role.lambda_role.arn
  handler          = "handler.handler"
  runtime          = "python3.12"
  filename         = data.archive_file.query_zip.output_path
  source_code_hash = data.archive_file.query_zip.output_base64sha256

  environment {
    variables = {
      DYNAMODB_TABLE = var.dynamodb_table_name
    }
  }

  tags = {
    Project     = var.project_name
    Environment = var.environment
  }
}

# S3 permission to invoke ingestion Lambda
resource "aws_lambda_permission" "s3_invoke" {
  statement_id  = "s3-invoke-permission"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.ingestion.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.claims_bucket.arn
}

# API Gateway permission to invoke query Lambda
resource "aws_lambda_permission" "apigateway_invoke" {
  statement_id  = "apigateway-invoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.query.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.claims_api.execution_arn}/*/*/claims/*"
}

# SQS trigger for rules engine Lambda
resource "aws_lambda_event_source_mapping" "sqs_trigger" {
  event_source_arn = aws_sqs_queue.claims_queue.arn
  function_name    = aws_lambda_function.rules_engine.arn
  batch_size       = 1
}