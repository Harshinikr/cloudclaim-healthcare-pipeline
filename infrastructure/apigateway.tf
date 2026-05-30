resource "aws_apigatewayv2_api" "claims_api" {
  name          = "${var.project_name}-api"
  protocol_type = "HTTP"

  tags = {
    Project     = var.project_name
    Environment = var.environment
  }
}

resource "aws_apigatewayv2_integration" "query_integration" {
  api_id                 = aws_apigatewayv2_api.claims_api.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.query.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "get_claim" {
  api_id    = aws_apigatewayv2_api.claims_api.id
  route_key = "GET /claims/{claim_id}"
  target    = "integrations/${aws_apigatewayv2_integration.query_integration.id}"
}

resource "aws_apigatewayv2_stage" "dev" {
  api_id      = aws_apigatewayv2_api.claims_api.id
  name        = "dev"
  auto_deploy = true

  tags = {
    Project     = var.project_name
    Environment = var.environment
  }
}

output "api_endpoint" {
  description = "API Gateway endpoint URL"
  value       = "${aws_apigatewayv2_stage.dev.invoke_url}/claims/{claim_id}"
}

output "s3_bucket_name" {
  description = "S3 bucket name for claim ingestion"
  value       = aws_s3_bucket.claims_bucket.bucket
}

output "dynamodb_table_name" {
  description = "DynamoDB table name"
  value       = aws_dynamodb_table.claims_table.name
}