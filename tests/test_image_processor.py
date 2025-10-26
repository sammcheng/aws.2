"""
Tests for the ImageProcessor utility.
"""

import pytest
from unittest.mock import Mock, patch
import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.image_processor import ImageProcessor

class TestImageProcessor:
    """Test cases for the ImageProcessor utility."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_rekognition = Mock()
        self.mock_s3 = Mock()
        self.processor = ImageProcessor(self.mock_rekognition, self.mock_s3)
    
    def test_analyze_accessibility_features_success(self):
        """Test successful accessibility analysis."""
        # Mock Rekognition responses
        self.mock_rekognition.detect_objects.return_value = {
            'ObjectLabels': [
                {'Name': 'Chair', 'Confidence': 95.0},
                {'Name': 'Table', 'Confidence': 90.0}
            ]
        }
        
        self.mock_rekognition.detect_labels.return_value = {
            'Labels': [
                {'Name': 'Furniture', 'Confidence': 85.0},
                {'Name': 'Indoor', 'Confidence': 95.0}
            ]
        }
        
        # Call the method
        result = self.processor.analyze_accessibility_features('test-bucket', 'test-image.jpg')
        
        # Assertions
        assert 'objects' in result
        assert 'labels' in result
        assert 'accessibility_analysis' in result
        assert 'image_info' in result
        
        # Check accessibility analysis structure
        analysis = result['accessibility_analysis']
        assert 'accessibility_features' in analysis
        assert 'potential_barriers' in analysis
        assert 'summary' in analysis
    
    def test_analyze_accessibility_features_with_ramp(self):
        """Test analysis with accessibility features like ramps."""
        # Mock Rekognition responses with accessibility features
        self.mock_rekognition.detect_objects.return_value = {
            'ObjectLabels': [
                {'Name': 'Ramp', 'Confidence': 95.0},
                {'Name': 'Handrail', 'Confidence': 90.0}
            ]
        }
        
        self.mock_rekognition.detect_labels.return_value = {
            'Labels': [
                {'Name': 'Accessible', 'Confidence': 85.0},
                {'Name': 'Wheelchair', 'Confidence': 80.0}
            ]
        }
        
        # Call the method
        result = self.processor.analyze_accessibility_features('test-bucket', 'test-image.jpg')
        
        # Check that accessibility features are detected
        analysis = result['accessibility_analysis']
        features = analysis['accessibility_features']
        
        # Should have detected ramp and handrail as accessibility features
        feature_names = [f['name'] for f in features]
        assert 'Ramp' in feature_names
        assert 'Handrail' in feature_names
    
    def test_analyze_accessibility_features_with_barriers(self):
        """Test analysis with potential barriers."""
        # Mock Rekognition responses with barriers
        self.mock_rekognition.detect_objects.return_value = {
            'ObjectLabels': [
                {'Name': 'Step', 'Confidence': 95.0},
                {'Name': 'Narrow Doorway', 'Confidence': 90.0}
            ]
        }
        
        self.mock_rekognition.detect_labels.return_value = {
            'Labels': [
                {'Name': 'Stairs', 'Confidence': 85.0},
                {'Name': 'Obstacle', 'Confidence': 80.0}
            ]
        }
        
        # Call the method
        result = self.processor.analyze_accessibility_features('test-bucket', 'test-image.jpg')
        
        # Check that barriers are detected
        analysis = result['accessibility_analysis']
        barriers = analysis['potential_barriers']
        
        # Should have detected step and narrow doorway as barriers
        barrier_names = [b['name'] for b in barriers]
        assert 'Step' in barrier_names
        assert 'Narrow Doorway' in barrier_names
    
    def test_calculate_accessibility_score(self):
        """Test accessibility score calculation."""
        # Test with features and barriers
        features = [
            {'name': 'Ramp', 'confidence': 95.0},
            {'name': 'Handrail', 'confidence': 90.0}
        ]
        barriers = [
            {'name': 'Step', 'confidence': 85.0}
        ]
        
        score = self.processor._calculate_accessibility_score(features, barriers)
        
        # Should be positive due to more features than barriers
        assert score > 50
        assert 0 <= score <= 100
    
    def test_calculate_accessibility_score_no_data(self):
        """Test accessibility score with no data."""
        score = self.processor._calculate_accessibility_score([], [])
        
        # Should return neutral score
        assert score == 50.0
    
    def test_detect_objects_error(self):
        """Test error handling in object detection."""
        # Mock Rekognition to raise exception
        self.mock_rekognition.detect_objects.side_effect = Exception("Rekognition error")
        self.mock_rekognition.detect_labels.return_value = {'Labels': []}
        
        # Should not raise exception, should return empty objects
        result = self.processor.analyze_accessibility_features('test-bucket', 'test-image.jpg')
        
        assert result['objects'] == []
    
    def test_detect_labels_error(self):
        """Test error handling in label detection."""
        # Mock Rekognition to raise exception
        self.mock_rekognition.detect_objects.return_value = {'ObjectLabels': []}
        self.mock_rekognition.detect_labels.side_effect = Exception("Rekognition error")
        
        # Should not raise exception, should return empty labels
        result = self.processor.analyze_accessibility_features('test-bucket', 'test-image.jpg')
        
        assert result['labels'] == []
