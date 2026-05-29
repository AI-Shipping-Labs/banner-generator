# Banner Generator Infrastructure

This Terraform deploys the renderer as an AWS Lambda container with:

- an ECR repository for the Docker image
- a private S3 bucket for templates
- a private S3 bucket for rendered outputs
- a Lambda Function URL protected by a bearer token checked inside the handler

Terraform state, plans, tfvars, and generated deploy env files are ignored by git.

Note: this Terraform is temporary in this repository. After the renderer is
redeployed in the other AWS account, the long-lived infrastructure definition
should move to the dedicated infra repository. Once that migration is complete,
destroy the stack managed from this repo.

## Deploy

From the repo root:

```bash
cd infra
terraform init
terraform apply -target=aws_ecr_repository.lambda
```

Build and push the image:

```bash
ECR_REPOSITORY_URL="$(terraform output -raw ecr_repository_url)"
AWS_REGION="$(terraform output -raw aws_region 2>/dev/null || aws configure get region)"

aws ecr get-login-password --region "$AWS_REGION" \
  | docker login --username AWS --password-stdin "$ECR_REPOSITORY_URL"

docker buildx build \
  --platform linux/amd64 \
  --provenance=false \
  --sbom=false \
  --output "type=image,name=$ECR_REPOSITORY_URL:latest,push=true,oci-mediatypes=false" \
  ..
```

Apply the full stack:

```bash
terraform apply
```

Read the deployed values:

```bash
FUNCTION_URL="$(terraform output -raw function_url)"
AUTH_TOKEN="$(terraform output -raw auth_token)"
OUTPUT_BUCKET="$(terraform output -raw output_bucket)"
```

Do not hardcode `FUNCTION_URL` or `AUTH_TOKEN` into the Remix app. Pass them to the app through that repo's environment variables or deployment secret manager.

## Invoke

Return the rendered image bytes over HTTP:

```bash
curl -sS -X POST "$FUNCTION_URL" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d @../examples/lambda-content-event.json \
  -o rendered.png
```

Inspect the Lambda proxy response with the base64 body through direct Lambda invocation:

```bash
cat > /tmp/banner-generator-event.json <<EOF
{
  "headers": {"authorization": "Bearer $AUTH_TOKEN"},
  "template": "asl-content-card",
  "format": "png",
  "size": "og",
  "data": {
    "title": "Direct Lambda invoke",
    "subtitle": "The response body is base64 here."
  }
}
EOF

aws lambda invoke \
  --function-name "$(terraform output -raw function_name)" \
  --payload fileb:///tmp/banner-generator-event.json \
  /tmp/banner-generator-response.json

jq '{statusCode, isBase64Encoded, contentType: .headers["Content-Type"]}' \
  /tmp/banner-generator-response.json
```

Render and store in the Terraform-managed output bucket:

```bash
curl -sS -X POST "$FUNCTION_URL" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "template": "asl-content-card",
    "format": "png",
    "size": "og",
    "data": {
      "kind": "Article",
      "title": "Rendered through Lambda",
      "subtitle": "Stored in S3",
      "meta": "Sandbox"
    },
    "s3": {
      "key": "renders/example.png",
      "content_type": "image/png"
    }
  }'
```

The handler also accepts `"s3": {"bucket": "...", "key": "..."}` when the Lambda role has permission to write to that bucket.

## Update Templates

Templates are uploaded from `banner_generator/templates` by Terraform. After changing templates:

```bash
cd infra
terraform apply
```

The Lambda checks the template bucket and refreshes its `/tmp` cache when S3 object metadata changes.
