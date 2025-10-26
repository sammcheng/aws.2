"""
AWS Lambda handler for processing accessibility analysis results
using Amazon Bedrock LLM for generating recommendations.
"""

import json
import boto3
import os
from typing import Dict, Any, List
from utils.bedrock_client import BedrockClient
from utils.logger import get_logger

logger = get_logger(__name__)

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for LLM-based accessibility analysis.
    
    Args:
        event: Lambda event containing analysis results
        context: Lambda context object
        
    Returns:
        Dict containing LLM-generated recommendations
    """
    try:
        # Initialize Bedrock client
        bedrock_client = BedrockClient()
        
        # Extract analysis results from event
        rekognition_results = event.get('rekognition_results', {})
        image_metadata = event.get('image_metadata', {})
        
        if not rekognition_results:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'No rekognition results provided'})
            }
        
        # Generate accessibility recommendations
        recommendations = bedrock_client.generate_accessibility_recommendations(
            rekognition_results,
            image_metadata
        )
        
        # Generate improvement suggestions
        improvements = bedrock_client.generate_improvement_suggestions(
            rekognition_results,
            image_metadata
        )
        
        logger.info("Successfully generated LLM recommendations")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'success': True,
                'recommendations': recommendations,
                'improvements': improvements,
                'metadata': image_metadata
            })
        }
        
    except Exception as e:
        logger.error(f"Error generating LLM recommendations: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Internal server error',
                'message': str(e)
            })
        }
