"""
AWS Lambda handler for processing images with Amazon Rekognition
to detect accessibility-relevant labels in home environments.
"""

import json
import boto3
import logging
from typing import Dict, Any, List

# Configure CloudWatch logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for detecting accessibility-relevant labels in images.
    
    Args:
        event: Lambda event containing {"bucket": "bucket-name", "key": "image-key"}
        context: Lambda context object
        
    Returns:
        Dict containing detected labels and image key
    """
    try:
        # Log the incoming event for debugging
        logger.info(f"Processing event: {json.dumps(event)}")
        
        # Extract image data from event
        bucket_name = event.get('bucket')
        image_key = event.get('key')
        
        # Validate required parameters
        if not bucket_name:
            logger.error("Missing 'bucket' in event")
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Missing bucket in event'})
            }
        
        if not image_key:
            logger.error("Missing 'key' in event")
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Missing key in event'})
            }
        
        logger.info(f"Processing image: s3://{bucket_name}/{image_key}")
        
        # Initialize Rekognition client
        rekognition = boto3.client('rekognition')
        
        # Call Rekognition to detect labels
        response = rekognition.detect_labels(
            Image={'S3Object': {'Bucket': bucket_name, 'Name': image_key}},
            MaxLabels=50,
            MinConfidence=70
        )
        
        logger.info(f"Rekognition detected {len(response.get('Labels', []))} labels")
        
        # Filter labels for accessibility-relevant ones
        accessibility_labels = filter_accessibility_labels(response.get('Labels', []))
        
        logger.info(f"Found {len(accessibility_labels)} accessibility-relevant labels")
        
        # Return the filtered results
        return {
            'statusCode': 200,
            'body': json.dumps({
                'labels': accessibility_labels,
                'image_key': image_key
            })
        }
        
    except Exception as e:
        logger.error(f"Error processing image: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Internal server error',
                'message': str(e)
            })
        }

def filter_accessibility_labels(labels: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Filter labels to only include accessibility-relevant ones.
    
    Args:
        labels: List of labels from Rekognition
        
    Returns:
        List of filtered accessibility-relevant labels
    """
    # Define accessibility-relevant keywords
    accessibility_keywords = {
        'stairs', 'ramp', 'door', 'doorway', 'bathroom', 'bedroom', 
        'kitchen', 'hallway', 'entrance', 'elevator', 'lift', 
        'wheelchair', 'grab bar', 'handrail', 'step', 'threshold'
    }
    
    filtered_labels = []
    
    for label in labels:
        label_name = label.get('Name', '').lower()
        confidence = label.get('Confidence', 0)
        
        # Check if label name contains any accessibility keywords
        if any(keyword in label_name for keyword in accessibility_keywords):
            filtered_labels.append({
                'name': label.get('Name'),
                'confidence': round(confidence, 2),
                'category': 'accessibility'
            })
            logger.info(f"Found accessibility label: {label.get('Name')} (confidence: {confidence:.2f}%)")
    
    return filtered_labels
