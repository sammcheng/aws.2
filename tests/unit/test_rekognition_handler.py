"""
Unit tests for the Rekognition Handler Lambda function.
"""

import json
import pytest
import os
from unittest.mock import patch, MagicMock
from moto import mock_rekognition
import boto3

# Add the project root to the path
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from lambdas.rekognition_handler.lambda_function import (
    lambda_handler,
    filter_accessibility_labels
)

class TestRekognitionHandler:
    """Test cases for the Rekognition Handler Lambda function."""
    
    def setup_method(self):
        """Set up test fixtures."""
        os.environ['AWS_REGION'] = 'us-east-1'
    
    def teardown_method(self):
        """Clean up after tests."""
        if 'AWS_REGION' in os.environ:
            del os.environ['AWS_REGION']
    
    @mock_rekognition
    def test_lambda_handler_success(self):
        """Test successful Rekognition processing."""
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
            
            event = {
                'bucket': 'test-bucket',
                'key': 'test-image.jpg'
            }
            
            context = MagicMock()
            
            response = lambda_handler(event, context)
            
            assert response['statusCode'] == 200
            body = json.loads(response['body'])
            assert 'labels' in body
            assert 'image_key' in body
            assert body['image_key'] == 'test-image.jpg'
            
            # Check that only accessibility-relevant labels are returned
            label_names = [label['name'] for label in body['labels']]
            assert 'Stairs' in label_names
            assert 'Door' in label_names
            assert 'Bathroom' in label_names
            assert 'Kitchen' in label_names
            assert 'Furniture' not in label_names  # Should be filtered out
    
    def test_lambda_handler_missing_bucket(self):
        """Test handler with missing bucket."""
        event = {
            'key': 'test-image.jpg'
        }
        
        context = MagicMock()
        
        response = lambda_handler(event, context)
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'error' in body
        assert 'Missing bucket' in body['error']
    
    def test_lambda_handler_missing_key(self):
        """Test handler with missing key."""
        event = {
            'bucket': 'test-bucket'
        }
        
        context = MagicMock()
        
        response = lambda_handler(event, context)
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'error' in body
        assert 'Missing key' in body['error']
    
    def test_lambda_handler_rekognition_error(self):
        """Test handler with Rekognition error."""
        with patch('boto3.client') as mock_client:
            mock_rekognition = MagicMock()
            mock_rekognition.detect_labels.side_effect = Exception("Rekognition error")
            mock_client.return_value = mock_rekognition
            
            event = {
                'bucket': 'test-bucket',
                'key': 'test-image.jpg'
            }
            
            context = MagicMock()
            
            response = lambda_handler(event, context)
            
            assert response['statusCode'] == 500
            body = json.loads(response['body'])
            assert 'error' in body
            assert 'Internal server error' in body['error']
    
    def test_filter_accessibility_labels(self):
        """Test accessibility label filtering."""
        labels = [
            {'Name': 'Stairs', 'Confidence': 95.5},
            {'Name': 'Door', 'Confidence': 88.2},
            {'Name': 'Bathroom', 'Confidence': 92.1},
            {'Name': 'Kitchen', 'Confidence': 85.7},
            {'Name': 'Furniture', 'Confidence': 78.3},
            {'Name': 'Ramp', 'Confidence': 90.0},
            {'Name': 'Elevator', 'Confidence': 85.0},
            {'Name': 'Handrail', 'Confidence': 88.0},
            {'Name': 'Step', 'Confidence': 92.0},
            {'Name': 'Threshold', 'Confidence': 87.0}
        ]
        
        filtered = filter_accessibility_labels(labels)
        
        # Check that only accessibility-relevant labels are returned
        label_names = [label['name'] for label in filtered]
        
        # Should include accessibility features
        assert 'Stairs' in label_names
        assert 'Door' in label_names
        assert 'Bathroom' in label_names
        assert 'Kitchen' in label_names
        assert 'Ramp' in label_names
        assert 'Elevator' in label_names
        assert 'Handrail' in label_names
        assert 'Step' in label_names
        assert 'Threshold' in label_names
        
        # Should exclude non-accessibility features
        assert 'Furniture' not in label_names
        
        # Check label structure
        for label in filtered:
            assert 'name' in label
            assert 'confidence' in label
            assert 'category' in label
            assert label['category'] == 'accessibility'
    
    def test_filter_accessibility_labels_empty(self):
        """Test filtering with empty labels list."""
        labels = []
        filtered = filter_accessibility_labels(labels)
        assert filtered == []
    
    def test_filter_accessibility_labels_no_matches(self):
        """Test filtering with no accessibility-relevant labels."""
        labels = [
            {'Name': 'Furniture', 'Confidence': 78.3},
            {'Name': 'Decoration', 'Confidence': 65.0},
            {'Name': 'Lighting', 'Confidence': 70.0}
        ]
        
        filtered = filter_accessibility_labels(labels)
        assert filtered == []
    
    def test_lambda_handler_exception(self):
        """Test handler with unexpected exception."""
        event = {
            'bucket': 'test-bucket',
            'key': 'test-image.jpg'
        }
        
        context = MagicMock()
        
        # Mock boto3 to raise exception
        with patch('boto3.client') as mock_client:
            mock_client.side_effect = Exception("AWS error")
            
            response = lambda_handler(event, context)
            
            assert response['statusCode'] == 500
            body = json.loads(response['body'])
            assert 'error' in body
            assert 'Internal server error' in body['error']
