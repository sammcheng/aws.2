#!/usr/bin/env python3
"""
Local testing script for Accessibility Checker Lambda functions.
Simulates Lambda events and tests functions locally with mocked AWS services.
"""

import json
import os
import sys
import boto3
from moto import mock_s3, mock_rekognition, mock_bedrock
from unittest.mock import patch, MagicMock
import pytest

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import Lambda functions
from lambdas.presigned_url.lambda_function import lambda_handler as presigned_url_handler
from lambdas.rekognition_handler.lambda_function import lambda_handler as rekognition_handler
from lambdas.llm_handler.lambda_function import lambda_handler as llm_handler
from lambdas.orchestrator.lambda_function import lambda_handler as orchestrator_handler

class MockContext:
    """Mock Lambda context for testing."""
    def __init__(self):
        self.function_name = "test-function"
        self.function_version = "1"
        self.invoked_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:test-function"
        self.memory_limit_in_mb = 512
        self.remaining_time_in_millis = 60000
        self.log_group_name = "/aws/lambda/test-function"
        self.log_stream_name = "2023/01/01/[$LATEST]test-stream"
        self.aws_request_id = "test-request-id"

def load_test_event(event_file):
    """Load test event from JSON file."""
    with open(f"tests/events/{event_file}", 'r') as f:
        return json.load(f)

@mock_s3
def test_presigned_url_generator():
    """Test presigned URL generator with mocked S3."""
    print("🧪 Testing Presigned URL Generator...")
    
    # Set up environment
    os.environ['S3_BUCKET_NAME'] = 'test-bucket'
    
    # Create mock S3 bucket
    s3_client = boto3.client('s3')
    s3_client.create_bucket(Bucket='test-bucket')
    
    # Load test event
    event = load_test_event('presigned_url_event.json')
    context = MockContext()
    
    # Test the function
    response = presigned_url_handler(event, context)
    
    # Verify response
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert 'upload_url' in body
    assert 'fields' in body
    assert 'key' in body
    assert body['key'].startswith('uploads/')
    
    print("✅ Presigned URL Generator test passed!")
    return response

@mock_rekognition
def test_rekognition_handler():
    """Test Rekognition handler with mocked Rekognition service."""
    print("🧪 Testing Rekognition Handler...")
    
    # Set up environment
    os.environ['AWS_REGION'] = 'us-east-1'
    
    # Create mock Rekognition client
    rekognition_client = boto3.client('rekognition')
    
    # Mock Rekognition response
    with patch('boto3.client') as mock_client:
        mock_rekognition = MagicMock()
        mock_rekognition.detect_labels.return_value = {
            'Labels': [
                {'Name': 'Stairs', 'Confidence': 95.5},
                {'Name': 'Door', 'Confidence': 88.2},
                {'Name': 'Bathroom', 'Confidence': 92.1},
                {'Name': 'Kitchen', 'Confidence': 85.7},
                {'Name': 'Furniture', 'Confidence': 78.3}
            ]
        }
        mock_client.return_value = mock_rekognition
        
        # Load test event
        event = load_test_event('rekognition_event.json')
        context = MockContext()
        
        # Test the function
        response = rekognition_handler(event, context)
        
        # Verify response
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert 'labels' in body
        assert 'image_key' in body
        assert len(body['labels']) > 0
        
        # Check that only accessibility-relevant labels are returned
        label_names = [label['name'] for label in body['labels']]
        assert 'Stairs' in label_names
        assert 'Door' in label_names
        assert 'Bathroom' in label_names
        assert 'Kitchen' in label_names
        assert 'Furniture' not in label_names  # Should be filtered out
        
        print("✅ Rekognition Handler test passed!")
        return response

@mock_bedrock
def test_llm_handler():
    """Test LLM handler with mocked Bedrock service."""
    print("🧪 Testing LLM Handler...")
    
    # Set up environment
    os.environ['BEDROCK_MODEL_ID'] = 'anthropic.claude-3-sonnet-20240229-v1:0'
    
    # Mock Bedrock response
    with patch('boto3.client') as mock_client:
        mock_bedrock = MagicMock()
        mock_bedrock.invoke_model.return_value = {
            'body': json.dumps({
                'content': [{
                    'text': json.dumps([
                        {
                            'title': 'Install Grab Bars',
                            'description': 'Add grab bars in the bathroom for safety',
                            'priority': 'high',
                            'category': 'safety',
                            'estimated_cost': 'low'
                        },
                        {
                            'title': 'Widen Doorways',
                            'description': 'Consider widening doorways for wheelchair access',
                            'priority': 'medium',
                            'category': 'structural',
                            'estimated_cost': 'high'
                        }
                    ])
                }])
            })
        }
        mock_client.return_value = mock_bedrock
        
        # Load test event
        event = load_test_event('llm_event.json')
        context = MockContext()
        
        # Test the function
        response = llm_handler(event, context)
        
        # Verify response
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert 'recommendations' in body
        assert 'improvements' in body
        assert len(body['recommendations']) > 0
        
        print("✅ LLM Handler test passed!")
        return response

@mock_s3
@mock_rekognition
@mock_bedrock
def test_orchestrator():
    """Test orchestrator with mocked AWS services."""
    print("🧪 Testing Orchestrator...")
    
    # Set up environment
    os.environ['S3_BUCKET_NAME'] = 'test-bucket'
    os.environ['AWS_REGION'] = 'us-east-1'
    os.environ['BEDROCK_MODEL_ID'] = 'anthropic.claude-3-sonnet-20240229-v1:0'
    
    # Create mock S3 bucket
    s3_client = boto3.client('s3')
    s3_client.create_bucket(Bucket='test-bucket')
    
    # Mock Lambda client for cross-function invocation
    with patch('boto3.client') as mock_client:
        # Mock S3 client
        mock_s3 = MagicMock()
        mock_s3.create_bucket.return_value = {}
        
        # Mock Rekognition response
        mock_rekognition = MagicMock()
        mock_rekognition.detect_labels.return_value = {
            'Labels': [
                {'Name': 'Stairs', 'Confidence': 95.5},
                {'Name': 'Door', 'Confidence': 88.2}
            ]
        }
        
        # Mock Bedrock response
        mock_bedrock = MagicMock()
        mock_bedrock.invoke_model.return_value = {
            'body': json.dumps({
                'content': [{
                    'text': json.dumps([
                        {
                            'title': 'Test Recommendation',
                            'description': 'Test description',
                            'priority': 'high',
                            'category': 'safety'
                        }
                    ])
                }])
            })
        }
        
        # Mock Lambda client for orchestrator
        mock_lambda = MagicMock()
        mock_lambda.invoke.return_value = {
            'Payload': json.dumps({
                'statusCode': 200,
                'body': json.dumps({
                    'labels': [
                        {'name': 'Stairs', 'confidence': 95.5, 'category': 'accessibility'},
                        {'name': 'Door', 'confidence': 88.2, 'category': 'accessibility'}
                    ]
                })
            })
        }
        
        # Configure mock client to return appropriate clients
        def mock_client_side_effect(service_name, **kwargs):
            if service_name == 's3':
                return mock_s3
            elif service_name == 'rekognition':
                return mock_rekognition
            elif service_name == 'bedrock-runtime':
                return mock_bedrock
            elif service_name == 'lambda':
                return mock_lambda
            return MagicMock()
        
        mock_client.side_effect = mock_client_side_effect
        
        # Load test event
        event = load_test_event('analyze_event.json')
        context = MockContext()
        
        # Test the function
        response = orchestrator_handler(event, context)
        
        # Verify response
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert 'score' in body
        assert 'analyzed_images' in body
        assert 'positive_features' in body
        assert 'barriers' in body
        assert 'recommendations' in body
        assert body['analyzed_images'] == 3
        
        print("✅ Orchestrator test passed!")
        return response

def run_all_tests():
    """Run all local tests."""
    print("🚀 Starting Local Testing Suite...")
    print("=" * 50)
    
    try:
        # Test individual functions
        test_presigned_url_generator()
        test_rekognition_handler()
        test_llm_handler()
        test_orchestrator()
        
        print("=" * 50)
        print("🎉 All tests passed successfully!")
        print("✅ Presigned URL Generator: Working")
        print("✅ Rekognition Handler: Working")
        print("✅ LLM Handler: Working")
        print("✅ Orchestrator: Working")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        sys.exit(1)

def simulate_api_calls():
    """Simulate API Gateway calls."""
    print("🌐 Simulating API Gateway Calls...")
    print("=" * 50)
    
    # Simulate presigned URL request
    print("📤 Simulating POST /presigned-url")
    presigned_event = {
        "httpMethod": "POST",
        "path": "/presigned-url",
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(load_test_event('presigned_url_event.json'))
    }
    
    # Simulate analyze request
    print("🔍 Simulating POST /analyze")
    analyze_event = {
        "httpMethod": "POST",
        "path": "/analyze",
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(load_test_event('analyze_event.json'))
    }
    
    print("✅ API simulation complete!")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Local testing for Accessibility Checker')
    parser.add_argument('--test', action='store_true', help='Run all tests')
    parser.add_argument('--simulate', action='store_true', help='Simulate API calls')
    parser.add_argument('--function', choices=['presigned', 'rekognition', 'llm', 'orchestrator'], 
                       help='Test specific function')
    
    args = parser.parse_args()
    
    if args.test:
        run_all_tests()
    elif args.simulate:
        simulate_api_calls()
    elif args.function:
        if args.function == 'presigned':
            test_presigned_url_generator()
        elif args.function == 'rekognition':
            test_rekognition_handler()
        elif args.function == 'llm':
            test_llm_handler()
        elif args.function == 'orchestrator':
            test_orchestrator()
    else:
        print("Usage: python test_local.py --test")
        print("       python test_local.py --simulate")
        print("       python test_local.py --function <function_name>")
