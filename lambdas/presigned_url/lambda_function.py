"""
AWS Lambda function for generating presigned S3 upload URLs.
Provides secure, temporary upload URLs for frontend file uploads.
"""

import json
import boto3
import uuid
import os
import time
from typing import Dict, Any
from urllib.parse import urlparse

# Import custom modules
from utils.structured_logger import get_logger, create_request_context
from utils.exceptions import (
    InvalidInputError, S3Error, ValidationError, 
    handle_aws_error, AccessibilityCheckerError
)
from utils.validation import PresignedUrlRequest, validate_file_size

# Initialize structured logger
logger = get_logger(__name__)

# Initialize AWS clients
s3_client = boto3.client('s3')

# Configuration
S3_BUCKET = os.environ.get('S3_BUCKET_NAME', 'accessibility-checker-uploads')
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB in bytes
EXPIRATION_SECONDS = 300  # 5 minutes

# Allowed file types
ALLOWED_CONTENT_TYPES = {
    'image/jpeg',
    'image/jpg', 
    'image/png',
    'image/webp'
}

ALLOWED_EXTENSIONS = {
    '.jpg',
    '.jpeg',
    '.png',
    '.webp'
}

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Generate presigned S3 upload URL for frontend file uploads.
    
    Args:
        event: Lambda event containing {"filename": "house1.jpg", "content_type": "image/jpeg"}
        context: Lambda context object
        
    Returns:
        Dict containing upload URL, fields, and generated key
    """
    request_id = getattr(context, 'aws_request_id', 'unknown')
    
    with create_request_context(request_id, 'presigned-url-generator') as ctx:
        try:
            # Log the incoming event for debugging
            ctx.log_operation('input_validation', f"Processing presigned URL request: {json.dumps(event)}")
            
            # Validate input using Pydantic model
            try:
                request_data = PresignedUrlRequest(**event)
            except Exception as validation_error:
                ctx.log_error('input_validation', f"Input validation failed: {str(validation_error)}")
                return create_error_response(400, InvalidInputError(
                    f"Input validation failed: {str(validation_error)}",
                    field="event"
                ))
            
            # Generate unique key to prevent collisions
            unique_key = generate_unique_key(request_data.filename)
            
            ctx.log_operation('key_generation', f"Generated unique key: {unique_key}")
            
            # Generate presigned POST URL
            try:
                presigned_data = generate_presigned_post(unique_key, request_data.content_type)
                ctx.log_operation('presigned_generation', f"Successfully generated presigned URL for: {unique_key}")
                
                return {
                    'statusCode': 200,
                    'body': json.dumps({
                        'upload_url': presigned_data['url'],
                        'fields': presigned_data['fields'],
                        'key': unique_key,
                        'expires_in': EXPIRATION_SECONDS
                    })
                }
                
            except Exception as s3_error:
                ctx.log_error('s3_operation', f"S3 operation failed: {str(s3_error)}", s3_error)
                return create_error_response(500, S3Error(
                    f"Failed to generate presigned URL: {str(s3_error)}",
                    operation="generate_presigned_post",
                    bucket=S3_BUCKET,
                    key=unique_key
                ))
                
        except AccessibilityCheckerError as custom_error:
            ctx.log_error('custom_error', f"Custom error: {custom_error.message}", custom_error)
            return create_error_response(400, custom_error)
            
        except Exception as e:
            ctx.log_error('unexpected_error', f"Unexpected error: {str(e)}", e)
            return create_error_response(500, AccessibilityCheckerError(
                f"Internal server error: {str(e)}",
                error_code="INTERNAL_ERROR"
            ))

def is_valid_file_type(filename: str, content_type: str) -> bool:
    """
    Validate that the file type is allowed.
    
    Args:
        filename: Name of the file
        content_type: MIME type of the file
        
    Returns:
        True if file type is allowed, False otherwise
    """
    # Check content type
    if content_type not in ALLOWED_CONTENT_TYPES:
        return False
    
    # Check file extension
    filename_lower = filename.lower()
    if not any(filename_lower.endswith(ext) for ext in ALLOWED_EXTENSIONS):
        return False
    
    return True

def generate_unique_key(filename: str) -> str:
    """
    Generate a unique S3 key to prevent collisions.
    
    Args:
        filename: Original filename
        
    Returns:
        Unique S3 key with UUID prefix
    """
    # Generate UUID for uniqueness
    unique_id = str(uuid.uuid4())
    
    # Extract file extension
    file_extension = os.path.splitext(filename)[1].lower()
    
    # Create unique key: uploads/uuid-filename
    unique_key = f"uploads/{unique_id}-{filename}"
    
    logger.info(f"Generated unique key: {unique_key}")
    return unique_key

def create_error_response(status_code: int, error: AccessibilityCheckerError) -> Dict[str, Any]:
    """
    Create standardized error response.
    
    Args:
        status_code: HTTP status code
        error: Custom exception
        
    Returns:
        Error response dictionary
    """
    return {
        'statusCode': status_code,
        'body': error.to_json()
    }


def generate_presigned_post(key: str, content_type: str) -> Dict[str, Any]:
    """
    Generate presigned POST data for S3 upload.
    
    Args:
        key: S3 object key
        content_type: MIME type of the file
        
    Returns:
        Presigned POST data with URL and fields
    """
    try:
        # Generate presigned POST
        presigned_data = s3_client.generate_presigned_post(
            Bucket=S3_BUCKET,
            Key=key,
            Fields={
                'Content-Type': content_type
            },
            Conditions=[
                {'Content-Type': content_type},
                ['content-length-range', 1, MAX_FILE_SIZE],
                {'key': key}
            ],
            ExpiresIn=EXPIRATION_SECONDS
        )
        
        logger.info(f"Generated presigned POST for key: {key}")
        return presigned_data
        
    except Exception as e:
        logger.error(f"Failed to generate presigned POST: {str(e)}")
        # Convert AWS error to custom exception
        raise handle_aws_error(e, "generate_presigned_post", "s3")

def validate_filename(filename: str) -> bool:
    """
    Validate filename for security and length.
    
    Args:
        filename: Name of the file
        
    Returns:
        True if filename is valid, False otherwise
    """
    if not filename:
        return False
    
    # Check length (reasonable limit)
    if len(filename) > 255:
        return False
    
    # Check for dangerous characters
    dangerous_chars = ['..', '/', '\\', '<', '>', ':', '"', '|', '?', '*']
    if any(char in filename for char in dangerous_chars):
        return False
    
    return True

def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to remove potentially dangerous characters.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    # Remove or replace dangerous characters
    sanitized = filename
    
    # Replace dangerous characters with underscores
    dangerous_chars = ['..', '/', '\\', '<', '>', ':', '"', '|', '?', '*']
    for char in dangerous_chars:
        sanitized = sanitized.replace(char, '_')
    
    # Remove multiple consecutive underscores
    while '__' in sanitized:
        sanitized = sanitized.replace('__', '_')
    
    # Ensure filename is not empty
    if not sanitized or sanitized == '_':
        sanitized = f"file_{uuid.uuid4().hex[:8]}"
    
    return sanitized
