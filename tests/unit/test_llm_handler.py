"""
Unit tests for the LLM Handler Lambda function.
"""

import json
import pytest
import os
from unittest.mock import patch, MagicMock
from moto import mock_bedrock
import boto3

# Add the project root to the path
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from lambdas.llm_handler.lambda_function import (
    lambda_handler,
    BedrockClient
)

class TestLLMHandler:
    """Test cases for the LLM Handler Lambda function."""
    
    def setup_method(self):
        """Set up test fixtures."""
        os.environ['BEDROCK_MODEL_ID'] = 'anthropic.claude-3-sonnet-20240229-v1:0'
    
    def teardown_method(self):
        """Clean up after tests."""
        if 'BEDROCK_MODEL_ID' in os.environ:
            del os.environ['BEDROCK_MODEL_ID']
    
    @mock_bedrock
    def test_lambda_handler_success(self):
        """Test successful LLM processing."""
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
            
            event = {
                'rekognition_results': {
                    'labels': [
                        {'name': 'Stairs', 'confidence': 95.5, 'category': 'accessibility'},
                        {'name': 'Door', 'confidence': 88.2, 'category': 'accessibility'}
                    ]
                },
                'image_metadata': {
                    'total_images': 2,
                    'analysis_type': 'accessibility_assessment'
                }
            }
            
            context = MagicMock()
            
            response = lambda_handler(event, context)
            
            assert response['statusCode'] == 200
            body = json.loads(response['body'])
            assert 'recommendations' in body
            assert 'improvements' in body
            assert len(body['recommendations']) > 0
            assert len(body['improvements']) > 0
    
    def test_lambda_handler_missing_rekognition_results(self):
        """Test handler with missing rekognition results."""
        event = {
            'image_metadata': {}
        }
        
        context = MagicMock()
        
        response = lambda_handler(event, context)
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'error' in body
        assert 'No rekognition results provided' in body['error']
    
    def test_lambda_handler_bedrock_error(self):
        """Test handler with Bedrock error."""
        with patch('boto3.client') as mock_client:
            mock_bedrock = MagicMock()
            mock_bedrock.invoke_model.side_effect = Exception("Bedrock error")
            mock_client.return_value = mock_bedrock
            
            event = {
                'rekognition_results': {
                    'labels': [{'name': 'Stairs', 'confidence': 95.5}]
                },
                'image_metadata': {}
            }
            
            context = MagicMock()
            
            response = lambda_handler(event, context)
            
            assert response['statusCode'] == 500
            body = json.loads(response['body'])
            assert 'error' in body
            assert 'Internal server error' in body['error']
    
    def test_lambda_handler_exception(self):
        """Test handler with unexpected exception."""
        event = {
            'rekognition_results': {
                'labels': [{'name': 'Stairs', 'confidence': 95.5}]
            },
            'image_metadata': {}
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
    
    def test_bedrock_client_init(self):
        """Test BedrockClient initialization."""
        client = BedrockClient()
        assert client.model_id == 'anthropic.claude-3-sonnet-20240229-v1:0'
        assert client.bedrock is not None
    
    def test_bedrock_client_prepare_analysis_context(self):
        """Test context preparation for LLM."""
        client = BedrockClient()
        
        rekognition_results = {
            'accessibility_analysis': {
                'accessibility_features': [
                    {'name': 'Ramp', 'confidence': 95.0}
                ],
                'potential_barriers': [
                    {'name': 'Step', 'confidence': 90.0}
                ],
                'summary': {'accessibility_score': 75.0}
            },
            'objects': [{'Name': 'Chair'}],
            'labels': [{'Name': 'Furniture'}]
        }
        
        image_metadata = {'bucket': 'test-bucket', 'key': 'test.jpg'}
        
        context = client._prepare_analysis_context(rekognition_results, image_metadata)
        
        assert 'Ramp' in context
        assert 'Step' in context
        assert '75.0' in context
        assert 'Chair' in context
        assert 'Furniture' in context
    
    def test_bedrock_client_create_recommendations_prompt(self):
        """Test recommendations prompt creation."""
        client = BedrockClient()
        context = "Test context with accessibility features"
        prompt = client._create_recommendations_prompt(context)
        
        assert context in prompt
        assert "accessibility expert" in prompt
        assert "JSON array" in prompt
        assert "title" in prompt
        assert "priority" in prompt
    
    def test_bedrock_client_create_improvements_prompt(self):
        """Test improvements prompt creation."""
        client = BedrockClient()
        context = "Test context with barriers"
        prompt = client._create_improvements_prompt(context)
        
        assert context in prompt
        assert "accessibility expert" in prompt
        assert "JSON array" in prompt
        assert "title" in prompt
        assert "implementation_difficulty" in prompt
    
    def test_bedrock_client_parse_recommendations_success(self):
        """Test parsing JSON recommendations."""
        client = BedrockClient()
        json_response = json.dumps([
            {
                "title": "Test Recommendation",
                "description": "Test description",
                "priority": "high",
                "category": "safety",
                "estimated_cost": "low"
            }
        ])
        
        recommendations = client._parse_recommendations(json_response)
        
        assert len(recommendations) == 1
        assert recommendations[0]['title'] == "Test Recommendation"
    
    def test_bedrock_client_parse_recommendations_fallback(self):
        """Test parsing fallback for non-JSON response."""
        client = BedrockClient()
        non_json_response = "This is not JSON"
        
        recommendations = client._parse_recommendations(non_json_response)
        
        assert len(recommendations) == 1
        assert recommendations[0]['title'] == "General Accessibility Review"
        assert recommendations[0]['description'] == non_json_response
    
    def test_bedrock_client_parse_improvements_success(self):
        """Test parsing JSON improvements."""
        client = BedrockClient()
        json_response = json.dumps([
            {
                "title": "Test Improvement",
                "description": "Test improvement description",
                "implementation_difficulty": "easy",
                "category": "equipment",
                "estimated_impact": "high"
            }
        ])
        
        improvements = client._parse_improvements(json_response)
        
        assert len(improvements) == 1
        assert improvements[0]['title'] == "Test Improvement"
    
    def test_bedrock_client_parse_improvements_fallback(self):
        """Test parsing fallback for non-JSON response."""
        client = BedrockClient()
        non_json_response = "This is not JSON"
        
        improvements = client._parse_improvements(non_json_response)
        
        assert len(improvements) == 1
        assert improvements[0]['title'] == "General Improvement Suggestions"
        assert improvements[0]['description'] == non_json_response
