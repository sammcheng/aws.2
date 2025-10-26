#!/bin/bash

# AWS Lambda Backend Deployment Script
# Automated deployment for Lambda functions using AWS CLI
# Usage: ./deploy-lambda.sh [environment] [options]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT="${1:-dev}"
STACK_NAME="accessibility-checker-${ENVIRONMENT}"
AWS_REGION="${AWS_REGION:-us-east-1}"

# Parse options
SKIP_SAM=false
SKIP_PACKAGING=false
SKIP_DEPLOYMENT=false
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-sam)
            SKIP_SAM=true
            shift
            ;;
        --skip-packaging)
            SKIP_PACKAGING=true
            shift
            ;;
        --skip-deployment)
            SKIP_DEPLOYMENT=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --help)
            echo "Usage: $0 [environment] [options]"
            echo "Environments: dev, prod"
            echo "Options:"
            echo "  --skip-sam         Skip SAM build"
            echo "  --skip-packaging   Skip Lambda packaging"
            echo "  --skip-deployment  Skip actual deployment"
            echo "  --verbose         Enable verbose output"
            echo "  --help            Show this help"
            exit 0
            ;;
        *)
            if [[ "$1" != "dev" && "$1" != "prod" ]]; then
                ENVIRONMENT="$1"
            fi
            shift
            ;;
    esac
done

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

log_verbose() {
    if [[ "$VERBOSE" == "true" ]]; then
        echo -e "${BLUE}[VERBOSE]${NC} $1"
    fi
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        log_error "AWS CLI is not installed. Please install it first."
        exit 1
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        log_error "AWS CLI is not configured. Please run 'aws configure' first."
        exit 1
    fi
    
    # Check SAM CLI
    if [[ "$SKIP_SAM" == "false" ]]; then
        if ! command -v sam &> /dev/null; then
            log_error "SAM CLI is not installed. Please install it first:"
            echo "pip install aws-sam-cli"
            exit 1
        fi
    fi
    
    # Check jq
    if ! command -v jq &> /dev/null; then
        log_error "jq is not installed. Please install it first."
        exit 1
    fi
    
    # Check zip
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

# Create S3 bucket for SAM artifacts
create_sam_bucket() {
    local bucket_name="sam-deployments-${ENVIRONMENT}-$(get_aws_account_id)"
    
    log_info "Creating S3 bucket for SAM artifacts: $bucket_name"
    
    if aws s3api head-bucket --bucket "$bucket_name" 2>/dev/null; then
        log_info "S3 bucket $bucket_name already exists"
    else
        if [[ "$AWS_REGION" == "us-east-1" ]]; then
            aws s3api create-bucket --bucket "$bucket_name"
        else
            aws s3api create-bucket --bucket "$bucket_name" --region "$AWS_REGION" \
                --create-bucket-configuration LocationConstraint="$AWS_REGION"
        fi
        
        log_success "S3 bucket $bucket_name created"
    fi
    
    echo "$bucket_name"
}

# Build SAM application
build_sam_application() {
    if [[ "$SKIP_SAM" == "true" ]]; then
        log_info "Skipping SAM build"
        return
    fi
    
    log_info "Building SAM application..."
    
    # Check if template.yaml exists
    if [[ ! -f "template.yaml" ]]; then
        log_error "template.yaml not found. Please run from project root."
        exit 1
    fi
    
    # Build SAM application
    sam build --use-container
    
    log_success "SAM application built successfully"
}

# Package SAM application
package_sam_application() {
    if [[ "$SKIP_PACKAGING" == "true" ]]; then
        log_info "Skipping SAM packaging"
        return
    fi
    
    log_info "Packaging SAM application..."
    
    local sam_bucket=$(create_sam_bucket)
    
    # Package SAM application
    sam package \
        --s3-bucket "$sam_bucket" \
        --output-template-file "packaged-template.yaml" \
        --region "$AWS_REGION"
    
    log_success "SAM application packaged successfully"
}

# Deploy SAM application
deploy_sam_application() {
    if [[ "$SKIP_DEPLOYMENT" == "true" ]]; then
        log_info "Skipping SAM deployment"
        return
    fi
    
    log_info "Deploying SAM application..."
    
    # Deploy with guided parameters for first time
    if [[ ! -f "samconfig.toml" ]]; then
        log_info "First deployment - guided setup"
        sam deploy --guided \
            --stack-name "$STACK_NAME" \
            --s3-bucket "$(create_sam_bucket)" \
            --region "$AWS_REGION" \
            --capabilities CAPABILITY_IAM \
            --parameter-overrides Environment="$ENVIRONMENT"
    else
        log_info "Deploying with existing configuration"
        sam deploy
    fi
    
    log_success "SAM application deployed successfully"
}

# Get deployment outputs
get_deployment_outputs() {
    log_info "Getting deployment outputs..."
    
    # Get stack outputs
    local outputs=$(aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --query 'Stacks[0].Outputs' \
        --output json)
    
    if [[ "$outputs" == "null" ]]; then
        log_warning "No outputs found for stack $STACK_NAME"
        return
    fi
    
    # Parse outputs
    local api_url=$(echo "$outputs" | jq -r '.[] | select(.OutputKey=="AccessibilityCheckerAPI") | .OutputValue')
    local s3_bucket=$(echo "$outputs" | jq -r '.[] | select(.OutputKey=="S3Bucket") | .OutputValue')
    local cache_table=$(echo "$outputs" | jq -r '.[] | select(.OutputKey=="CacheTable") | .OutputValue')
    
    log_success "Deployment outputs retrieved"
    echo ""
    echo "🚀 Deployment Information:"
    echo "=========================="
    echo "Stack Name: $STACK_NAME"
    echo "Environment: $ENVIRONMENT"
    echo "Region: $AWS_REGION"
    echo ""
    
    if [[ -n "$api_url" ]]; then
        echo "📡 API Gateway URL: $api_url"
        echo "   Endpoints:"
        echo "   POST $api_url/presigned-url"
        echo "   POST $api_url/analyze"
    fi
    
    if [[ -n "$s3_bucket" ]]; then
        echo "📦 S3 Bucket: $s3_bucket"
    fi
    
    if [[ -n "$cache_table" ]]; then
        echo "💾 Cache Table: $cache_table"
    fi
    
    echo ""
}

# Test deployment
test_deployment() {
    local api_url="$1"
    
    if [[ -z "$api_url" ]]; then
        log_warning "No API URL provided for testing"
        return
    fi
    
    log_info "Testing deployment..."
    
    # Test health endpoint (if available)
    if curl -s "$api_url/health" &> /dev/null; then
        log_success "Health check passed"
    else
        log_warning "Health check failed or not available"
    fi
    
    # Test presigned URL endpoint
    log_info "Testing presigned URL endpoint..."
    local response=$(curl -s -X POST "$api_url/presigned-url" \
        -H "Content-Type: application/json" \
        -d '{"filename":"test.jpg","content_type":"image/jpeg"}' \
        -w "%{http_code}")
    
    if [[ "$response" == *"200" ]]; then
        log_success "Presigned URL endpoint working"
    else
        log_warning "Presigned URL endpoint test failed"
    fi
    
    echo ""
    echo "🧪 Test your API:"
    echo "curl -X POST $api_url/presigned-url \\"
    echo "  -H 'Content-Type: application/json' \\"
    echo "  -d '{\"filename\":\"test.jpg\",\"content_type\":\"image/jpeg\"}'"
    echo ""
}

# Cleanup function
cleanup() {
    log_info "Cleaning up temporary files..."
    
    # Remove packaged template
    if [[ -f "packaged-template.yaml" ]]; then
        rm -f "packaged-template.yaml"
    fi
    
    # Remove .aws-sam directory
    if [[ -d ".aws-sam" ]]; then
        rm -rf ".aws-sam"
    fi
    
    log_success "Cleanup completed"
}

# Main deployment function
main() {
    echo "🚀 AWS Lambda Backend Deployment Script"
    echo "======================================="
    echo "Environment: $ENVIRONMENT"
    echo "Stack Name: $STACK_NAME"
    echo "Region: $AWS_REGION"
    echo ""
    
    # Check prerequisites
    check_prerequisites
    
    # Build SAM application
    build_sam_application
    
    # Package SAM application
    package_sam_application
    
    # Deploy SAM application
    deploy_sam_application
    
    # Get deployment outputs
    get_deployment_outputs
    
    # Test deployment
    local api_url=$(aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --query 'Stacks[0].Outputs[?OutputKey==`AccessibilityCheckerAPI`].OutputValue' \
        --output text 2>/dev/null || echo "")
    
    if [[ -n "$api_url" ]]; then
        test_deployment "$api_url"
    fi
    
    # Cleanup
    cleanup
    
    log_success "Lambda backend deployment completed!"
    echo ""
    echo "🎉 Your Lambda backend is ready!"
    echo ""
    echo "📚 Next steps:"
    echo "1. Test your API endpoints"
    echo "2. Set up monitoring and alerting"
    echo "3. Configure custom domain (optional)"
    echo "4. Set up CI/CD pipeline"
    echo ""
    echo "📖 Documentation: README.md"
    echo "🔧 Configuration: template.yaml"
    echo ""
}

# Trap to ensure cleanup on exit
trap cleanup EXIT

# Run main function
main "$@"
