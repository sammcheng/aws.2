#!/bin/bash

# Express.js Backend Deployment Script
# Quick deployment for Express.js backend to various platforms
# Usage: ./deploy-express.sh [platform] [environment]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PLATFORM="${1:-railway}"
ENVIRONMENT="${2:-dev}"
PROJECT_NAME="accessibility-checker-express"

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
    log_info "Checking prerequisites for $PLATFORM deployment..."
    
    case $PLATFORM in
        railway)
            if ! command -v railway &> /dev/null; then
                log_error "Railway CLI is not installed. Please install it first:"
                echo "npm install -g @railway/cli"
                exit 1
            fi
            ;;
        vercel)
            if ! command -v vercel &> /dev/null; then
                log_error "Vercel CLI is not installed. Please install it first:"
                echo "npm install -g vercel"
                exit 1
            fi
            ;;
        heroku)
            if ! command -v heroku &> /dev/null; then
                log_error "Heroku CLI is not installed. Please install it first:"
                echo "Visit: https://devcenter.heroku.com/articles/heroku-cli"
                exit 1
            fi
            ;;
        render)
            log_info "Render deployment requires GitHub integration"
            ;;
        *)
            log_error "Unsupported platform: $PLATFORM"
            echo "Supported platforms: railway, vercel, heroku, render"
            exit 1
            ;;
    esac
    
    # Check if express-backend directory exists
    if [[ ! -d "express-backend" ]]; then
        log_error "Express.js backend directory not found. Please run from project root."
        exit 1
    fi
    
    # Check if package.json exists
    if [[ ! -f "express-backend/package.json" ]]; then
        log_error "package.json not found in express-backend directory"
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Prepare Express.js backend
prepare_express_backend() {
    log_info "Preparing Express.js backend for deployment..."
    
    cd express-backend
    
    # Check if .env file exists
    if [[ ! -f ".env" ]]; then
        log_warning ".env file not found. Creating from template..."
        cp env.example .env
        log_warning "Please edit .env file with your OpenAI API key before deploying."
    fi
    
    # Install dependencies
    log_info "Installing dependencies..."
    npm install --production
    
    # Create deployment package
    log_info "Creating deployment package..."
    mkdir -p ../deployments
    zip -r "../deployments/express-backend-${ENVIRONMENT}.zip" . \
        -x "node_modules/*" ".git/*" "*.log" "tmp/*" "tests/*" "*.test.js"
    
    cd ..
    
    log_success "Express.js backend prepared for deployment"
}

# Deploy to Railway
deploy_railway() {
    log_info "Deploying to Railway..."
    
    cd express-backend
    
    # Check if already logged in
    if ! railway whoami &> /dev/null; then
        log_info "Please log in to Railway..."
        railway login
    fi
    
    # Deploy
    log_info "Deploying to Railway..."
    railway up --detach
    
    # Get deployment URL
    local url=$(railway domain)
    
    log_success "Deployed to Railway successfully!"
    echo "🚀 URL: https://$url"
    
    cd ..
}

# Deploy to Vercel
deploy_vercel() {
    log_info "Deploying to Vercel..."
    
    cd express-backend
    
    # Check if already logged in
    if ! vercel whoami &> /dev/null; then
        log_info "Please log in to Vercel..."
        vercel login
    fi
    
    # Deploy
    log_info "Deploying to Vercel..."
    vercel --prod
    
    # Get deployment URL
    local url=$(vercel ls --json | jq -r '.[0].url')
    
    log_success "Deployed to Vercel successfully!"
    echo "🚀 URL: https://$url"
    
    cd ..
}

# Deploy to Heroku
deploy_heroku() {
    log_info "Deploying to Heroku..."
    
    cd express-backend
    
    # Check if Heroku app exists
    if ! heroku apps:info &> /dev/null; then
        log_info "Creating Heroku app..."
        heroku create "${PROJECT_NAME}-${ENVIRONMENT}"
    fi
    
    # Set environment variables
    log_info "Setting environment variables..."
    heroku config:set NODE_ENV=production
    heroku config:set LOG_LEVEL=info
    
    # Deploy
    log_info "Deploying to Heroku..."
    git add .
    git commit -m "Deploy to Heroku" || true
    git push heroku main
    
    # Get deployment URL
    local url=$(heroku apps:info --json | jq -r '.app.web_url')
    
    log_success "Deployed to Heroku successfully!"
    echo "🚀 URL: $url"
    
    cd ..
}

# Deploy to Render
deploy_render() {
    log_info "Render deployment requires GitHub integration..."
    echo ""
    echo "📋 Manual deployment steps for Render:"
    echo "1. Push your code to GitHub"
    echo "2. Go to https://render.com"
    echo "3. Connect your GitHub repository"
    echo "4. Create a new Web Service"
    echo "5. Configure:"
    echo "   - Build Command: npm install"
    echo "   - Start Command: npm start"
    echo "   - Environment: Node"
    echo "6. Set environment variables:"
    echo "   - OPENAI_API_KEY=your_openai_api_key_here"
    echo "   - NODE_ENV=production"
    echo "7. Deploy!"
    echo ""
    echo "📄 Configuration files already created:"
    echo "   - render.yaml (Render configuration)"
    echo "   - package.json (Dependencies)"
    echo "   - server.js (Main application)"
    echo ""
}

# Test deployment
test_deployment() {
    local url="$1"
    
    if [[ -z "$url" ]]; then
        log_warning "No URL provided for testing"
        return
    fi
    
    log_info "Testing deployment at $url..."
    
    # Test health endpoint
    if curl -s "$url/health" | grep -q "healthy"; then
        log_success "Health check passed"
    else
        log_warning "Health check failed"
    fi
    
    # Test API endpoints
    log_info "Testing API endpoints..."
    echo "Health: $url/health"
    echo "Upload: $url/api/upload"
    echo "Analyze: $url/api/analyze"
    echo "Upload & Analyze: $url/api/upload-and-analyze"
}

# Main deployment function
main() {
    echo "🚀 Express.js Backend Deployment Script"
    echo "========================================"
    echo "Platform: $PLATFORM"
    echo "Environment: $ENVIRONMENT"
    echo ""
    
    # Check prerequisites
    check_prerequisites
    
    # Prepare backend
    prepare_express_backend
    
    # Deploy based on platform
    case $PLATFORM in
        railway)
            deploy_railway
            ;;
        vercel)
            deploy_vercel
            ;;
        heroku)
            deploy_heroku
            ;;
        render)
            deploy_render
            ;;
        *)
            log_error "Unsupported platform: $PLATFORM"
            exit 1
            ;;
    esac
    
    log_success "Deployment completed!"
    echo ""
    echo "🎉 Your Express.js backend is ready!"
    echo ""
    echo "📚 Next steps:"
    echo "1. Set your OpenAI API key in environment variables"
    echo "2. Test your API endpoints"
    echo "3. Configure CORS for your frontend"
    echo "4. Set up monitoring and logging"
    echo ""
    echo "📖 Documentation: express-backend/README.md"
    echo "🔧 Configuration: express-backend/env.example"
    echo ""
}

# Run main function
main "$@"
