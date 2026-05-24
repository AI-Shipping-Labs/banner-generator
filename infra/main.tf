locals {
  name            = "${var.project_name}-${var.environment}"
  template_prefix = trim(var.template_prefix, "/")
  output_prefix   = trim(var.output_prefix, "/")
  template_files  = fileset("${path.module}/../banner_generator/templates", "**/*")
  auth_token      = var.auth_token != "" ? var.auth_token : random_password.auth_token.result

  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

resource "random_id" "suffix" {
  byte_length = 4
}

resource "random_password" "auth_token" {
  length  = 40
  special = false
}

resource "aws_ecr_repository" "lambda" {
  name                 = local.name
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = local.common_tags
}

resource "aws_ecr_lifecycle_policy" "lambda" {
  repository = aws_ecr_repository.lambda.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep the last 10 Lambda images"
        selection = {
          tagStatus   = "any"
          countType   = "imageCountMoreThan"
          countNumber = 10
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}

data "aws_ecr_image" "lambda" {
  repository_name = aws_ecr_repository.lambda.name
  image_tag       = var.image_tag
}

resource "aws_s3_bucket" "templates" {
  bucket = "${local.name}-templates-${random_id.suffix.hex}"
  tags   = local.common_tags
}

resource "aws_s3_bucket" "outputs" {
  bucket = "${local.name}-outputs-${random_id.suffix.hex}"
  tags   = local.common_tags
}

resource "aws_s3_bucket_public_access_block" "templates" {
  bucket                  = aws_s3_bucket.templates.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_public_access_block" "outputs" {
  bucket                  = aws_s3_bucket.outputs.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "templates" {
  bucket = aws_s3_bucket.templates.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "outputs" {
  bucket = aws_s3_bucket.outputs.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_object" "templates" {
  for_each = {
    for file in local.template_files : file => file
    if !endswith(file, "/")
  }

  bucket       = aws_s3_bucket.templates.id
  key          = "${local.template_prefix}/${each.value}"
  source       = "${path.module}/../banner_generator/templates/${each.value}"
  etag         = filemd5("${path.module}/../banner_generator/templates/${each.value}")
  content_type = lookup(local.content_types, try(regex("\\.[^.]+$", each.value), ""), "application/octet-stream")
}

locals {
  content_types = {
    ".css"  = "text/css"
    ".html" = "text/html"
    ".png"  = "image/png"
    ".svg"  = "image/svg+xml"
  }
}

resource "aws_iam_role" "lambda" {
  name = "${local.name}-lambda"

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

  tags = local.common_tags
}

resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "lambda_s3" {
  name = "${local.name}-s3"
  role = aws_iam_role.lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.templates.arn,
          "${aws_s3_bucket.templates.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject"
        ]
        Resource = "${aws_s3_bucket.outputs.arn}/*"
      }
    ]
  })
}

resource "aws_lambda_function" "renderer" {
  function_name = local.name
  role          = aws_iam_role.lambda.arn
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.lambda.repository_url}@${data.aws_ecr_image.lambda.image_digest}"
  memory_size   = var.lambda_memory_size
  timeout       = var.lambda_timeout

  ephemeral_storage {
    size = 1024
  }

  environment {
    variables = {
      BANNER_GENERATOR_AUTH_TOKEN      = local.auth_token
      BANNER_GENERATOR_TEMPLATE_BUCKET = aws_s3_bucket.templates.id
      BANNER_GENERATOR_TEMPLATE_PREFIX = local.template_prefix
      BANNER_GENERATOR_OUTPUT_BUCKET   = aws_s3_bucket.outputs.id
    }
  }

  depends_on = [
    aws_iam_role_policy_attachment.lambda_basic,
    aws_iam_role_policy.lambda_s3,
    aws_s3_object.templates,
  ]

  tags = local.common_tags
}

resource "aws_lambda_function_url" "renderer" {
  function_name      = aws_lambda_function.renderer.function_name
  authorization_type = "NONE"

  cors {
    allow_methods = ["POST"]
    allow_origins = ["*"]
    allow_headers = ["authorization", "content-type", "x-api-token"]
    max_age       = 300
  }
}

resource "aws_lambda_permission" "function_url_public" {
  statement_id           = "AllowFunctionUrlInvoke"
  action                 = "lambda:InvokeFunctionUrl"
  function_name          = aws_lambda_function.renderer.function_name
  principal              = "*"
  function_url_auth_type = "NONE"
}

resource "aws_lambda_permission" "function_url_invoke_function" {
  statement_id             = "AllowFunctionInvokeViaFunctionUrl"
  action                   = "lambda:InvokeFunction"
  function_name            = aws_lambda_function.renderer.function_name
  principal                = "*"
  invoked_via_function_url = true
}
