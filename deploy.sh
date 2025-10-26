#!/bin/bash

# Automated Deployment Script for Accessibility Checker API
# Supports both AWS Lambda backend and Express.js alternative
# Usage: ./deploy.sh [dev|prod] [lambda|express]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_NAME="accessibility-checker"
AWS_REGION="${AWS_REGION:-us-east-1}"
STACK_NAME="${PROJECT_NAME}-${1:-dev}"

# Parse arguments
ENVIRONMENT="${1:-dev}"
BACKEND_TYPE="${2:-lambda}"

# Validate arguments
if [[ "$ENVIRONMENT" != "dev" && "$ENVIRONMENT" != "prod" ]]; then
    echo -e "${RED}Error: Environment must be 'dev' or 'prod'${NC}"
    echo "Usage: $0 [dev|prod] [lambda|express]"
    exit 1
fi

if [[ "$BACKEND_TYPE" != "lambda" && "$BACKEND_TYPE" != "express" ]]; then
    echo -e "${RED}Error: Backend type must be 'lambda' or 'express'${NC}"
    echo "Usage: $0 [dev|prod] [lambda|express]"
    exit 1
fi

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if AWS CLI is installed
    if ! command -v aws &> /dev/null; then
        log_error "AWS CLI is not installed. Please install it first."
        exit 1
    fi
    
    # Check if AWS CLI is configured
    if ! aws sts get-caller-identity &> /dev/null; then
        log_error "AWS CLI is not configured. Please run 'aws configure' first."
        exit 1
    fi
    
    # Check if jq is installed
    if ! command -v jq &> /dev/null; then
        log_error "jq is not installed. Please install it first."
        exit 1
    fi
    
    # Check if zip is installed
    if ! command -v zip &> /dev/null; then
        log_error "zip is not installed. Please install it first."
        exit 1
    fi
    
    log_success "All prerequisites met"
}

# Get AWS account ID
get_aws_account_id() {
    aws sts get-caller-identity --query Account --output text
}

# Create S3 bucket for deployment artifacts
create_s3_bucket() {
    local bucket_name="${PROJECT_NAME}-deployments-${ENVIRONMENT}-$(get_aws_account_id)"
    
    log_info "Creating S3 bucket for deployment artifacts: $bucket_name"
    
    # Check if bucket exists
    if aws s3api head-bucket --bucket "$bucket_name" 2>/dev/null; then
        log_info "S3 bucket $bucket_name already exists"
    else
        # Create bucket
        if [[ "$AWS_REGION" == "us-east-1" ]]; then
            aws s3api create-bucket --bucket "$bucket_name"
        else
            aws s3api create-bucket --bucket "$bucket_name" --region "$AWS_REGION" \
                --create-bucket-configuration LocationConstraint="$AWS_REGION"
        fi
        
        # Enable versioning
        aws s3api put-bucket-versioning --bucket "$bucket_name" \
            --versioning-configuration Status=Enabled
        
        # Set bucket policy for public read (if needed)
        aws s3api put-bucket-policy --bucket "$bucket_name" --policy '{
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "PublicReadGetObject",
                    "Effect": "Allow",
                    "Principal": "*",
                    "Action": "s3:GetObject",
                    "Resource": "arn:aws:s3:::'"$bucket_name"'/*"
                }
            ]
        }'
        
        log_success "S3 bucket $bucket_name created"
    fi
    
    echo "$bucket_name"
}

# Create S3 bucket for images
create_images_bucket() {
    local bucket_name="${PROJECT_NAME}-images-${ENVIRONMENT}-$(get_aws_account_id)"
    
    log_info "Creating S3 bucket for images: $bucket_name"
    
    # Check if bucket exists
    if aws s3api head-bucket --bucket "$bucket_name" 2>/dev/null; then
        log_info "S3 bucket $bucket_name already exists"
    else
        # Create bucket
        if [[ "$AWS_REGION" == "us-east-1" ]]; then
            aws s3api create-bucket --bucket "$bucket_name"
        else
            aws s3api create-bucket --bucket "$bucket_name" --region "$AWS_REGION" \
                --create-bucket-configuration LocationConstraint="$AWS_REGION"
        fi
        
        # Enable CORS
        aws s3api put-bucket-cors --bucket "$bucket_name" --cors-configuration '{
            "CORSRules": [
                {
                    "AllowedHeaders": ["*"],
                    "AllowedMethods": ["GET", "PUT", "POST", "DELETE"],
                    "AllowedOrigins": ["*"],
                    "ExposeHeaders": ["ETag"]
                }
            ]
        }'
        
        # Enable versioning
        aws s3api put-bucket-versioning --bucket "$bucket_name" \
            --versioning-configuration Status=Enabled
        
        log_success "S3 bucket $bucket_name created with CORS enabled"
    fi
    
    echo "$bucket_name"
}

# Package Lambda function
package_lambda_function() {
    local function_name="$1"
    local function_dir="$2"
    local package_name="${function_name}-${ENVIRONMENT}.zip"
    
    log_info "Packaging Lambda function: $function_name"
    
    # Create temporary directory
    local temp_dir=$(mktemp -d)
    local package_path="$temp_dir/$package_name"
    
    # Copy function code
    cp -r "$function_dir"/* "$temp_dir/"
    
    # Install dependencies if requirements.txt exists
    if [[ -f "$function_dir/requirements.txt" ]]; then
        log_info "Installing dependencies for $function_name"
        pip install -r "$function_dir/requirements.txt" -t "$temp_dir/" --quiet
    fi
    
    # Create zip package
    cd "$temp_dir"
    zip -r "$package_name" . -q
    cd "$SCRIPT_DIR"
    
    # Move package to deployment directory
    mkdir -p "deployments"
    mv "$temp_dir/$package_name" "deployments/"
    
    # Cleanup
    rm -rf "$temp_dir"
    
    log_success "Lambda function $function_name packaged: deployments/$package_name"
    echo "deployments/$package_name"
}

# Deploy Lambda function
deploy_lambda_function() {
    local function_name="$1"
    local package_path="$2"
    local role_arn="$3"
    local environment_vars="$4"
    
    log_info "Deploying Lambda function: $function_name"
    
    # Check if function exists
    if aws lambda get-function --function-name "$function_name" &> /dev/null; then
        log_info "Updating existing Lambda function: $function_name"
        aws lambda update-function-code \
            --function-name "$function_name" \
            --zip-file "fileb://$package_path"
        
        aws lambda update-function-configuration \
            --function-name "$function_name" \
            --environment Variables="$environment_vars" \
            --timeout 60 \
            --memory-size 512
    else
        log_info "Creating new Lambda function: $function_name"
        aws lambda create-function \
            --function-name "$function_name" \
            --runtime python3.11 \
            --role "$role_arn" \
            --handler lambda_function.lambda_handler \
            --zip-file "fileb://$package_path" \
            --timeout 60 \
            --memory-size 512 \
            --environment Variables="$environment_vars"
    fi
    
    log_success "Lambda function $function_name deployed"
}

# Create IAM role for Lambda
create_lambda_role() {
    local role_name="${PROJECT_NAME}-lambda-role-${ENVIRONMENT}"
    
    log_info "Creating IAM role: $role_name"
    
    # Check if role exists
    if aws iam get-role --role-name "$role_name" &> /dev/null; then
        log_info "IAM role $role_name already exists"
    else
        # Create role
        aws iam create-role \
            --role-name "$role_name" \
            --assume-role-policy-document '{
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {
                            "Service": "lambda.amazonaws.com"
                        },
                        "Action": "sts:AssumeRole"
                    }
                ]
            }'
        
        # Attach policies
        aws iam attach-role-policy \
            --role-name "$role_name" \
            --policy-arn "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
        
        aws iam attach-role-policy \
            --role-name "$role_name" \
            --policy-arn "arn:aws:iam::aws:policy/AmazonS3FullAccess"
        
        aws iam attach-role-policy \
            --role-name "$role_name" \
            --policy-arn "arn:aws:iam::aws:policy/AmazonRekognitionFullAccess"
        
        aws iam attach-role-policy \
            --role-name "$role_name" \
            --policy-arn "arn:aws:iam::aws:policy/AmazonBedrockFullAccess"
        
        aws iam attach-role-policy \
            --role-name "$role_name" \
            --policy-arn "arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess"
        
        # Wait for role to be available
        log_info "Waiting for IAM role to be available..."
        sleep 10
        
        log_success "IAM role $role_name created"
    fi
    
    # Get role ARN
    aws iam get-role --role-name "$role_name" --query Role.Arn --output text
}

# Create API Gateway
create_api_gateway() {
    local api_name="${PROJECT_NAME}-api-${ENVIRONMENT}"
    
    log_info "Creating API Gateway: $api_name"
    
    # Check if API exists
    local api_id=$(aws apigateway get-rest-apis --query "items[?name=='$api_name'].id" --output text)
    
    if [[ -n "$api_id" && "$api_id" != "None" ]]; then
        log_info "API Gateway $api_name already exists with ID: $api_id"
    else
        # Create API
        api_id=$(aws apigateway create-rest-api \
            --name "$api_name" \
            --description "Accessibility Checker API" \
            --query id --output text)
        
        log_success "API Gateway $api_name created with ID: $api_id"
    fi
    
    echo "$api_id"
}

# Configure API Gateway CORS
configure_api_cors() {
    local api_id="$1"
    local resource_id="$2"
    
    log_info "Configuring CORS for API Gateway resource: $resource_id"
    
    # Enable CORS
    aws apigateway put-method-response \
        --rest-api-id "$api_id" \
        --resource-id "$resource_id" \
        --http-method OPTIONS \
        --status-code 200 \
        --response-parameters method.response.header.Access-Control-Allow-Headers=false,method.response.header.Access-Control-Allow-Methods=false,method.response.header.Access-Control-Allow-Origin=false
    
    aws apigateway put-integration-response \
        --rest-api-id "$api_id" \
        --resource-id "$resource_id" \
        --http-method OPTIONS \
        --status-code 200 \
        --response-parameters '{"method.response.header.Access-Control-Allow-Headers":"'"'"'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"'"'","method.response.header.Access-Control-Allow-Methods":"'"'"'GET,POST,PUT,DELETE,OPTIONS'"'"'","method.response.header.Access-Control-Allow-Origin":"'"'"'*'"'"'"}'
    
    log_success "CORS configured for API Gateway"
}

# Create API Gateway resource and method
create_api_resource() {
    local api_id="$1"
    local parent_id="$2"
    local path_part="$3"
    local lambda_function_name="$4"
    local http_method="$5"
    
    log_info "Creating API Gateway resource: $path_part"
    
    # Get root resource ID if not provided
    if [[ -z "$parent_id" ]]; then
        parent_id=$(aws apigateway get-resources --rest-api-id "$api_id" --query "items[?path=='/'].id" --output text)
    fi
    
    # Create resource
    local resource_id=$(aws apigateway create-resource \
        --rest-api-id "$api_id" \
        --parent-id "$parent_id" \
        --path-part "$path_part" \
        --query id --output text)
    
    # Create method
    aws apigateway put-method \
        --rest-api-id "$api_id" \
        --resource-id "$resource_id" \
        --http-method "$http_method" \
        --authorization-type NONE
    
    # Create integration
    aws apigateway put-integration \
        --rest-api-id "$api_id" \
        --resource-id "$resource_id" \
        --http-method "$http_method" \
        --type AWS_PROXY \
        --integration-http-method POST \
        --uri "arn:aws:apigateway:$AWS_REGION:lambda:path/2015-03-31/functions/arn:aws:lambda:$AWS_REGION:$(get_aws_account_id):function:$lambda_function_name/invocations"
    
    # Add permission for API Gateway to invoke Lambda
    aws lambda add-permission \
        --function-name "$lambda_function_name" \
        --statement-id "api-gateway-invoke-$(date +%s)" \
        --action lambda:InvokeFunction \
        --principal apigateway.amazonaws.com \
        --source-arn "arn:aws:apigateway:$AWS_REGION::/restapis/$api_id/*/*"
    
    log_success "API Gateway resource $path_part created"
    echo "$resource_id"
}

# Deploy API Gateway stage
deploy_api_stage() {
    local api_id="$1"
    local stage_name="${ENVIRONMENT}"
    
    log_info "Deploying API Gateway stage: $stage_name"
    
    aws apigateway create-deployment \
        --rest-api-id "$api_id" \
        --stage-name "$stage_name" \
        --stage-description "Deployment for $ENVIRONMENT environment"
    
    log_success "API Gateway stage $stage_name deployed"
}

# Create CloudWatch log groups
create_cloudwatch_logs() {
    local function_names=("$@")
    
    log_info "Creating CloudWatch log groups for Lambda functions"
    
    for function_name in "${function_names[@]}"; do
        local log_group_name="/aws/lambda/$function_name"
        
        if aws logs describe-log-groups --log-group-name-prefix "$log_group_name" --query 'logGroups[0].logGroupName' --output text | grep -q "$log_group_name"; then
            log_info "CloudWatch log group $log_group_name already exists"
        else
            aws logs create-log-group --log-group-name "$log_group_name"
            aws logs put-retention-policy --log-group-name "$log_group_name" --retention-in-days 14
            log_success "CloudWatch log group $log_group_name created"
        fi
    done
}

# Deploy Lambda backend
deploy_lambda_backend() {
    log_info "Deploying Lambda backend for $ENVIRONMENT environment"
    
    # Create S3 buckets
    local images_bucket=$(create_images_bucket)
    local deployments_bucket=$(create_s3_bucket)
    
    # Create IAM role
    local role_arn=$(create_lambda_role)
    
    # Environment variables
    local environment_vars="S3_BUCKET_NAME=$images_bucket,AWS_REGION=$AWS_REGION,BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0"
    
    # Lambda functions to deploy
    local functions=(
        "presigned-url-generator-$ENVIRONMENT"
        "rekognition-handler-$ENVIRONMENT"
        "llm-handler-$ENVIRONMENT"
        "orchestrator-handler-$ENVIRONMENT"
    )
    
    local function_dirs=(
        "lambdas/presigned_url"
        "lambdas/rekognition_handler"
        "lambdas/llm_handler"
        "lambdas/orchestrator"
    )
    
    # Package and deploy Lambda functions
    for i in "${!functions[@]}"; do
        local function_name="${functions[$i]}"
        local function_dir="${function_dirs[$i]}"
        
        log_info "Processing Lambda function: $function_name"
        
        # Package function
        local package_path=$(package_lambda_function "$function_name" "$function_dir")
        
        # Deploy function
        deploy_lambda_function "$function_name" "$package_path" "$role_arn" "$environment_vars"
    done
    
    # Create API Gateway
    local api_id=$(create_api_gateway)
    
    # Create API resources
    local presigned_resource_id=$(create_api_resource "$api_id" "" "presigned-url" "presigned-url-generator-$ENVIRONMENT" "POST")
    local analyze_resource_id=$(create_api_resource "$api_id" "" "analyze" "orchestrator-handler-$ENVIRONMENT" "POST")
    
    # Configure CORS
    configure_api_cors "$api_id" "$presigned_resource_id"
    configure_api_cors "$api_id" "$analyze_resource_id"
    
    # Deploy API Gateway
    deploy_api_stage "$api_id"
    
    # Create CloudWatch log groups
    create_cloudwatch_logs "${functions[@]}"
    
    # Get API Gateway URL
    local api_url="https://$api_id.execute-api.$AWS_REGION.amazonaws.com/$ENVIRONMENT"
    
    log_success "Lambda backend deployed successfully!"
    echo ""
    echo "🚀 API Gateway URL: $api_url"
    echo "📡 Endpoints:"
    echo "   POST $api_url/presigned-url"
    echo "   POST $api_url/analyze"
    echo ""
    echo "📊 AWS Resources Created:"
    echo "   S3 Bucket (Images): $images_bucket"
    echo "   S3 Bucket (Deployments): $deployments_bucket"
    echo "   Lambda Functions: ${functions[*]}"
    echo "   API Gateway: $api_id"
    echo ""
}

# Deploy Express.js backend
deploy_express_backend() {
    log_info "Deploying Express.js backend for $ENVIRONMENT environment"
    
    # Check if we're in the express-backend directory
    if [[ ! -f "express-backend/package.json" ]]; then
        log_error "Express.js backend not found. Please run from the project root."
        exit 1
    fi
    
    cd express-backend
    
    # Check if dependencies are installed
    if [[ ! -d "node_modules" ]]; then
        log_info "Installing Express.js dependencies..."
        npm install
    fi
    
    # Check if .env file exists
    if [[ ! -f ".env" ]]; then
        log_warning ".env file not found. Creating from template..."
        cp env.example .env
        log_warning "Please edit .env file with your OpenAI API key before deploying."
    fi
    
    # Create deployment package
    log_info "Creating Express.js deployment package..."
    mkdir -p ../deployments
    zip -r "../deployments/express-backend-${ENVIRONMENT}.zip" . -x "node_modules/*" ".git/*" "*.log" "tmp/*"
    
    cd ..
    
    log_success "Express.js backend packaged successfully!"
    echo ""
    echo "📦 Deployment package: deployments/express-backend-${ENVIRONMENT}.zip"
    echo ""
    echo "🚀 Deploy to your preferred platform:"
    echo "   Railway: railway up"
    echo "   Render: Connect GitHub repo to Render"
    echo "   Vercel: vercel --prod"
    echo "   Heroku: git push heroku main"
    echo ""
    echo "📋 Don't forget to:"
    echo "   1. Set OPENAI_API_KEY environment variable"
    echo "   2. Configure CORS for your frontend domain"
    echo "   3. Set up monitoring and logging"
    echo ""
}

# Main deployment function
main() {
    echo "🚀 Accessibility Checker API Deployment Script"
    echo "================================================"
    echo "Environment: $ENVIRONMENT"
    echo "Backend Type: $BACKEND_TYPE"
    echo "AWS Region: $AWS_REGION"
    echo ""
    
    # Check prerequisites
    check_prerequisites
    
    # Deploy based on backend type
    if [[ "$BACKEND_TYPE" == "lambda" ]]; then
        deploy_lambda_backend
    else
        deploy_express_backend
    fi
    
    log_success "Deployment completed successfully!"
    echo ""
    echo "🎉 Your Accessibility Checker API is ready!"
    echo ""
    echo "📚 Next steps:"
    echo "   1. Test your API endpoints"
    echo "   2. Set up monitoring and alerting"
    echo "   3. Configure custom domain (optional)"
    echo "   4. Set up CI/CD pipeline"
    echo ""
}

# Run main function
main "$@"
