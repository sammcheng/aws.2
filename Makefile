# Accessibility Checker API - Development Makefile

.PHONY: help install test test-unit test-local deploy invoke-local clean setup-localstack

# Default target
help:
	@echo "Accessibility Checker API - Development Commands"
	@echo "================================================"
	@echo ""
	@echo "Setup & Installation:"
	@echo "  install          Install Python dependencies"
	@echo "  setup-localstack Start LocalStack for local AWS simulation"
	@echo ""
	@echo "Testing:"
	@echo "  test            Run all tests (unit + local)"
	@echo "  test-unit       Run unit tests with pytest"
	@echo "  test-local      Run local testing script"
	@echo ""
	@echo "Development:"
	@echo "  invoke-local    Test individual Lambda functions locally"
	@echo "  clean           Clean up temporary files"
	@echo ""
	@echo "Deployment:"
	@echo "  deploy          Deploy to AWS using SAM"
	@echo "  build           Build SAM application"
	@echo ""

# Installation
install:
	@echo "📦 Installing Python dependencies..."
	pip install -r requirements.txt
	pip install pytest pytest-mock moto boto3
	@echo "✅ Dependencies installed!"

# Setup LocalStack
setup-localstack:
	@echo "🐳 Starting LocalStack for local AWS simulation..."
	docker-compose up -d localstack
	@echo "⏳ Waiting for LocalStack to be ready..."
	sleep 10
	@echo "✅ LocalStack is ready at http://localhost:4566"

# Testing
test: test-unit test-local
	@echo "🎉 All tests completed!"

test-unit:
	@echo "🧪 Running unit tests with pytest..."
	pytest tests/unit/ -v --tb=short
	@echo "✅ Unit tests completed!"

test-local:
	@echo "🧪 Running local testing script..."
	python test_local.py --test
	@echo "✅ Local tests completed!"

# Local development
invoke-local:
	@echo "🚀 Testing Lambda functions locally..."
	@echo ""
	@echo "Testing Presigned URL Generator..."
	python test_local.py --function presigned
	@echo ""
	@echo "Testing Rekognition Handler..."
	python test_local.py --function rekognition
	@echo ""
	@echo "Testing LLM Handler..."
	python test_local.py --function llm
	@echo ""
	@echo "Testing Orchestrator..."
	python test_local.py --function orchestrator
	@echo "✅ Local invocation tests completed!"

# SAM commands
build:
	@echo "🔨 Building SAM application..."
	sam build
	@echo "✅ SAM build completed!"

deploy:
	@echo "🚀 Deploying to AWS..."
	sam deploy --guided
	@echo "✅ Deployment completed!"

deploy-dev:
	@echo "🚀 Deploying to AWS (dev environment)..."
	sam deploy --config-env dev
	@echo "✅ Dev deployment completed!"

deploy-prod:
	@echo "🚀 Deploying to AWS (prod environment)..."
	sam deploy --config-env prod
	@echo "✅ Prod deployment completed!"

# Local API Gateway
start-api:
	@echo "🌐 Starting local API Gateway..."
	sam local start-api --port 3000
	@echo "✅ Local API Gateway running at http://localhost:3000"

# Cleanup
clean:
	@echo "🧹 Cleaning up temporary files..."
	rm -rf .aws-sam/
	rm -rf localstack-data/
	rm -rf __pycache__/
	rm -rf tests/__pycache__/
	rm -rf tests/unit/__pycache__/
	find . -name "*.pyc" -delete
	find . -name "*.pyo" -delete
	find . -name ".pytest_cache" -type d -exec rm -rf {} +
	@echo "✅ Cleanup completed!"

# Docker commands
docker-up:
	@echo "🐳 Starting all Docker services..."
	docker-compose up -d
	@echo "✅ All services started!"

docker-down:
	@echo "🐳 Stopping all Docker services..."
	docker-compose down
	@echo "✅ All services stopped!"

docker-logs:
	@echo "📋 Showing Docker logs..."
	docker-compose logs -f

# Performance optimization
build-layer:
	@echo "🔨 Building Lambda layer..."
	./layers/build_layer.sh
	@echo "✅ Layer built successfully!"

deploy-layer:
	@echo "🚀 Deploying Lambda layer..."
	./layers/build_layer.sh --deploy
	@echo "✅ Layer deployed successfully!"

optimize:
	@echo "⚡ Running performance optimizations..."
	@echo "Building layer..."
	./layers/build_layer.sh
	@echo "Building SAM application..."
	sam build
	@echo "✅ Optimization completed!"

# Development helpers
check-aws:
	@echo "🔍 Checking AWS configuration..."
	aws sts get-caller-identity
	@echo "✅ AWS configuration is valid!"

check-sam:
	@echo "🔍 Checking SAM CLI..."
	sam --version
	@echo "✅ SAM CLI is available!"

# Performance testing
test-performance:
	@echo "📊 Running performance tests..."
	python -c "
import time
import asyncio
import aiohttp

async def test_concurrent_requests():
    async with aiohttp.ClientSession() as session:
        start_time = time.time()
        tasks = [
            session.post('http://localhost:3000/presigned-url', 
                        json={'filename': f'test{i}.jpg', 'content_type': 'image/jpeg'})
            for i in range(10)
        ]
        results = await asyncio.gather(*tasks)
        duration = time.time() - start_time
        print(f'Processed 10 requests in {duration:.2f}s')
        print(f'Average response time: {duration/10:.2f}s per request')

asyncio.run(test_concurrent_requests())
"
	@echo "✅ Performance test completed!"

# Test specific functions
test-presigned:
	@echo "🧪 Testing Presigned URL function..."
	python test_local.py --function presigned

test-rekognition:
	@echo "🧪 Testing Rekognition function..."
	python test_local.py --function rekognition

test-llm:
	@echo "🧪 Testing LLM function..."
	python test_local.py --function llm

test-orchestrator:
	@echo "🧪 Testing Orchestrator function..."
	python test_local.py --function orchestrator

# API testing
test-api:
	@echo "🌐 Testing API endpoints..."
	@echo "Testing POST /presigned-url..."
	curl -X POST http://localhost:3000/presigned-url \
		-H "Content-Type: application/json" \
		-d '{"filename": "test.jpg", "content_type": "image/jpeg"}' || echo "API not running"
	@echo ""
	@echo "Testing POST /analyze..."
	curl -X POST http://localhost:3000/analyze \
		-H "Content-Type: application/json" \
		-d '{"images": [{"bucket": "test", "key": "test.jpg"}]}' || echo "API not running"

# Environment setup
setup-env:
	@echo "🔧 Setting up environment..."
	cp env.example .env
	@echo "✅ Environment file created! Please edit .env with your configuration."

# Full development setup
dev-setup: install setup-env setup-localstack
	@echo "🎉 Development environment is ready!"
	@echo "Run 'make start-api' to start the local API Gateway"
	@echo "Run 'make test' to run all tests"
