"""
Unit tests for the Orchestrator Lambda function.
"""

import json
import pytest
import os
from unittest.mock import patch, MagicMock
from moto import mock_s3, mock_rekognition, mock_bedrock
import boto3

# Add the project root to the path
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from lambdas.orchestrator.lambda_function import (
    lambda_handler,
    process_images_with_rekognition,
    combine_labels_from_images,
    invoke_llm_lambda,
    generate_final_assessment,
    calculate_accessibility_score,
    categorize_labels
)

class TestOrchestrator:
    """Test cases for the Orchestrator Lambda function."""
    
    def setup_method(self):
        """Set up test fixtures."""
        os.environ['S3_BUCKET_NAME'] = 'test-bucket'
        os.environ['AWS_REGION'] = 'us-east-1'
        os.environ['BEDROCK_MODEL_ID'] = 'anthropic.claude-3-sonnet-20240229-v1:0'
    
    def teardown_method(self):
        """Clean up after tests."""
        for env_var in ['S3_BUCKET_NAME', 'AWS_REGION', 'BEDROCK_MODEL_ID']:
            if env_var in os.environ:
                del os.environ[env_var]
    
    @mock_s3
    @mock_rekognition
    @mock_bedrock
    def test_lambda_handler_success(self):
        """Test successful orchestrator processing."""
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
            
            event = {
                'images': [
                    {'bucket': 'test-bucket', 'key': 'image1.jpg'},
                    {'bucket': 'test-bucket', 'key': 'image2.jpg'}
                ]
            }
            
            context = MagicMock()
            context.aws_request_id = 'test-request-id'
            
            response = lambda_handler(event, context)
            
            assert response['statusCode'] == 200
            body = json.loads(response['body'])
            assert 'score' in body
            assert 'analyzed_images' in body
            assert 'positive_features' in body
            assert 'barriers' in body
            assert 'recommendations' in body
            assert body['analyzed_images'] == 2
    
    def test_lambda_handler_no_images(self):
        """Test handler with no images."""
        event = {}
        
        context = MagicMock()
        
        response = lambda_handler(event, context)
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'error' in body
        assert 'No images provided' in body['error']
    
    def test_lambda_handler_empty_images(self):
        """Test handler with empty images list."""
        event = {'images': []}
        
        context = MagicMock()
        
        response = lambda_handler(event, context)
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'error' in body
        assert 'No images provided' in body['error']
    
    def test_lambda_handler_exception(self):
        """Test handler with unexpected exception."""
        event = {
            'images': [{'bucket': 'test-bucket', 'key': 'image1.jpg'}]
        }
        
        context = MagicMock()
        
        # Mock boto3 to raise exception
        with patch('boto3.client') as mock_client:
            mock_client.side_effect = Exception("AWS error")
            
            response = lambda_handler(event, context)
            
            assert response['statusCode'] == 500
            body = json.loads(response['body'])
            assert 'error' in body
            assert 'Orchestrator failed' in body['error']
    
    def test_combine_labels_from_images(self):
        """Test combining labels from multiple images."""
        rekognition_results = [
            {
                'statusCode': 200,
                'body': json.dumps({
                    'labels': [
                        {'name': 'Stairs', 'confidence': 95.5, 'category': 'accessibility'},
                        {'name': 'Door', 'confidence': 88.2, 'category': 'accessibility'}
                    ]
                })
            },
            {
                'statusCode': 200,
                'body': json.dumps({
                    'labels': [
                        {'name': 'Bathroom', 'confidence': 92.1, 'category': 'accessibility'},
                        {'name': 'Kitchen', 'confidence': 85.7, 'category': 'accessibility'}
                    ]
                })
            }
        ]
        
        combined = combine_labels_from_images(rekognition_results)
        
        assert len(combined) == 4
        label_names = [label['name'] for label in combined]
        assert 'Stairs' in label_names
        assert 'Door' in label_names
        assert 'Bathroom' in label_names
        assert 'Kitchen' in label_names
    
    def test_combine_labels_from_images_with_errors(self):
        """Test combining labels with some failed results."""
        rekognition_results = [
            {
                'statusCode': 200,
                'body': json.dumps({
                    'labels': [
                        {'name': 'Stairs', 'confidence': 95.5, 'category': 'accessibility'}
                    ]
                })
            },
            {
                'statusCode': 500,
                'body': json.dumps({'error': 'Processing failed'})
            }
        ]
        
        combined = combine_labels_from_images(rekognition_results)
        
        assert len(combined) == 1
        assert combined[0]['name'] == 'Stairs'
    
    def test_calculate_accessibility_score(self):
        """Test accessibility score calculation."""
        # Test with positive features
        positive_labels = [
            {'name': 'Ramp', 'confidence': 95.0, 'category': 'accessibility'},
            {'name': 'Handrail', 'confidence': 90.0, 'category': 'accessibility'}
        ]
        
        score = calculate_accessibility_score(positive_labels)
        assert score > 50  # Should be positive
        
        # Test with barriers
        barrier_labels = [
            {'name': 'Stairs', 'confidence': 95.0, 'category': 'accessibility'},
            {'name': 'Step', 'confidence': 90.0, 'category': 'accessibility'}
        ]
        
        score = calculate_accessibility_score(barrier_labels)
        assert score < 50  # Should be negative
        
        # Test with no labels
        score = calculate_accessibility_score([])
        assert score == 50  # Should be neutral
    
    def test_categorize_labels(self):
        """Test label categorization."""
        labels = [
            {'name': 'Ramp', 'confidence': 95.0, 'category': 'accessibility'},
            {'name': 'Handrail', 'confidence': 90.0, 'category': 'accessibility'},
            {'name': 'Stairs', 'confidence': 85.0, 'category': 'accessibility'},
            {'name': 'Step', 'confidence': 80.0, 'category': 'accessibility'},
            {'name': 'Furniture', 'confidence': 75.0, 'category': 'accessibility'}
        ]
        
        positive_features, barriers = categorize_labels(labels)
        
        # Check positive features
        positive_names = [f['name'] for f in positive_features]
        assert 'Ramp' in positive_names
        assert 'Handrail' in positive_names
        
        # Check barriers
        barrier_names = [b['name'] for b in barriers]
        assert 'Stairs' in barrier_names
        assert 'Step' in barrier_names
        
        # Furniture should not be in either category
        assert 'Furniture' not in positive_names
        assert 'Furniture' not in barrier_names
    
    def test_generate_final_assessment(self):
        """Test final assessment generation."""
        combined_labels = [
            {'name': 'Ramp', 'confidence': 95.0, 'category': 'accessibility'},
            {'name': 'Stairs', 'confidence': 85.0, 'category': 'accessibility'}
        ]
        
        llm_results = {
            'statusCode': 200,
            'body': json.dumps({
                'recommendations': [
                    {
                        'title': 'Test Recommendation',
                        'description': 'Test description',
                        'priority': 'high',
                        'category': 'safety'
                    }
                ]
            })
        }
        
        image_count = 2
        
        assessment = generate_final_assessment(combined_labels, llm_results, image_count)
        
        assert 'score' in assessment
        assert 'analyzed_images' in assessment
        assert 'positive_features' in assessment
        assert 'barriers' in assessment
        assert 'recommendations' in assessment
        assert assessment['analyzed_images'] == 2
        assert len(assessment['recommendations']) > 0
    
    def test_generate_final_assessment_with_llm_error(self):
        """Test final assessment with LLM error."""
        combined_labels = [
            {'name': 'Stairs', 'confidence': 85.0, 'category': 'accessibility'}
        ]
        
        llm_results = {
            'statusCode': 500,
            'body': json.dumps({'error': 'LLM failed'})
        }
        
        image_count = 1
        
        assessment = generate_final_assessment(combined_labels, llm_results, image_count)
        
        assert 'score' in assessment
        assert 'analyzed_images' in assessment
        assert 'positive_features' in assessment
        assert 'barriers' in assessment
        assert 'recommendations' in assessment
        assert assessment['analyzed_images'] == 1
        # Should have fallback recommendations
        assert len(assessment['recommendations']) > 0
