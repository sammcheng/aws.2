"""
Input validation models and utilities for the Accessibility Checker API.
Uses Pydantic for robust data validation and serialization.
"""

from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field, validator, root_validator
import re
from utils.exceptions import InvalidInputError, ValidationError


class ImageInfo(BaseModel):
    """Model for image information."""
    bucket: str = Field(..., min_length=1, max_length=63, description="S3 bucket name")
    key: str = Field(..., min_length=1, max_length=1024, description="S3 object key")
    
    @validator('bucket')
    def validate_bucket_name(cls, v):
        """Validate S3 bucket name format."""
        if not re.match(r'^[a-z0-9][a-z0-9\-]*[a-z0-9]$', v):
            raise InvalidInputError(
                "Invalid bucket name format",
                field="bucket",
                value=v
            )
        return v
    
    @validator('key')
    def validate_key_format(cls, v):
        """Validate S3 key format."""
        if v.startswith('/') or v.endswith('/'):
            raise InvalidInputError(
                "S3 key cannot start or end with '/'",
                field="key",
                value=v
            )
        return v


class PresignedUrlRequest(BaseModel):
    """Model for presigned URL generation request."""
    filename: str = Field(..., min_length=1, max_length=255, description="Original filename")
    content_type: str = Field(..., description="MIME type of the file")
    
    @validator('filename')
    def validate_filename(cls, v):
        """Validate filename for security."""
        # Check for dangerous characters
        dangerous_chars = ['..', '/', '\\', '<', '>', ':', '"', '|', '?', '*']
        if any(char in v for char in dangerous_chars):
            raise InvalidInputError(
                "Filename contains dangerous characters",
                field="filename",
                value=v
            )
        return v
    
    @validator('content_type')
    def validate_content_type(cls, v):
        """Validate content type."""
        allowed_types = {
            'image/jpeg', 'image/jpg', 'image/png', 'image/webp'
        }
        if v not in allowed_types:
            raise InvalidInputError(
                f"Unsupported content type. Allowed: {', '.join(allowed_types)}",
                field="content_type",
                value=v
            )
        return v


class AnalyzeRequest(BaseModel):
    """Model for image analysis request."""
    images: List[ImageInfo] = Field(..., min_items=1, max_items=10, description="List of images to analyze")
    
    @validator('images')
    def validate_images_not_empty(cls, v):
        """Validate that images list is not empty."""
        if not v:
            raise InvalidInputError("Images list cannot be empty", field="images")
        return v


class RekognitionRequest(BaseModel):
    """Model for Rekognition processing request."""
    bucket: str = Field(..., min_length=1, max_length=63, description="S3 bucket name")
    key: str = Field(..., min_length=1, max_length=1024, description="S3 object key")
    
    @validator('bucket')
    def validate_bucket_name(cls, v):
        """Validate S3 bucket name format."""
        if not re.match(r'^[a-z0-9][a-z0-9\-]*[a-z0-9]$', v):
            raise InvalidInputError(
                "Invalid bucket name format",
                field="bucket",
                value=v
            )
        return v


class LLMRequest(BaseModel):
    """Model for LLM processing request."""
    rekognition_results: Dict[str, Any] = Field(..., description="Results from Rekognition analysis")
    image_metadata: Dict[str, Any] = Field(..., description="Image metadata")
    
    @validator('rekognition_results')
    def validate_rekognition_results(cls, v):
        """Validate that rekognition results contain required fields."""
        if not isinstance(v, dict):
            raise InvalidInputError(
                "Rekognition results must be a dictionary",
                field="rekognition_results",
                value=type(v).__name__
            )
        return v


class LabelInfo(BaseModel):
    """Model for detected label information."""
    name: str = Field(..., min_length=1, max_length=100, description="Label name")
    confidence: float = Field(..., ge=0, le=100, description="Confidence score (0-100)")
    category: str = Field(default="accessibility", description="Label category")
    
    @validator('confidence')
    def validate_confidence_range(cls, v):
        """Validate confidence is within valid range."""
        if not 0 <= v <= 100:
            raise ValidationError(
                "Confidence must be between 0 and 100",
                field="confidence",
                expected_type="float (0-100)",
                actual_value=v
            )
        return round(v, 2)


class AccessibilityFeature(BaseModel):
    """Model for accessibility feature."""
    name: str = Field(..., min_length=1, max_length=100, description="Feature name")
    confidence: float = Field(..., ge=0, le=100, description="Confidence score")
    feature_type: str = Field(..., description="Type of accessibility feature")
    
    @validator('feature_type')
    def validate_feature_type(cls, v):
        """Validate feature type."""
        allowed_types = {'ramp', 'elevator', 'handrail', 'grab_bar', 'accessible_door', 'wide_hallway'}
        if v not in allowed_types:
            raise InvalidInputError(
                f"Invalid feature type. Allowed: {', '.join(allowed_types)}",
                field="feature_type",
                value=v
            )
        return v


class Barrier(BaseModel):
    """Model for accessibility barrier."""
    name: str = Field(..., min_length=1, max_length=100, description="Barrier name")
    confidence: float = Field(..., ge=0, le=100, description="Confidence score")
    barrier_type: str = Field(..., description="Type of barrier")
    
    @validator('barrier_type')
    def validate_barrier_type(cls, v):
        """Validate barrier type."""
        allowed_types = {'stairs', 'step', 'threshold', 'narrow_doorway', 'obstacle', 'clutter'}
        if v not in allowed_types:
            raise InvalidInputError(
                f"Invalid barrier type. Allowed: {', '.join(allowed_types)}",
                field="barrier_type",
                value=v
            )
        return v


class Recommendation(BaseModel):
    """Model for accessibility recommendation."""
    title: str = Field(..., min_length=1, max_length=200, description="Recommendation title")
    description: str = Field(..., min_length=1, max_length=1000, description="Detailed description")
    priority: str = Field(..., description="Priority level")
    category: str = Field(..., description="Recommendation category")
    estimated_cost: Optional[str] = Field(None, description="Estimated cost")
    
    @validator('priority')
    def validate_priority(cls, v):
        """Validate priority level."""
        allowed_priorities = {'low', 'medium', 'high', 'critical'}
        if v not in allowed_priorities:
            raise InvalidInputError(
                f"Invalid priority. Allowed: {', '.join(allowed_priorities)}",
                field="priority",
                value=v
            )
        return v
    
    @validator('category')
    def validate_category(cls, v):
        """Validate category."""
        allowed_categories = {'safety', 'mobility', 'vision', 'hearing', 'cognitive', 'general'}
        if v not in allowed_categories:
            raise InvalidInputError(
                f"Invalid category. Allowed: {', '.join(allowed_categories)}",
                field="category",
                value=v
            )
        return v


class Improvement(BaseModel):
    """Model for improvement suggestion."""
    title: str = Field(..., min_length=1, max_length=200, description="Improvement title")
    description: str = Field(..., min_length=1, max_length=1000, description="Detailed description")
    implementation_difficulty: str = Field(..., description="Implementation difficulty")
    category: str = Field(..., description="Improvement category")
    estimated_impact: Optional[str] = Field(None, description="Estimated impact")
    
    @validator('implementation_difficulty')
    def validate_difficulty(cls, v):
        """Validate implementation difficulty."""
        allowed_difficulties = {'easy', 'moderate', 'complex', 'expert'}
        if v not in allowed_difficulties:
            raise InvalidInputError(
                f"Invalid difficulty. Allowed: {', '.join(allowed_difficulties)}",
                field="implementation_difficulty",
                value=v
            )
        return v


class AssessmentResponse(BaseModel):
    """Model for final accessibility assessment response."""
    score: int = Field(..., ge=0, le=100, description="Accessibility score (0-100)")
    analyzed_images: int = Field(..., ge=1, description="Number of images analyzed")
    positive_features: List[AccessibilityFeature] = Field(default_factory=list, description="Positive accessibility features")
    barriers: List[Barrier] = Field(default_factory=list, description="Identified barriers")
    recommendations: List[Recommendation] = Field(default_factory=list, description="Recommendations")
    total_labels: int = Field(..., ge=0, description="Total number of labels detected")
    analysis_timestamp: Optional[str] = Field(None, description="Analysis timestamp")
    
    @validator('score')
    def validate_score_range(cls, v):
        """Validate score is within valid range."""
        if not 0 <= v <= 100:
            raise ValidationError(
                "Score must be between 0 and 100",
                field="score",
                expected_type="int (0-100)",
                actual_value=v
            )
        return v


def validate_event_structure(event: Dict[str, Any], required_fields: List[str]) -> None:
    """
    Validate that event contains required fields.
    
    Args:
        event: The event dictionary to validate
        required_fields: List of required field names
        
    Raises:
        InvalidInputError: If required fields are missing
    """
    missing_fields = [field for field in required_fields if field not in event]
    if missing_fields:
        raise InvalidInputError(
            f"Missing required fields: {', '.join(missing_fields)}",
            field="event",
            value=list(event.keys())
        )


def validate_file_size(size_bytes: int, max_size_mb: int = 10) -> None:
    """
    Validate file size is within limits.
    
    Args:
        size_bytes: File size in bytes
        max_size_mb: Maximum allowed size in MB
        
    Raises:
        InvalidInputError: If file size exceeds limit
    """
    max_size_bytes = max_size_mb * 1024 * 1024
    if size_bytes > max_size_bytes:
        raise InvalidInputError(
            f"File size {size_bytes} bytes exceeds maximum allowed size of {max_size_mb}MB",
            field="file_size",
            value=size_bytes
        )


def validate_image_dimensions(width: int, height: int, max_dimension: int = 4096) -> None:
    """
    Validate image dimensions are within limits.
    
    Args:
        width: Image width in pixels
        height: Image height in pixels
        max_dimension: Maximum allowed dimension
        
    Raises:
        InvalidInputError: If dimensions exceed limits
    """
    if width > max_dimension or height > max_dimension:
        raise InvalidInputError(
            f"Image dimensions {width}x{height} exceed maximum allowed dimension of {max_dimension}px",
            field="image_dimensions",
            value=f"{width}x{height}"
        )
