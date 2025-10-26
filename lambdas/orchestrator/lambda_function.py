"""
AWS Lambda orchestrator for coordinating the entire accessibility analysis workflow.
Coordinates Rekognition and LLM Lambda functions to provide comprehensive assessments.
"""

import json
import boto3
import os
from typing import Dict, Any, List
from concurrent.futures import ThreadPoolExecutor, as_completed

# Import custom modules
from utils.structured_logger import get_logger, create_request_context
from utils.exceptions import (
    InvalidInputError, LambdaInvocationError, AccessibilityCheckerError,
    handle_aws_error
)
from utils.validation import AnalyzeRequest
from utils.cache import ConnectionPool, ImageAnalysisCache, PerformanceMonitor
from utils.batch_processor import RekognitionBatchProcessor
from utils.streaming_llm import StreamingLLMClient

# Initialize structured logger
logger = get_logger(__name__)

# Initialize AWS clients with connection pooling
lambda_client = ConnectionPool.get_client('lambda')

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main orchestrator Lambda handler for coordinating accessibility analysis workflow.
    
    Args:
        event: Lambda event containing {"images": [{"bucket": "...", "key": "..."}]}
        context: Lambda context object
        
    Returns:
        Dict containing final assessment with score, analyzed images, and recommendations
    """
    try:
        # Log the incoming event for debugging
        logger.info(f"Orchestrator processing event: {json.dumps(event)}")
        
        # Extract images from event
        images = event.get('images', [])
        
        if not images:
            logger.error("No images provided in event")
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'No images provided'})
            }
        
        logger.info(f"Processing {len(images)} images")
        
        # Step 1: Process all images with Rekognition Lambda asynchronously
        rekognition_results = process_images_with_rekognition(images)
        
        # Step 2: Combine all labels from multiple images
        combined_labels = combine_labels_from_images(rekognition_results)
        
        # Step 3: Invoke LLM Lambda with combined data
        llm_results = invoke_llm_lambda(combined_labels, len(images))
        
        # Step 4: Generate final assessment
        final_assessment = generate_final_assessment(
            combined_labels, 
            llm_results, 
            len(images)
        )
        
        logger.info(f"Orchestrator completed successfully. Analyzed {len(images)} images")
        
        return {
            'statusCode': 200,
            'body': json.dumps(final_assessment)
        }
        
    except Exception as e:
        logger.error(f"Orchestrator error: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Orchestrator failed',
                'message': str(e)
            })
        }

def process_images_with_rekognition(images: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    """
    Process all images with Rekognition Lambda asynchronously.
    
    Args:
        images: List of image objects with bucket and key
        
    Returns:
        List of Rekognition results for each image
    """
    rekognition_results = []
    errors = []
    
    # Use ThreadPoolExecutor for concurrent processing
    with ThreadPoolExecutor(max_workers=10) as executor:
        # Submit all Rekognition tasks
        future_to_image = {
            executor.submit(invoke_rekognition_lambda, image): image 
            for image in images
        }
        
        # Collect results as they complete
        for future in as_completed(future_to_image):
            image = future_to_image[future]
            try:
                result = future.result()
                if result.get('statusCode') == 200:
                    rekognition_results.append(result)
                    logger.info(f"Successfully processed image: {image.get('key')}")
                else:
                    error_msg = result.get('body', {}).get('error', 'Unknown error')
                    errors.append(f"Image {image.get('key')}: {error_msg}")
                    logger.error(f"Rekognition failed for {image.get('key')}: {error_msg}")
            except Exception as e:
                error_msg = f"Exception processing {image.get('key')}: {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)
    
    # Log any errors that occurred
    if errors:
        logger.warning(f"Encountered {len(errors)} errors during Rekognition processing")
        for error in errors:
            logger.warning(error)
    
    return rekognition_results

def invoke_rekognition_lambda(image: Dict[str, str]) -> Dict[str, Any]:
    """
    Invoke the Rekognition Lambda function for a single image.
    
    Args:
        image: Image object with bucket and key
        
    Returns:
        Rekognition Lambda response
    """
    try:
        # Prepare payload for Rekognition Lambda
        payload = {
            'bucket': image['bucket'],
            'key': image['key']
        }
        
        # Invoke Rekognition Lambda
        response = lambda_client.invoke(
            FunctionName='rekognition-handler',  # Update with actual function name
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )
        
        # Parse response
        response_payload = json.loads(response['Payload'].read())
        
        return response_payload
        
    except Exception as e:
        logger.error(f"Failed to invoke Rekognition Lambda for {image.get('key')}: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': f'Rekognition invocation failed: {str(e)}'})
        }

def combine_labels_from_images(rekognition_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Combine all labels from multiple images into a single list.
    
    Args:
        rekognition_results: List of Rekognition results
        
    Returns:
        Combined list of all labels from all images
    """
    combined_labels = []
    image_count = 0
    
    for result in rekognition_results:
        if result.get('statusCode') == 200:
            body = json.loads(result.get('body', '{}'))
            labels = body.get('labels', [])
            combined_labels.extend(labels)
            image_count += 1
            logger.info(f"Added {len(labels)} labels from image")
    
    logger.info(f"Combined {len(combined_labels)} labels from {image_count} images")
    return combined_labels

def invoke_llm_lambda(combined_labels: List[Dict[str, Any]], image_count: int) -> Dict[str, Any]:
    """
    Invoke the LLM Lambda function with combined data.
    
    Args:
        combined_labels: Combined labels from all images
        image_count: Number of images analyzed
        
    Returns:
        LLM Lambda response
    """
    try:
        # Prepare payload for LLM Lambda
        payload = {
            'rekognition_results': {
                'labels': combined_labels,
                'image_count': image_count
            },
            'image_metadata': {
                'total_images': image_count,
                'analysis_type': 'accessibility_assessment'
            }
        }
        
        # Invoke LLM Lambda
        response = lambda_client.invoke(
            FunctionName='llm-handler',  # Update with actual function name
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )
        
        # Parse response
        response_payload = json.loads(response['Payload'].read())
        
        return response_payload
        
    except Exception as e:
        logger.error(f"Failed to invoke LLM Lambda: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': f'LLM invocation failed: {str(e)}'})
        }

def generate_final_assessment(
    combined_labels: List[Dict[str, Any]], 
    llm_results: Dict[str, Any], 
    image_count: int
) -> Dict[str, Any]:
    """
    Generate the final accessibility assessment.
    
    Args:
        combined_labels: Combined labels from all images
        llm_results: Results from LLM Lambda
        image_count: Number of images analyzed
        
    Returns:
        Final assessment with score, features, barriers, and recommendations
    """
    try:
        # Extract LLM results
        llm_body = {}
        if llm_results.get('statusCode') == 200:
            llm_body = json.loads(llm_results.get('body', '{}'))
        
        # Calculate accessibility score based on labels
        score = calculate_accessibility_score(combined_labels)
        
        # Categorize labels into positive features and barriers
        positive_features, barriers = categorize_labels(combined_labels)
        
        # Extract recommendations from LLM results
        recommendations = llm_body.get('recommendations', [])
        if not recommendations:
            recommendations = generate_fallback_recommendations(positive_features, barriers)
        
        # Generate final assessment
        assessment = {
            'score': score,
            'analyzed_images': image_count,
            'positive_features': positive_features,
            'barriers': barriers,
            'recommendations': recommendations,
            'total_labels': len(combined_labels),
            'analysis_timestamp': context.aws_request_id if 'context' in globals() else None
        }
        
        logger.info(f"Generated final assessment with score: {score}")
        return assessment
        
    except Exception as e:
        logger.error(f"Error generating final assessment: {str(e)}")
        return {
            'score': 0,
            'analyzed_images': image_count,
            'positive_features': [],
            'barriers': [],
            'recommendations': [{'title': 'Analysis Error', 'description': 'Unable to complete assessment'}],
            'error': str(e)
        }

def calculate_accessibility_score(labels: List[Dict[str, Any]]) -> int:
    """
    Calculate accessibility score based on detected labels.
    
    Args:
        labels: List of detected labels
        
    Returns:
        Accessibility score (0-100)
    """
    if not labels:
        return 50  # Neutral score for no data
    
    # Define positive and negative features
    positive_features = {'ramp', 'elevator', 'lift', 'handrail', 'grab bar', 'accessible'}
    negative_features = {'stairs', 'step', 'threshold', 'narrow', 'obstacle'}
    
    positive_count = 0
    negative_count = 0
    
    for label in labels:
        label_name = label.get('name', '').lower()
        confidence = label.get('confidence', 0)
        
        # Weight by confidence
        weight = confidence / 100.0
        
        if any(feature in label_name for feature in positive_features):
            positive_count += weight
        elif any(feature in label_name for feature in negative_features):
            negative_count += weight
    
    # Calculate score (0-100)
    if positive_count + negative_count == 0:
        return 50
    
    score = int((positive_count / (positive_count + negative_count)) * 100)
    return max(0, min(100, score))

def categorize_labels(labels: List[Dict[str, Any]]) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Categorize labels into positive features and barriers.
    
    Args:
        labels: List of detected labels
        
    Returns:
        Tuple of (positive_features, barriers)
    """
    positive_features = []
    barriers = []
    
    positive_keywords = {'ramp', 'elevator', 'lift', 'handrail', 'grab bar', 'accessible', 'wide'}
    barrier_keywords = {'stairs', 'step', 'threshold', 'narrow', 'obstacle', 'clutter'}
    
    for label in labels:
        label_name = label.get('name', '').lower()
        
        if any(keyword in label_name for keyword in positive_keywords):
            positive_features.append(label)
        elif any(keyword in label_name for keyword in barrier_keywords):
            barriers.append(label)
    
    return positive_features, barriers

def generate_fallback_recommendations(
    positive_features: List[Dict[str, Any]], 
    barriers: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Generate fallback recommendations when LLM is unavailable.
    
    Args:
        positive_features: List of positive accessibility features
        barriers: List of identified barriers
        
    Returns:
        List of basic recommendations
    """
    recommendations = []
    
    # Add recommendations based on barriers found
    if barriers:
        recommendations.append({
            'title': 'Address Identified Barriers',
            'description': f'Consider modifications to address {len(barriers)} identified barriers',
            'priority': 'high',
            'category': 'safety'
        })
    
    # Add general recommendations
    if not positive_features:
        recommendations.append({
            'title': 'Add Accessibility Features',
            'description': 'Consider adding ramps, handrails, and other accessibility features',
            'priority': 'medium',
            'category': 'improvement'
        })
    
    return recommendations
