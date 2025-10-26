"""
Amazon Bedrock client for generating accessibility recommendations
using Large Language Models.
"""

import json
import boto3
import os
from typing import Dict, Any, List
from utils.logger import get_logger

logger = get_logger(__name__)

class BedrockClient:
    """Handles interactions with Amazon Bedrock for LLM processing."""
    
    def __init__(self):
        """Initialize the Bedrock client."""
        self.bedrock = boto3.client('bedrock-runtime')
        self.model_id = os.getenv('BEDROCK_MODEL_ID', 'anthropic.claude-3-sonnet-20240229-v1:0')
    
    def generate_accessibility_recommendations(
        self, 
        rekognition_results: Dict[str, Any], 
        image_metadata: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Generate accessibility recommendations based on analysis results.
        
        Args:
            rekognition_results: Results from Rekognition analysis
            image_metadata: Additional image metadata
            
        Returns:
            List of accessibility recommendations
        """
        try:
            # Prepare context for the LLM
            context = self._prepare_analysis_context(rekognition_results, image_metadata)
            
            # Create prompt for accessibility recommendations
            prompt = self._create_recommendations_prompt(context)
            
            # Call Bedrock
            response = self._call_bedrock(prompt)
            
            # Parse and return recommendations
            return self._parse_recommendations(response)
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {str(e)}")
            return []
    
    def generate_improvement_suggestions(
        self, 
        rekognition_results: Dict[str, Any], 
        image_metadata: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Generate improvement suggestions for accessibility.
        
        Args:
            rekognition_results: Results from Rekognition analysis
            image_metadata: Additional image metadata
            
        Returns:
            List of improvement suggestions
        """
        try:
            # Prepare context for the LLM
            context = self._prepare_analysis_context(rekognition_results, image_metadata)
            
            # Create prompt for improvement suggestions
            prompt = self._create_improvements_prompt(context)
            
            # Call Bedrock
            response = self._call_bedrock(prompt)
            
            # Parse and return suggestions
            return self._parse_improvements(response)
            
        except Exception as e:
            logger.error(f"Error generating improvements: {str(e)}")
            return []
    
    def _prepare_analysis_context(
        self, 
        rekognition_results: Dict[str, Any], 
        image_metadata: Dict[str, Any]
    ) -> str:
        """Prepare analysis context for the LLM."""
        context_parts = []
        
        # Add accessibility features
        if 'accessibility_analysis' in rekognition_results:
            analysis = rekognition_results['accessibility_analysis']
            
            if analysis.get('accessibility_features'):
                features = [f"{f['name']} (confidence: {f['confidence']:.1f}%)" 
                           for f in analysis['accessibility_features']]
                context_parts.append(f"Accessibility features detected: {', '.join(features)}")
            
            if analysis.get('potential_barriers'):
                barriers = [f"{b['name']} (confidence: {b['confidence']:.1f}%)" 
                           for b in analysis['potential_barriers']]
                context_parts.append(f"Potential barriers detected: {', '.join(barriers)}")
            
            if 'summary' in analysis:
                summary = analysis['summary']
                context_parts.append(f"Accessibility score: {summary.get('accessibility_score', 'N/A')}/100")
        
        # Add detected objects and labels
        if rekognition_results.get('objects'):
            objects = [obj.get('Name', 'Unknown') for obj in rekognition_results['objects']]
            context_parts.append(f"Objects detected: {', '.join(objects)}")
        
        if rekognition_results.get('labels'):
            labels = [label.get('Name', 'Unknown') for label in rekognition_results['labels']]
            context_parts.append(f"Labels detected: {', '.join(labels)}")
        
        return '; '.join(context_parts)
    
    def _create_recommendations_prompt(self, context: str) -> str:
        """Create prompt for accessibility recommendations."""
        return f"""
You are an accessibility expert analyzing a home environment. Based on the following analysis:

{context}

Please provide specific, actionable recommendations to improve accessibility. Focus on:
1. Immediate safety concerns
2. Accessibility improvements
3. Universal design principles
4. Cost-effective solutions

Format your response as a JSON array of recommendations, each with:
- title: Brief title of the recommendation
- description: Detailed explanation
- priority: "high", "medium", or "low"
- category: "safety", "mobility", "vision", "hearing", or "cognitive"
- estimated_cost: "low", "medium", or "high"
"""
    
    def _create_improvements_prompt(self, context: str) -> str:
        """Create prompt for improvement suggestions."""
        return f"""
You are an accessibility expert analyzing a home environment. Based on the following analysis:

{context}

Please provide specific improvement suggestions for this space. Focus on:
1. Structural modifications
2. Equipment recommendations
3. Technology solutions
4. Design improvements

Format your response as a JSON array of improvements, each with:
- title: Brief title of the improvement
- description: Detailed explanation
- implementation_difficulty: "easy", "moderate", or "complex"
- category: "structural", "equipment", "technology", or "design"
- estimated_impact: "high", "medium", or "low"
"""
    
    def _call_bedrock(self, prompt: str) -> str:
        """Call Amazon Bedrock with the given prompt."""
        try:
            body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 2000,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }
            
            response = self.bedrock.invoke_model(
                modelId=self.model_id,
                body=json.dumps(body)
            )
            
            response_body = json.loads(response['body'].read())
            return response_body['content'][0]['text']
            
        except Exception as e:
            logger.error(f"Error calling Bedrock: {str(e)}")
            raise
    
    def _parse_recommendations(self, response: str) -> List[Dict[str, Any]]:
        """Parse LLM response into structured recommendations."""
        try:
            # Extract JSON from response
            json_start = response.find('[')
            json_end = response.rfind(']') + 1
            
            if json_start != -1 and json_end > json_start:
                json_str = response[json_start:json_end]
                return json.loads(json_str)
            else:
                # Fallback: create a single recommendation
                return [{
                    "title": "General Accessibility Review",
                    "description": response,
                    "priority": "medium",
                    "category": "general",
                    "estimated_cost": "medium"
                }]
                
        except Exception as e:
            logger.error(f"Error parsing recommendations: {str(e)}")
            return [{
                "title": "Analysis Error",
                "description": "Unable to parse recommendations from LLM response",
                "priority": "low",
                "category": "general",
                "estimated_cost": "low"
            }]
    
    def _parse_improvements(self, response: str) -> List[Dict[str, Any]]:
        """Parse LLM response into structured improvements."""
        try:
            # Extract JSON from response
            json_start = response.find('[')
            json_end = response.rfind(']') + 1
            
            if json_start != -1 and json_end > json_start:
                json_str = response[json_start:json_end]
                return json.loads(json_str)
            else:
                # Fallback: create a single improvement
                return [{
                    "title": "General Improvement Suggestions",
                    "description": response,
                    "implementation_difficulty": "moderate",
                    "category": "general",
                    "estimated_impact": "medium"
                }]
                
        except Exception as e:
            logger.error(f"Error parsing improvements: {str(e)}")
            return [{
                "title": "Analysis Error",
                "description": "Unable to parse improvements from LLM response",
                "implementation_difficulty": "easy",
                "category": "general",
                "estimated_impact": "low"
            }]
