"""
Tests for the LLM Lambda handler.
"""

import json
import pytest
from unittest.mock import Mock, patch
import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lambdas.llm_handler.lambda_function import lambda_handler

class TestLLMHandler:
    """Test cases for the LLM Lambda handler."""
    
    def test_lambda_handler_success(self):
        """Test successful LLM processing."""
        # Mock event with rekognition results
        event = {
            'rekognition_results': {
                'objects': [{'Name': 'Chair', 'Confidence': 95.0}],
                'labels': [{'Name': 'Furniture', 'Confidence': 90.0}],
                'accessibility_analysis': {
                    'accessibility_features': [],
                    'potential_barriers': [],
                    'summary': {'accessibility_score': 75.0}
                }
            },
            'image_metadata': {
                'bucket': 'test-bucket',
                'key': 'test-image.jpg'
            }
        }
        
        # Mock context
        context = Mock()
        context.function_name = 'test-function'
        
        # Mock BedrockClient
        with patch('lambdas.llm_handler.lambda_function.BedrockClient') as mock_bedrock_class:
            mock_bedrock = Mock()
            mock_bedrock.generate_accessibility_recommendations.return_value = [
                {
                    'title': 'Test Recommendation',
                    'description': 'Test description',
                    'priority': 'high',
                    'category': 'safety',
                    'estimated_cost': 'low'
                }
            ]
            mock_bedrock.generate_improvement_suggestions.return_value = [
                {
                    'title': 'Test Improvement',
                    'description': 'Test improvement description',
                    'implementation_difficulty': 'easy',
                    'category': 'equipment',
                    'estimated_impact': 'high'
                }
            ]
            mock_bedrock_class.return_value = mock_bedrock
            
            # Call the handler
            response = lambda_handler(event, context)
            
            # Assertions
            assert response['statusCode'] == 200
            body = json.loads(response['body'])
            assert body['success'] is True
            assert 'recommendations' in body
            assert 'improvements' in body
    
    def test_lambda_handler_missing_rekognition_results(self):
        """Test handler with missing rekognition results."""
        event = {'image_metadata': {}}
        context = Mock()
        
        response = lambda_handler(event, context)
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'error' in body
    
    def test_lambda_handler_exception(self):
        """Test handler with exception during processing."""
        event = {
            'rekognition_results': {
                'objects': [],
                'labels': [],
                'accessibility_analysis': {}
            },
            'image_metadata': {}
        }
        context = Mock()
        
        # Mock BedrockClient to raise exception
        with patch('lambdas.llm_handler.lambda_function.BedrockClient') as mock_bedrock_class:
            mock_bedrock_class.side_effect = Exception("Bedrock error")
            
            response = lambda_handler(event, context)
            
            assert response['statusCode'] == 500
            body = json.loads(response['body'])
            assert 'error' in body
            assert 'Internal server error' in body['error']
