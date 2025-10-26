"""
Streaming LLM client for real-time response processing.
Provides streaming responses from Amazon Bedrock for better user experience.
"""

import json
import time
from typing import Dict, Any, List, Generator, Optional
from utils.structured_logger import get_logger
from utils.exceptions import LLMError, handle_aws_error
from utils.cache import ConnectionPool

logger = get_logger(__name__)

class StreamingLLMClient:
    """Streaming LLM client for real-time response processing."""
    
    def __init__(self, model_id: str = None):
        """
        Initialize streaming LLM client.
        
        Args:
            model_id: Bedrock model ID
        """
        self.model_id = model_id or "anthropic.claude-3-sonnet-20240229-v1:0"
        self.bedrock = ConnectionPool.get_client('bedrock-runtime')
    
    def stream_recommendations(
        self, 
        rekognition_results: Dict[str, Any], 
        image_metadata: Dict[str, Any]
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Stream accessibility recommendations.
        
        Args:
            rekognition_results: Results from Rekognition analysis
            image_metadata: Image metadata
            
        Yields:
            Streaming recommendation chunks
        """
        try:
            # Prepare context for streaming
            context = self._prepare_streaming_context(rekognition_results, image_metadata)
            
            # Create streaming prompt
            prompt = self._create_streaming_prompt(context)
            
            # Stream response from Bedrock
            for chunk in self._stream_bedrock_response(prompt):
                if chunk:
                    yield self._parse_streaming_chunk(chunk, "recommendation")
                    
        except Exception as e:
            logger.error(f"Error streaming recommendations: {str(e)}")
            yield {
                "type": "error",
                "content": f"Error generating recommendations: {str(e)}",
                "timestamp": time.time()
            }
    
    def stream_improvements(
        self, 
        rekognition_results: Dict[str, Any], 
        image_metadata: Dict[str, Any]
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Stream improvement suggestions.
        
        Args:
            rekognition_results: Results from Rekognition analysis
            image_metadata: Image metadata
            
        Yields:
            Streaming improvement chunks
        """
        try:
            # Prepare context for streaming
            context = self._prepare_streaming_context(rekognition_results, image_metadata)
            
            # Create streaming prompt
            prompt = self._create_improvements_prompt(context)
            
            # Stream response from Bedrock
            for chunk in self._stream_bedrock_response(prompt):
                if chunk:
                    yield self._parse_streaming_chunk(chunk, "improvement")
                    
        except Exception as e:
            logger.error(f"Error streaming improvements: {str(e)}")
            yield {
                "type": "error",
                "content": f"Error generating improvements: {str(e)}",
                "timestamp": time.time()
            }
    
    def _prepare_streaming_context(
        self, 
        rekognition_results: Dict[str, Any], 
        image_metadata: Dict[str, Any]
    ) -> str:
        """Prepare context for streaming LLM processing."""
        context_parts = []
        
        # Add accessibility features
        if 'accessibility_analysis' in rekognition_results:
            analysis = rekognition_results['accessibility_analysis']
            
            if analysis.get('accessibility_features'):
                features = [f"{f['name']} (confidence: {f['confidence']:.1f}%)" 
                           for f in analysis['accessibility_features']]
                context_parts.append(f"Accessibility features: {', '.join(features)}")
            
            if analysis.get('potential_barriers'):
                barriers = [f"{b['name']} (confidence: {b['confidence']:.1f}%)" 
                           for b in analysis['potential_barriers']]
                context_parts.append(f"Potential barriers: {', '.join(barriers)}")
        
        # Add detected objects and labels
        if rekognition_results.get('objects'):
            objects = [obj.get('Name', 'Unknown') for obj in rekognition_results['objects']]
            context_parts.append(f"Objects: {', '.join(objects)}")
        
        if rekognition_results.get('labels'):
            labels = [label.get('Name', 'Unknown') for label in rekognition_results['labels']]
            context_parts.append(f"Labels: {', '.join(labels)}")
        
        return '; '.join(context_parts)
    
    def _create_streaming_prompt(self, context: str) -> str:
        """Create prompt for streaming recommendations."""
        return f"""
You are an accessibility expert analyzing a home environment. Based on the following analysis:

{context}

Please provide specific, actionable recommendations to improve accessibility. 
Stream your response as you think, providing recommendations one at a time.
Focus on:
1. Immediate safety concerns
2. Accessibility improvements
3. Universal design principles
4. Cost-effective solutions

Format each recommendation as:
- Title: Brief title
- Description: Detailed explanation
- Priority: high/medium/low
- Category: safety/mobility/vision/hearing/cognitive
- Cost: low/medium/high
"""
    
    def _create_improvements_prompt(self, context: str) -> str:
        """Create prompt for streaming improvements."""
        return f"""
You are an accessibility expert analyzing a home environment. Based on the following analysis:

{context}

Please provide specific improvement suggestions for this space.
Stream your response as you think, providing improvements one at a time.
Focus on:
1. Structural modifications
2. Equipment recommendations
3. Technology solutions
4. Design improvements

Format each improvement as:
- Title: Brief title
- Description: Detailed explanation
- Difficulty: easy/moderate/complex
- Category: structural/equipment/technology/design
- Impact: high/medium/low
"""
    
    def _stream_bedrock_response(self, prompt: str) -> Generator[str, None, None]:
        """
        Stream response from Bedrock.
        
        Args:
            prompt: Input prompt
            
        Yields:
            Response chunks
        """
        try:
            body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 2000,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "stream": True
            }
            
            response = self.bedrock.invoke_model_with_response_stream(
                modelId=self.model_id,
                body=json.dumps(body)
            )
            
            for event in response['body']:
                if 'chunk' in event:
                    chunk = event['chunk']
                    if 'bytes' in chunk:
                        chunk_data = json.loads(chunk['bytes'].decode())
                        if 'delta' in chunk_data and 'text' in chunk_data['delta']:
                            yield chunk_data['delta']['text']
                            
        except Exception as e:
            logger.error(f"Error streaming from Bedrock: {str(e)}")
            raise handle_aws_error(e, "stream_bedrock_response", "bedrock")
    
    def _parse_streaming_chunk(self, chunk: str, chunk_type: str) -> Dict[str, Any]:
        """
        Parse streaming chunk into structured format.
        
        Args:
            chunk: Raw text chunk
            chunk_type: Type of chunk (recommendation/improvement)
            
        Returns:
            Parsed chunk data
        """
        return {
            "type": chunk_type,
            "content": chunk,
            "timestamp": time.time(),
            "model_id": self.model_id
        }
    
    def get_complete_response(
        self, 
        rekognition_results: Dict[str, Any], 
        image_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Get complete non-streaming response.
        
        Args:
            rekognition_results: Results from Rekognition analysis
            image_metadata: Image metadata
            
        Returns:
            Complete response with recommendations and improvements
        """
        try:
            # Collect streaming responses
            recommendations = []
            improvements = []
            
            # Stream recommendations
            for chunk in self.stream_recommendations(rekognition_results, image_metadata):
                if chunk.get("type") == "recommendation":
                    recommendations.append(chunk.get("content", ""))
            
            # Stream improvements
            for chunk in self.stream_improvements(rekognition_results, image_metadata):
                if chunk.get("type") == "improvement":
                    improvements.append(chunk.get("content", ""))
            
            # Parse and structure the responses
            parsed_recommendations = self._parse_recommendations("".join(recommendations))
            parsed_improvements = self._parse_improvements("".join(improvements))
            
            return {
                "recommendations": parsed_recommendations,
                "improvements": parsed_improvements,
                "streaming_enabled": True
            }
            
        except Exception as e:
            logger.error(f"Error getting complete response: {str(e)}")
            return {
                "recommendations": [],
                "improvements": [],
                "error": str(e)
            }
    
    def _parse_recommendations(self, text: str) -> List[Dict[str, Any]]:
        """Parse recommendations from text."""
        # Simple parsing - in production, use more sophisticated parsing
        recommendations = []
        lines = text.split('\n')
        
        current_rec = {}
        for line in lines:
            line = line.strip()
            if line.startswith('- Title:'):
                if current_rec:
                    recommendations.append(current_rec)
                current_rec = {'title': line.replace('- Title:', '').strip()}
            elif line.startswith('- Description:'):
                current_rec['description'] = line.replace('- Description:', '').strip()
            elif line.startswith('- Priority:'):
                current_rec['priority'] = line.replace('- Priority:', '').strip()
            elif line.startswith('- Category:'):
                current_rec['category'] = line.replace('- Category:', '').strip()
            elif line.startswith('- Cost:'):
                current_rec['estimated_cost'] = line.replace('- Cost:', '').strip()
        
        if current_rec:
            recommendations.append(current_rec)
        
        return recommendations
    
    def _parse_improvements(self, text: str) -> List[Dict[str, Any]]:
        """Parse improvements from text."""
        # Simple parsing - in production, use more sophisticated parsing
        improvements = []
        lines = text.split('\n')
        
        current_imp = {}
        for line in lines:
            line = line.strip()
            if line.startswith('- Title:'):
                if current_imp:
                    improvements.append(current_imp)
                current_imp = {'title': line.replace('- Title:', '').strip()}
            elif line.startswith('- Description:'):
                current_imp['description'] = line.replace('- Description:', '').strip()
            elif line.startswith('- Difficulty:'):
                current_imp['implementation_difficulty'] = line.replace('- Difficulty:', '').strip()
            elif line.startswith('- Category:'):
                current_imp['category'] = line.replace('- Category:', '').strip()
            elif line.startswith('- Impact:'):
                current_imp['estimated_impact'] = line.replace('- Impact:', '').strip()
        
        if current_imp:
            improvements.append(current_imp)
        
        return improvements
