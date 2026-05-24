variable "aws_region" {
  description = "AWS region to deploy into."
  type        = string
  default     = "eu-west-1"
}

variable "project_name" {
  description = "Name prefix for deployed resources."
  type        = string
  default     = "banner-generator"
}

variable "environment" {
  description = "Deployment environment name."
  type        = string
  default     = "sandbox"
}

variable "image_tag" {
  description = "ECR image tag for the Lambda container."
  type        = string
  default     = "latest"
}

variable "lambda_memory_size" {
  description = "Lambda memory in MB. Chromium rendering needs more than the default."
  type        = number
  default     = 2048
}

variable "lambda_timeout" {
  description = "Lambda timeout in seconds."
  type        = number
  default     = 60
}

variable "auth_token" {
  description = "Bearer token required by the Lambda Function URL. Leave empty to generate one."
  type        = string
  default     = ""
  sensitive   = true
}

variable "template_prefix" {
  description = "S3 prefix where templates are uploaded."
  type        = string
  default     = "templates"
}

variable "output_prefix" {
  description = "Default S3 prefix callers should use for rendered outputs."
  type        = string
  default     = "renders"
}
