# Deployment Guide

Comprehensive deployment guide for the Accessibility Checker API with both AWS Lambda and Express.js backends.

## 🚀 Quick Start

### Prerequisites
- AWS CLI configured (for Lambda backend)
- Node.js 18+ (for Express.js backend)
- Git repository access

### One-Command Deployment

#### AWS Lambda Backend
```bash
# Deploy to development
./deploy.sh dev lambda

# Deploy to production
./deploy.sh prod lambda
```

#### Express.js Backend
```bash
# Deploy to Railway
./deploy-express.sh railway dev

# Deploy to Vercel
./deploy-express.sh vercel dev

# Deploy to Heroku
./deploy-express.sh heroku dev
```

## 📋 Deployment Options

### AWS Lambda Backend

#### Features
- ✅ Serverless architecture
- ✅ Auto-scaling
- ✅ Pay-per-request pricing
- ✅ AWS service integration
- ✅ Enterprise-grade security

#### Prerequisites
- AWS CLI configured
- SAM CLI installed
- AWS account with appropriate permissions

#### Deployment Steps
1. **Check Prerequisites**
   ```bash
   aws sts get-caller-identity
   sam --version
   ```

2. **Deploy Lambda Backend**
   ```bash
   ./deploy.sh dev lambda
   ```

3. **Test Deployment**
   ```bash
   curl -X POST https://your-api-id.execute-api.us-east-1.amazonaws.com/dev/presigned-url \
     -H "Content-Type: application/json" \
     -d '{"filename":"test.jpg","content_type":"image/jpeg"}'
   ```

#### Advanced Options
```bash
# Skip SAM build
./deploy-lambda.sh dev --skip-sam

# Skip packaging
./deploy-lambda.sh dev --skip-packaging

# Skip deployment
./deploy-lambda.sh dev --skip-deployment

# Verbose output
./deploy-lambda.sh dev --verbose
```

### Express.js Backend

#### Features
- ✅ Fast deployment (5 minutes)
- ✅ Easy debugging
- ✅ Simple architecture
- ✅ Multiple platform options
- ✅ Cost-effective

#### Platform Options

##### Railway (Recommended)
```bash
# Install Railway CLI
npm install -g @railway/cli

# Deploy
./deploy-express.sh railway dev
```

##### Vercel
```bash
# Install Vercel CLI
npm install -g vercel

# Deploy
./deploy-express.sh vercel dev
```

##### Heroku
```bash
# Install Heroku CLI
# Visit: https://devcenter.heroku.com/articles/heroku-cli

# Deploy
./deploy-express.sh heroku dev
```

##### Render
```bash
# Manual deployment via GitHub
./deploy-express.sh render dev
```

## 🔧 Configuration

### Environment Variables

#### AWS Lambda Backend
```bash
# Required
AWS_REGION=us-east-1
S3_BUCKET_NAME=your-bucket-name
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0

# Optional
CACHE_TABLE_NAME=accessibility-checker-cache-dev
LOG_LEVEL=INFO
```

#### Express.js Backend
```bash
# Required
OPENAI_API_KEY=your_openai_api_key_here

# Optional
PORT=3000
NODE_ENV=production
LOG_LEVEL=info
ALLOWED_ORIGINS=*
RATE_LIMIT_MAX_REQUESTS=100
MAX_FILE_SIZE=10485760
```

### Deployment Configuration

The `deployment-config.yaml` file contains all deployment settings:

```yaml
# Environment-specific configurations
environments:
  dev:
    aws:
      region: "us-east-1"
      lambda:
        timeout: 60
        memory_size: 512
        reserved_concurrency:
          presigned_url: 5
          rekognition: 10
          llm: 3
          orchestrator: 8
  
  prod:
    aws:
      region: "us-east-1"
      lambda:
        timeout: 60
        memory_size: 512
        reserved_concurrency:
          presigned_url: 10
          rekognition: 20
          llm: 5
          orchestrator: 15
```

## 🛠️ Deployment Scripts

### Main Deployment Script (`deploy.sh`)

#### Usage
```bash
./deploy.sh [environment] [backend_type]
```

#### Examples
```bash
# Deploy Lambda backend to development
./deploy.sh dev lambda

# Deploy Express.js backend to production
./deploy.sh prod express
```

#### Features
- ✅ Prerequisites checking
- ✅ S3 bucket creation
- ✅ Lambda function packaging
- ✅ API Gateway setup
- ✅ CloudWatch log groups
- ✅ CORS configuration
- ✅ Environment-specific settings

### Express.js Deployment Script (`deploy-express.sh`)

#### Usage
```bash
./deploy-express.sh [platform] [environment]
```

#### Examples
```bash
# Deploy to Railway
./deploy-express.sh railway dev

# Deploy to Vercel
./deploy-express.sh vercel prod
```

#### Supported Platforms
- **Railway** - Easiest deployment
- **Vercel** - Great for APIs
- **Heroku** - Full-featured platform
- **Render** - Free tier available

### Lambda Deployment Script (`deploy-lambda.sh`)

#### Usage
```bash
./deploy-lambda.sh [environment] [options]
```

#### Examples
```bash
# Deploy to development
./deploy-lambda.sh dev

# Deploy with verbose output
./deploy-lambda.sh dev --verbose

# Skip SAM build
./deploy-lambda.sh dev --skip-sam
```

#### Options
- `--skip-sam` - Skip SAM build
- `--skip-packaging` - Skip Lambda packaging
- `--skip-deployment` - Skip actual deployment
- `--verbose` - Enable verbose output
- `--help` - Show help

## 📊 Platform Comparison

| Feature | AWS Lambda | Express.js |
|---------|------------|------------|
| **Setup Time** | 30+ minutes | 5 minutes |
| **Debugging** | Complex | Easy |
| **Cost** | Pay per request | Fixed monthly |
| **Scaling** | Automatic | Manual |
| **Dependencies** | Complex | Simple |
| **Local Development** | Requires AWS | Standard Node.js |
| **Hackathon Ready** | ⭐⭐ | ⭐⭐⭐⭐⭐ |

## 🎯 Hackathon Recommendations

### For Speed (Express.js)
```bash
# Quick deployment to Railway
./deploy-express.sh railway dev

# Set OpenAI API key
# Test immediately
```

### For Production (AWS Lambda)
```bash
# Full AWS deployment
./deploy.sh prod lambda

# Enterprise-grade features
# Auto-scaling
# Pay-per-request
```

## 🔍 Testing Deployments

### Health Checks
```bash
# Lambda backend
curl https://your-api-id.execute-api.us-east-1.amazonaws.com/dev/health

# Express.js backend
curl https://your-app.railway.app/health
```

### API Testing
```bash
# Test presigned URL
curl -X POST https://your-api.com/api/presigned-url \
  -H "Content-Type: application/json" \
  -d '{"filename":"test.jpg","content_type":"image/jpeg"}'

# Test analysis
curl -X POST https://your-api.com/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"images":[{"filename":"test.jpg","base64":"..."}]}'
```

## 🚨 Troubleshooting

### Common Issues

#### AWS Lambda Backend
```bash
# Check AWS credentials
aws sts get-caller-identity

# Check SAM CLI
sam --version

# Check stack status
aws cloudformation describe-stacks --stack-name accessibility-checker-dev
```

#### Express.js Backend
```bash
# Check Node.js version
node --version

# Check dependencies
npm list

# Check environment variables
echo $OPENAI_API_KEY
```

### Debug Commands

#### Lambda Backend
```bash
# View CloudFormation events
aws cloudformation describe-stack-events --stack-name accessibility-checker-dev

# View Lambda logs
aws logs describe-log-groups --log-group-name-prefix "/aws/lambda/"

# Test Lambda function
aws lambda invoke --function-name presigned-url-generator-dev response.json
```

#### Express.js Backend
```bash
# View application logs
railway logs

# Check deployment status
railway status

# Test locally
cd express-backend && npm run dev
```

## 📈 Monitoring and Alerting

### CloudWatch (Lambda Backend)
- Lambda function metrics
- API Gateway metrics
- Custom business metrics
- CloudWatch alarms

### Platform Monitoring (Express.js)
- Railway: Built-in metrics
- Vercel: Analytics included
- Heroku: Add-ons available
- Render: Built-in monitoring

## 🔄 CI/CD Integration

### GitHub Actions
```yaml
name: Deploy
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Deploy Lambda
        run: ./deploy.sh prod lambda
```

### Automated Deployments
- **Lambda**: SAM CLI + CloudFormation
- **Express.js**: Platform-specific CLI tools
- **Both**: GitHub Actions integration

## 📚 Next Steps

1. **Test Your Deployment**
   - Health checks
   - API endpoints
   - Error handling

2. **Set Up Monitoring**
   - CloudWatch alarms
   - Custom metrics
   - Error tracking

3. **Configure Security**
   - API keys
   - CORS settings
   - Rate limiting

4. **Set Up CI/CD**
   - GitHub Actions
   - Automated testing
   - Deployment pipelines

## 🎉 Success Checklist

- [ ] Prerequisites installed
- [ ] Environment variables set
- [ ] Deployment script executed
- [ ] Health checks passing
- [ ] API endpoints working
- [ ] Monitoring configured
- [ ] Security settings applied
- [ ] Documentation updated

---

**Ready to deploy!** 🚀 Choose your backend and platform, then run the deployment script!