"""
Unit tests for the Presigned URL Lambda function.
"""

import json
import pytest
import os
from unittest.mock import patch, MagicMock
from moto import mock_s3
import boto3

# Add the project root to the path
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from lambdas.presigned_url.lambda_function import (
    lambda_handler,
    is_valid_file_type,
    generate_unique_key,
    sanitize_filename
)

class TestPresignedUrlFunction:
    """Test cases for the Presigned URL Lambda function."""
    
    def setup_method(self):
        """Set up test fixtures."""
        os.environ['S3_BUCKET_NAME'] = 'test-bucket'
    
    def teardown_method(self):
        """Clean up after tests."""
        if 'S3_BUCKET_NAME' in os.environ:
            del os.environ['S3_BUCKET_NAME']
    
    @mock_s3
    def test_lambda_handler_success(self):
        """Test successful presigned URL generation."""
        # Create mock S3 bucket
        s3_client = boto3.client('s3')
        s3_client.create_bucket(Bucket='test-bucket')
        
        event = {
            'filename': 'house1.jpg',
            'content_type': 'image/jpeg'
        }
        
        context = MagicMock()
        context.aws_request_id = 'test-request-id'
        
        response = lambda_handler(event, context)
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert 'upload_url' in body
        assert 'fields' in body
        assert 'key' in body
        assert body['key'].startswith('uploads/')
        assert body['expires_in'] == 300
    
    def test_lambda_handler_missing_filename(self):
        """Test handler with missing filename."""
        event = {
            'content_type': 'image/jpeg'
        }
        
        context = MagicMock()
        
        response = lambda_handler(event, context)
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'error' in body
        assert 'Missing filename' in body['error']
    
    def test_lambda_handler_missing_content_type(self):
        """Test handler with missing content type."""
        event = {
            'filename': 'house1.jpg'
        }
        
        context = MagicMock()
        
        response = lambda_handler(event, context)
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'error' in body
        assert 'Missing content_type' in body['error']
    
    def test_lambda_handler_invalid_file_type(self):
        """Test handler with invalid file type."""
        event = {
            'filename': 'document.pdf',
            'content_type': 'application/pdf'
        }
        
        context = MagicMock()
        
        response = lambda_handler(event, context)
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'error' in body
        assert 'Invalid file type' in body['error']
    
    def test_is_valid_file_type_valid(self):
        """Test file type validation with valid types."""
        assert is_valid_file_type('house1.jpg', 'image/jpeg') == True
        assert is_valid_file_type('house1.jpeg', 'image/jpeg') == True
        assert is_valid_file_type('house1.png', 'image/png') == True
        assert is_valid_file_type('house1.webp', 'image/webp') == True
    
    def test_is_valid_file_type_invalid(self):
        """Test file type validation with invalid types."""
        assert is_valid_file_type('document.pdf', 'application/pdf') == False
        assert is_valid_file_type('text.txt', 'text/plain') == False
        assert is_valid_file_type('house1.jpg', 'image/gif') == False
        assert is_valid_file_type('house1.gif', 'image/jpeg') == False
    
    def test_generate_unique_key(self):
        """Test unique key generation."""
        key = generate_unique_key('house1.jpg')
        
        assert key.startswith('uploads/')
        assert key.endswith('-house1.jpg')
        assert len(key) > len('uploads/-house1.jpg')  # Should have UUID
    
    def test_sanitize_filename(self):
        """Test filename sanitization."""
        # Test dangerous characters
        assert sanitize_filename('../../../etc/passwd') == 'etc_passwd'
        assert sanitize_filename('file<name>') == 'file_name_'
        assert sanitize_filename('file|name') == 'file_name'
        assert sanitize_filename('file?name') == 'file_name'
        
        # Test empty filename
        assert sanitize_filename('') != ''
        assert sanitize_filename('_') != '_'
    
    @mock_s3
    def test_lambda_handler_s3_error(self):
        """Test handler with S3 error."""
        # Don't create bucket to simulate S3 error
        event = {
            'filename': 'house1.jpg',
            'content_type': 'image/jpeg'
        }
        
        context = MagicMock()
        
        response = lambda_handler(event, context)
        
        assert response['statusCode'] == 500
        body = json.loads(response['body'])
        assert 'error' in body
        assert 'Failed to generate presigned URL' in body['error']
    
    def test_lambda_handler_exception(self):
        """Test handler with unexpected exception."""
        event = {
            'filename': 'house1.jpg',
            'content_type': 'image/jpeg'
        }
        
        context = MagicMock()
        
        # Mock boto3 to raise exception
        with patch('boto3.client') as mock_client:
            mock_client.side_effect = Exception("AWS error")
            
            response = lambda_handler(event, context)
            
            assert response['statusCode'] == 500
            body = json.loads(response['body'])
            assert 'error' in body
            assert 'Failed to generate presigned URL' in body['error']
