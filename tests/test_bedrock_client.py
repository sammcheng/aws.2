"""
Tests for the BedrockClient utility.
"""

import json
import pytest
from unittest.mock import Mock, patch
import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.bedrock_client import BedrockClient

class TestBedrockClient:
    """Test cases for the BedrockClient utility."""
    
    def setup_method(self):
        """Set up test fixtures."""
        with patch.dict(os.environ, {'BEDROCK_MODEL_ID': 'test-model'}):
            self.client = BedrockClient()
    
    def test_init(self):
        """Test BedrockClient initialization."""
        assert self.client.model_id == 'test-model'
        assert self.client.bedrock is not None
    
    def test_prepare_analysis_context(self):
        """Test context preparation for LLM."""
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
        
        context = self.client._prepare_analysis_context(rekognition_results, image_metadata)
        
        assert 'Ramp' in context
        assert 'Step' in context
        assert '75.0' in context
        assert 'Chair' in context
        assert 'Furniture' in context
    
    def test_create_recommendations_prompt(self):
        """Test recommendations prompt creation."""
        context = "Test context with accessibility features"
        prompt = self.client._create_recommendations_prompt(context)
        
        assert context in prompt
        assert "accessibility expert" in prompt
        assert "JSON array" in prompt
        assert "title" in prompt
        assert "priority" in prompt
    
    def test_create_improvements_prompt(self):
        """Test improvements prompt creation."""
        context = "Test context with barriers"
        prompt = self.client._create_improvements_prompt(context)
        
        assert context in prompt
        assert "accessibility expert" in prompt
        assert "JSON array" in prompt
        assert "title" in prompt
        assert "implementation_difficulty" in prompt
    
    @patch('utils.bedrock_client.BedrockClient._call_bedrock')
    def test_generate_accessibility_recommendations_success(self, mock_call_bedrock):
        """Test successful recommendations generation."""
        # Mock Bedrock response
        mock_response = json.dumps([
            {
                "title": "Test Recommendation",
                "description": "Test description",
                "priority": "high",
                "category": "safety",
                "estimated_cost": "low"
            }
        ])
        mock_call_bedrock.return_value = mock_response
        
        rekognition_results = {
            'accessibility_analysis': {
                'accessibility_features': [],
                'potential_barriers': [],
                'summary': {'accessibility_score': 50.0}
            }
        }
        image_metadata = {}
        
        recommendations = self.client.generate_accessibility_recommendations(
            rekognition_results, image_metadata
        )
        
        assert len(recommendations) == 1
        assert recommendations[0]['title'] == "Test Recommendation"
        assert recommendations[0]['priority'] == "high"
    
    @patch('utils.bedrock_client.BedrockClient._call_bedrock')
    def test_generate_improvement_suggestions_success(self, mock_call_bedrock):
        """Test successful improvements generation."""
        # Mock Bedrock response
        mock_response = json.dumps([
            {
                "title": "Test Improvement",
                "description": "Test improvement description",
                "implementation_difficulty": "easy",
                "category": "equipment",
                "estimated_impact": "high"
            }
        ])
        mock_call_bedrock.return_value = mock_response
        
        rekognition_results = {
            'accessibility_analysis': {
                'accessibility_features': [],
                'potential_barriers': [],
                'summary': {'accessibility_score': 50.0}
            }
        }
        image_metadata = {}
        
        improvements = self.client.generate_improvement_suggestions(
            rekognition_results, image_metadata
        )
        
        assert len(improvements) == 1
        assert improvements[0]['title'] == "Test Improvement"
        assert improvements[0]['implementation_difficulty'] == "easy"
    
    def test_call_bedrock_success(self):
        """Test successful Bedrock API call."""
        # Mock Bedrock response
        mock_response = {
            'body': Mock()
        }
        mock_response['body'].read.return_value = json.dumps({
            'content': [{'text': 'Test response'}]
        }).encode()
        
        with patch.object(self.client.bedrock, 'invoke_model', return_value=mock_response):
            response = self.client._call_bedrock("Test prompt")
            assert response == 'Test response'
    
    def test_parse_recommendations_json_success(self):
        """Test parsing JSON recommendations."""
        json_response = json.dumps([
            {
                "title": "Test Recommendation",
                "description": "Test description",
                "priority": "high",
                "category": "safety",
                "estimated_cost": "low"
            }
        ])
        
        recommendations = self.client._parse_recommendations(json_response)
        
        assert len(recommendations) == 1
        assert recommendations[0]['title'] == "Test Recommendation"
    
    def test_parse_recommendations_fallback(self):
        """Test parsing fallback for non-JSON response."""
        non_json_response = "This is not JSON"
        
        recommendations = self.client._parse_recommendations(non_json_response)
        
        assert len(recommendations) == 1
        assert recommendations[0]['title'] == "General Accessibility Review"
        assert recommendations[0]['description'] == non_json_response
    
    def test_parse_improvements_json_success(self):
        """Test parsing JSON improvements."""
        json_response = json.dumps([
            {
                "title": "Test Improvement",
                "description": "Test improvement description",
                "implementation_difficulty": "easy",
                "category": "equipment",
                "estimated_impact": "high"
            }
        ])
        
        improvements = self.client._parse_improvements(json_response)
        
        assert len(improvements) == 1
        assert improvements[0]['title'] == "Test Improvement"
    
    def test_parse_improvements_fallback(self):
        """Test parsing fallback for non-JSON response."""
        non_json_response = "This is not JSON"
        
        improvements = self.client._parse_improvements(non_json_response)
        
        assert len(improvements) == 1
        assert improvements[0]['title'] == "General Improvement Suggestions"
        assert improvements[0]['description'] == non_json_response
