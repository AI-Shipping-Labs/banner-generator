output "ecr_repository_url" {
  description = "Repository URL for the Lambda container image."
  value       = aws_ecr_repository.lambda.repository_url
}

output "aws_region" {
  description = "AWS region used by the provider."
  value       = var.aws_region
}

output "function_name" {
  description = "Lambda function name."
  value       = aws_lambda_function.renderer.function_name
}

output "function_url" {
  description = "Lambda Function URL for render requests."
  value       = aws_lambda_function_url.renderer.function_url
}

output "template_bucket" {
  description = "S3 bucket containing synced templates."
  value       = aws_s3_bucket.templates.id
}

output "output_bucket" {
  description = "Default S3 bucket for rendered outputs."
  value       = aws_s3_bucket.outputs.id
}

output "output_prefix" {
  description = "Recommended prefix for rendered outputs."
  value       = local.output_prefix
}

output "auth_token" {
  description = "Bearer token for the Function URL."
  value       = local.auth_token
  sensitive   = true
}
