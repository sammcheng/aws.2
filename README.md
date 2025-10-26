# HousingA - Comprehensive Housing Analysis Platform

This repository contains two complementary projects for housing analysis and accessibility assessment:

## 🏠 Project 1: Zillow Image Scraper (Web Application)

A comprehensive Python application that scrapes property images from Zillow listings and stores them in organized S3 buckets. Features both a command-line interface and a modern web application.

### 🚀 Features

#### Core Functionality
- ✅ **Smart Image Extraction** - Finds all unique property images from Zillow listings
- ✅ **S3 Integration** - Automatically uploads images to organized S3 folders
- ✅ **Web Interface** - Modern, responsive web application
- ✅ **High-Quality Images** - Downloads highest resolution available (1536px)
- ✅ **Duplicate Filtering** - Removes duplicate images across different resolutions
- ✅ **Error Handling** - Graceful handling of network issues and missing data

#### Web Application Features
- 🎨 **Modern UI** - Bootstrap-based responsive design
- 📱 **Mobile Friendly** - Works on all device sizes
- 🖼️ **Image Gallery** - Beautiful gallery view with modal lightbox
- 📋 **Copy URLs** - Easy copying of S3 URLs to clipboard
- ⬇️ **Bulk Download** - Download all images at once
- 📊 **Statistics** - View image counts and processing status

### 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Web Frontend  │────│   Flask API      │────│   S3 Storage    │
│   (HTML/JS)     │    │   (Python)      │    │   (AWS)         │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │  Zillow Scraper  │
                       │  (Core Logic)    │
                       └──────────────────┘
```

### 🚀 Usage

#### Web Application
1. **Start the web server**
```bash
python app.py
```

2. **Open your browser**
```
http://localhost:5000
```

3. **Enter a Zillow URL and click "Extract Images"**

#### Command Line Interface
```bash
# Basic usage
python zillow_image_scraper.py "https://www.zillow.com/homedetails/123-Main-St-San-Jose-CA-95112/123456_zpid/"

# Upload to S3
python zillow_image_scraper.py "https://www.zillow.com/homedetails/123-Main-St-San-Jose-CA-95112/123456_zpid/" --s3

# Download locally
python zillow_image_scraper.py "https://www.zillow.com/homedetails/123-Main-St-San-Jose-CA-95112/123456_zpid/" --download
```

---

## ♿ Project 2: Home Accessibility Checker (AWS Lambda Backend)

A Python-based AWS Lambda backend system for analyzing home environments and providing accessibility recommendations using Amazon Rekognition and Amazon Bedrock.

### 🏗️ Architecture Overview

This backend system consists of two main Lambda functions that work together to analyze home images and generate accessibility recommendations:

#### 1. Rekognition Handler (`/lambdas/rekognition_handler/`)
- **Purpose**: Processes images using Amazon Rekognition to detect objects, labels, and accessibility features
- **Input**: S3 bucket and key for image location
- **Output**: Analysis results including detected objects, accessibility features, and potential barriers
- **Key Features**:
  - Object detection and labeling
  - Accessibility feature identification
  - Barrier detection
  - Accessibility scoring

#### 2. LLM Handler (`/lambdas/llm_handler/`)
- **Purpose**: Uses Amazon Bedrock to generate intelligent recommendations based on Rekognition analysis
- **Input**: Rekognition analysis results and image metadata
- **Output**: Structured recommendations and improvement suggestions
- **Key Features**:
  - AI-powered accessibility recommendations
  - Improvement suggestions with priority levels
  - Cost and implementation difficulty estimates

### 📁 Project Structure

```
aws/
├── lambdas/
│   ├── rekognition_handler/
│   │   └── lambda_function.py      # Rekognition Lambda handler
│   └── llm_handler/
│       └── lambda_function.py     # LLM Lambda handler
├── utils/
│   ├── __init__.py
│   ├── logger.py                   # Logging utility
│   ├── image_processor.py        # Image processing utilities
│   └── bedrock_client.py           # Bedrock LLM client
├── tests/
│   ├── __init__.py
│   ├── test_rekognition_handler.py
│   ├── test_llm_handler.py
│   ├── test_image_processor.py
│   └── test_bedrock_client.py
├── requirements.txt                # Python dependencies
├── env.example                     # Environment variables template
└── README.md                       # This file
```

### 🔧 AWS Services Used

#### Amazon Rekognition
- **Object Detection**: Identifies furniture, fixtures, and architectural elements
- **Label Detection**: Recognizes accessibility-related features and barriers
- **Custom Analysis**: Analyzes images for accessibility compliance

#### Amazon Bedrock
- **Claude 3 Sonnet**: Large Language Model for generating recommendations
- **Structured Output**: JSON-formatted recommendations and suggestions
- **Context-Aware**: Uses Rekognition results to provide relevant advice

#### Amazon S3
- **Image Storage**: Stores uploaded home images for analysis
- **Lambda Integration**: Provides images to Lambda functions

### 🚀 Usage Flow

1. **Image Upload**: User uploads home image to S3
2. **Rekognition Analysis**: First Lambda processes image with Amazon Rekognition
3. **LLM Processing**: Second Lambda generates recommendations using Bedrock
4. **Response**: Structured recommendations returned to client

### 🧪 Testing

Run tests using pytest:

```bash
# Install test dependencies
pip install pytest pytest-mock

# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_rekognition_handler.py

# Run with verbose output
pytest -v tests/
```

---

## 📦 Installation & Setup

### Prerequisites
- Python 3.9+ (for Zillow scraper) / Python 3.11 (for Lambda backend)
- AWS Account with S3 access
- AWS credentials configured
- Docker (for local development)
- AWS SAM CLI (for deployment)

### Setup Steps

1. **Clone the repository**
```bash
git clone https://github.com/G-Krishna-chandra/housingA.git
cd housingA
```

2. **Install dependencies**
```bash
# Install Python dependencies
pip install -r requirements.txt

# Install development dependencies
pip install pytest pytest-mock moto boto3

# Or use the Makefile
make install
```

3. **Configure AWS credentials**
```bash
# Option 1: AWS CLI
aws configure

# Option 2: Environment variables
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_DEFAULT_REGION=us-east-1
```

4. **Set up environment variables**
```bash
cp env.example .env
# Edit .env with your configuration
```

## 🧪 Local Development & Testing

### Quick Start
```bash
# Set up development environment
make dev-setup

# Run all tests
make test

# Start local API Gateway
make start-api
```

### Testing Commands
```bash
# Run all tests
make test

# Run unit tests only
make test-unit

# Run local testing script
make test-local

# Test individual functions
make test-presigned
make test-rekognition
make test-llm
make test-orchestrator

# Test API endpoints
make test-api
```

### Local AWS Simulation
```bash
# Start LocalStack for local AWS services
make setup-localstack

# Or manually with Docker Compose
docker-compose up -d localstack

# Check LocalStack status
curl http://localhost:4566/health
```

### Local Lambda Testing
```bash
# Test individual Lambda functions
python test_local.py --test

# Test specific function
python test_local.py --function presigned
python test_local.py --function rekognition
python test_local.py --function llm
python test_local.py --function orchestrator

# Simulate API calls
python test_local.py --simulate
```

### Local API Gateway
```bash
# Start local API Gateway
make start-api

# Test endpoints
curl -X POST http://localhost:3000/presigned-url \
  -H "Content-Type: application/json" \
  -d '{"filename": "test.jpg", "content_type": "image/jpeg"}'

curl -X POST http://localhost:3000/analyze \
  -H "Content-Type: application/json" \
  -d '{"images": [{"bucket": "test", "key": "test.jpg"}]}'
```

## 🛠️ Development Commands

### Makefile Commands
```bash
# Show all available commands
make help

# Setup & Installation
make install              # Install Python dependencies
make setup-localstack     # Start LocalStack for local AWS simulation
make dev-setup           # Complete development environment setup

# Testing
make test                # Run all tests (unit + local)
make test-unit           # Run unit tests with pytest
make test-local          # Run local testing script
make test-presigned      # Test Presigned URL function
make test-rekognition    # Test Rekognition function
make test-llm           # Test LLM function
make test-orchestrator  # Test Orchestrator function
make test-api           # Test API endpoints

# Development
make invoke-local        # Test individual Lambda functions locally
make start-api          # Start local API Gateway
make clean              # Clean up temporary files

# Deployment
make build              # Build SAM application
make deploy             # Deploy to AWS using SAM
make deploy-dev         # Deploy to dev environment
make deploy-prod        # Deploy to prod environment

# Docker
make docker-up          # Start all Docker services
make docker-down        # Stop all Docker services
make docker-logs        # Show Docker logs
```

## 🐳 Docker Deployment

### Using Docker Compose
```bash
# Build and start the application
docker-compose up --build

# Run in background
docker-compose up -d
```

## 🔧 Configuration

### Environment Variables
- `AWS_ACCESS_KEY_ID` - Your AWS access key
- `AWS_SECRET_ACCESS_KEY` - Your AWS secret key
- `AWS_DEFAULT_REGION` - AWS region (default: us-east-1)
- `S3_BUCKET_NAME` - S3 bucket name (default: zillow-images)
- `BEDROCK_MODEL_ID` - Bedrock model ID for Lambda backend
- `FLASK_ENV` - Flask environment (development/production)
- `SECRET_KEY` - Flask secret key for sessions
- `PORT` - Server port (default: 5000)

## 📁 S3 Organization

Images are stored in S3 with the following structure:
```
your-bucket/
├── listings/
│   ├── zpid_123456/
│   │   ├── image_001.jpg
│   │   ├── image_002.webp
│   │   └── ...
│   ├── zpid_789012/
│   │   ├── image_001.jpg
│   │   └── ...
│   └── ...
```

## 🛠️ API Endpoints

### Web Endpoints
- `GET /` - Main application page
- `GET /gallery/<job_id>` - View image gallery
- `GET /status/<job_id>` - Check processing status
- `GET /results/<job_id>` - Get detailed results

### API Endpoints
- `POST /process` - Process a Zillow URL
  ```json
  {
    "url": "https://www.zillow.com/homedetails/..."
  }
  ```

## 🔍 How It Works

### Zillow Scraper
1. **URL Validation** - Ensures the URL is a valid Zillow listing
2. **Page Fetching** - Downloads the listing page with browser-like headers
3. **Image Discovery** - Multiple methods to find images:
   - JSON data extraction
   - HTML parsing
   - Pattern matching
4. **Deduplication** - Removes duplicate images across resolutions
5. **S3 Upload** - Organizes and uploads images to S3
6. **Results** - Returns organized image URLs and metadata

### Accessibility Checker
1. **Image Analysis** - Amazon Rekognition analyzes uploaded images
2. **Feature Detection** - Identifies accessibility features and barriers
3. **AI Recommendations** - Amazon Bedrock generates intelligent suggestions
4. **Structured Output** - Returns prioritized recommendations and improvements

## 🚨 Error Handling

Both applications handle various error conditions:
- Invalid URLs
- Network connectivity issues
- Missing AWS credentials
- S3 upload failures
- Malformed image data
- Rate limiting

## 📊 Performance

- **Processing Time**: Typically 10-30 seconds per listing
- **Image Quality**: 1536px resolution (highest available)
- **Storage**: Organized by listing ID in S3
- **Scalability**: Handles multiple concurrent requests

## 🔒 Security

- AWS IAM credentials for S3 access
- Input validation for URLs
- Error message sanitization
- Rate limiting protection

## 📝 License

This project is open source and available under the MIT License.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📞 Support

For issues and questions:
1. Check the error messages in the web interface
2. Review the command-line output for detailed error information
3. Ensure AWS credentials are properly configured
4. Verify S3 bucket permissions
