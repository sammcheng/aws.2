"""
Tests for the Rekognition Lambda handler.
"""

import json
import pytest
from unittest.mock import Mock, patch
import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lambdas.rekognition_handler.lambda_function import lambda_handler

class TestRekognitionHandler:
    """Test cases for the Rekognition Lambda handler."""
    
    def test_lambda_handler_success(self):
        """Test successful image processing."""
        # Mock event
        event = {
            'bucket': 'test-bucket',
            'key': 'test-image.jpg'
        }
        
        # Mock context
        context = Mock()
        context.function_name = 'test-function'
        
        # Mock AWS clients
        with patch('lambdas.rekognition_handler.lambda_function.boto3') as mock_boto3:
            mock_rekognition = Mock()
            mock_s3 = Mock()
            mock_boto3.client.side_effect = [mock_rekognition, mock_s3]
            
            # Mock ImageProcessor
            with patch('lambdas.rekognition_handler.lambda_function.ImageProcessor') as mock_processor_class:
                mock_processor = Mock()
                mock_processor.analyze_accessibility_features.return_value = {
                    'objects': [],
                    'labels': [],
                    'accessibility_analysis': {
                        'accessibility_features': [],
                        'potential_barriers': [],
                        'summary': {'accessibility_score': 75.0}
                    }
                }
                mock_processor_class.return_value = mock_processor
                
                # Call the handler
                response = lambda_handler(event, context)
                
                # Assertions
                assert response['statusCode'] == 200
                body = json.loads(response['body'])
                assert body['success'] is True
                assert 'results' in body
    
    def test_lambda_handler_missing_bucket(self):
        """Test handler with missing bucket in event."""
        event = {'key': 'test-image.jpg'}
        context = Mock()
        
        response = lambda_handler(event, context)
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'error' in body
    
    def test_lambda_handler_missing_key(self):
        """Test handler with missing key in event."""
        event = {'bucket': 'test-bucket'}
        context = Mock()
        
        response = lambda_handler(event, context)
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'error' in body
    
    def test_lambda_handler_exception(self):
        """Test handler with exception during processing."""
        event = {
            'bucket': 'test-bucket',
            'key': 'test-image.jpg'
        }
        context = Mock()
        
        # Mock AWS clients to raise exception
        with patch('lambdas.rekognition_handler.lambda_function.boto3') as mock_boto3:
            mock_boto3.client.side_effect = Exception("AWS error")
            
            response = lambda_handler(event, context)
            
            assert response['statusCode'] == 500
            body = json.loads(response['body'])
            assert 'error' in body
            assert 'Internal server error' in body['error']
