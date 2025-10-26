"""
Image processing utility for analyzing accessibility features
using Amazon Rekognition.
"""

import boto3
from typing import Dict, Any, List, Optional
from utils.logger import get_logger

logger = get_logger(__name__)

class ImageProcessor:
    """Handles image processing and accessibility analysis."""
    
    def __init__(self, rekognition_client, s3_client):
        """
        Initialize the image processor.
        
        Args:
            rekognition_client: Boto3 Rekognition client
            s3_client: Boto3 S3 client
        """
        self.rekognition = rekognition_client
        self.s3 = s3_client
    
    def analyze_accessibility_features(self, bucket: str, key: str) -> Dict[str, Any]:
        """
        Analyze an image for accessibility features and barriers.
        
        Args:
            bucket: S3 bucket name
            key: S3 object key
            
        Returns:
            Dict containing analysis results
        """
        try:
            # Detect objects and labels
            objects = self._detect_objects(bucket, key)
            labels = self._detect_labels(bucket, key)
            
            # Analyze for accessibility features
            accessibility_analysis = self._analyze_accessibility(objects, labels)
            
            return {
                'objects': objects,
                'labels': labels,
                'accessibility_analysis': accessibility_analysis,
                'image_info': {
                    'bucket': bucket,
                    'key': key
                }
            }
            
        except Exception as e:
            logger.error(f"Error analyzing image {key}: {str(e)}")
            raise
    
    def _detect_objects(self, bucket: str, key: str) -> List[Dict[str, Any]]:
        """Detect objects in the image."""
        try:
            response = self.rekognition.detect_objects(
                Image={'S3Object': {'Bucket': bucket, 'Name': key}}
            )
            return response.get('ObjectLabels', [])
        except Exception as e:
            logger.error(f"Error detecting objects: {str(e)}")
            return []
    
    def _detect_labels(self, bucket: str, key: str) -> List[Dict[str, Any]]:
        """Detect labels in the image."""
        try:
            response = self.rekognition.detect_labels(
                Image={'S3Object': {'Bucket': bucket, 'Name': key}},
                MaxLabels=50,
                MinConfidence=70
            )
            return response.get('Labels', [])
        except Exception as e:
            logger.error(f"Error detecting labels: {str(e)}")
            return []
    
    def _analyze_accessibility(self, objects: List[Dict], labels: List[Dict]) -> Dict[str, Any]:
        """
        Analyze detected objects and labels for accessibility features.
        
        Args:
            objects: List of detected objects
            labels: List of detected labels
            
        Returns:
            Dict containing accessibility analysis
        """
        accessibility_features = []
        potential_barriers = []
        
        # Check for accessibility features
        accessibility_keywords = [
            'ramp', 'elevator', 'handrail', 'grab bar', 'accessible',
            'wheelchair', 'mobility', 'assistive'
        ]
        
        # Check for potential barriers
        barrier_keywords = [
            'step', 'stairs', 'narrow', 'obstacle', 'clutter',
            'uneven', 'slippery', 'high'
        ]
        
        # Analyze objects
        for obj in objects:
            obj_name = obj.get('Name', '').lower()
            confidence = obj.get('Confidence', 0)
            
            if any(keyword in obj_name for keyword in accessibility_keywords):
                accessibility_features.append({
                    'type': 'accessibility_feature',
                    'name': obj.get('Name'),
                    'confidence': confidence
                })
            
            if any(keyword in obj_name for keyword in barrier_keywords):
                potential_barriers.append({
                    'type': 'potential_barrier',
                    'name': obj.get('Name'),
                    'confidence': confidence
                })
        
        # Analyze labels
        for label in labels:
            label_name = label.get('Name', '').lower()
            confidence = label.get('Confidence', 0)
            
            if any(keyword in label_name for keyword in accessibility_keywords):
                accessibility_features.append({
                    'type': 'accessibility_feature',
                    'name': label.get('Name'),
                    'confidence': confidence
                })
            
            if any(keyword in label_name for keyword in barrier_keywords):
                potential_barriers.append({
                    'type': 'potential_barrier',
                    'name': label.get('Name'),
                    'confidence': confidence
                })
        
        return {
            'accessibility_features': accessibility_features,
            'potential_barriers': potential_barriers,
            'summary': {
                'total_features': len(accessibility_features),
                'total_barriers': len(potential_barriers),
                'accessibility_score': self._calculate_accessibility_score(
                    accessibility_features, potential_barriers
                )
            }
        }
    
    def _calculate_accessibility_score(self, features: List[Dict], barriers: List[Dict]) -> float:
        """
        Calculate an accessibility score based on features and barriers.
        
        Args:
            features: List of accessibility features
            barriers: List of potential barriers
            
        Returns:
            Accessibility score (0-100)
        """
        if not features and not barriers:
            return 50.0  # Neutral score for no data
        
        # Weight features more heavily than barriers
        feature_score = len(features) * 10
        barrier_penalty = len(barriers) * 5
        
        score = max(0, min(100, 50 + feature_score - barrier_penalty))
        return round(score, 1)
