"""
Custom exceptions for the Accessibility Checker API.
Provides specific error types for different failure scenarios.
"""

from typing import Dict, Any, Optional
import json


class AccessibilityCheckerError(Exception):
    """Base exception for all Accessibility Checker errors."""
    
    def __init__(self, message: str, error_code: str = "GENERIC_ERROR", details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for JSON serialization."""
        return {
            "error": self.message,
            "error_code": self.error_code,
            "details": self.details
        }
    
    def to_json(self) -> str:
        """Convert exception to JSON string."""
        return json.dumps(self.to_dict())


class InvalidInputError(AccessibilityCheckerError):
    """Raised when input validation fails."""
    
    def __init__(self, message: str, field: Optional[str] = None, value: Optional[Any] = None):
        details = {}
        if field:
            details["field"] = field
        if value is not None:
            details["value"] = str(value)
        
        super().__init__(
            message=message,
            error_code="INVALID_INPUT",
            details=details
        )


class S3Error(AccessibilityCheckerError):
    """Raised when S3 operations fail."""
    
    def __init__(self, message: str, operation: str, bucket: Optional[str] = None, key: Optional[str] = None):
        details = {"operation": operation}
        if bucket:
            details["bucket"] = bucket
        if key:
            details["key"] = key
        
        super().__init__(
            message=message,
            error_code="S3_ERROR",
            details=details
        )


class RekognitionError(AccessibilityCheckerError):
    """Raised when Amazon Rekognition operations fail."""
    
    def __init__(self, message: str, operation: str, image_info: Optional[Dict[str, str]] = None):
        details = {"operation": operation}
        if image_info:
            details.update(image_info)
        
        super().__init__(
            message=message,
            error_code="REKOGNITION_ERROR",
            details=details
        )


class LLMError(AccessibilityCheckerError):
    """Raised when LLM operations fail."""
    
    def __init__(self, message: str, operation: str, model_id: Optional[str] = None):
        details = {"operation": operation}
        if model_id:
            details["model_id"] = model_id
        
        super().__init__(
            message=message,
            error_code="LLM_ERROR",
            details=details
        )


class LambdaInvocationError(AccessibilityCheckerError):
    """Raised when Lambda function invocation fails."""
    
    def __init__(self, message: str, function_name: str, invocation_type: str = "RequestResponse"):
        super().__init__(
            message=message,
            error_code="LAMBDA_INVOCATION_ERROR",
            details={
                "function_name": function_name,
                "invocation_type": invocation_type
            }
        )


class ServiceUnavailableError(AccessibilityCheckerError):
    """Raised when external services are unavailable."""
    
    def __init__(self, message: str, service: str, retry_after: Optional[int] = None):
        details = {"service": service}
        if retry_after:
            details["retry_after"] = retry_after
        
        super().__init__(
            message=message,
            error_code="SERVICE_UNAVAILABLE",
            details=details
        )


class RateLimitError(AccessibilityCheckerError):
    """Raised when rate limits are exceeded."""
    
    def __init__(self, message: str, service: str, retry_after: Optional[int] = None):
        details = {"service": service}
        if retry_after:
            details["retry_after"] = retry_after
        
        super().__init__(
            message=message,
            error_code="RATE_LIMIT_EXCEEDED",
            details=details
        )


class ValidationError(AccessibilityCheckerError):
    """Raised when data validation fails."""
    
    def __init__(self, message: str, field: str, expected_type: str, actual_value: Any):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            details={
                "field": field,
                "expected_type": expected_type,
                "actual_value": str(actual_value)
            }
        )


class ConfigurationError(AccessibilityCheckerError):
    """Raised when configuration is invalid or missing."""
    
    def __init__(self, message: str, config_key: str):
        super().__init__(
            message=message,
            error_code="CONFIGURATION_ERROR",
            details={"config_key": config_key}
        )


class TimeoutError(AccessibilityCheckerError):
    """Raised when operations timeout."""
    
    def __init__(self, message: str, operation: str, timeout_seconds: int):
        super().__init__(
            message=message,
            error_code="TIMEOUT_ERROR",
            details={
                "operation": operation,
                "timeout_seconds": timeout_seconds
            }
        )


class QuotaExceededError(AccessibilityCheckerError):
    """Raised when service quotas are exceeded."""
    
    def __init__(self, message: str, service: str, quota_type: str):
        super().__init__(
            message=message,
            error_code="QUOTA_EXCEEDED",
            details={
                "service": service,
                "quota_type": quota_type
            }
        )


def handle_aws_error(error: Exception, operation: str, service: str) -> AccessibilityCheckerError:
    """
    Convert AWS SDK errors to custom exceptions.
    
    Args:
        error: The original AWS error
        operation: The operation that failed
        service: The AWS service name
        
    Returns:
        Appropriate custom exception
    """
    error_message = str(error)
    error_code = getattr(error, 'response', {}).get('Error', {}).get('Code', 'UNKNOWN')
    
    if service == 's3':
        if 'NoSuchBucket' in error_code:
            return S3Error(f"S3 bucket not found: {error_message}", operation)
        elif 'NoSuchKey' in error_code:
            return S3Error(f"S3 object not found: {error_message}", operation)
        elif 'AccessDenied' in error_code:
            return S3Error(f"S3 access denied: {error_message}", operation)
        else:
            return S3Error(f"S3 operation failed: {error_message}", operation)
    
    elif service == 'rekognition':
        if 'InvalidParameter' in error_code:
            return RekognitionError(f"Invalid Rekognition parameters: {error_message}", operation)
        elif 'ImageTooLarge' in error_code:
            return RekognitionError(f"Image too large for Rekognition: {error_message}", operation)
        elif 'InvalidImageFormat' in error_code:
            return RekognitionError(f"Invalid image format: {error_message}", operation)
        else:
            return RekognitionError(f"Rekognition operation failed: {error_message}", operation)
    
    elif service == 'bedrock':
        if 'ModelNotAvailable' in error_code:
            return LLMError(f"Bedrock model not available: {error_message}", operation)
        elif 'ThrottlingException' in error_code:
            return RateLimitError(f"Bedrock rate limit exceeded: {error_message}", service)
        elif 'ValidationException' in error_code:
            return LLMError(f"Invalid Bedrock request: {error_message}", operation)
        else:
            return LLMError(f"Bedrock operation failed: {error_message}", operation)
    
    elif service == 'lambda':
        if 'ResourceNotFoundException' in error_code:
            return LambdaInvocationError(f"Lambda function not found: {error_message}", operation)
        elif 'TooManyRequestsException' in error_code:
            return RateLimitError(f"Lambda rate limit exceeded: {error_message}", service)
        else:
            return LambdaInvocationError(f"Lambda invocation failed: {error_message}", operation)
    
    else:
        return AccessibilityCheckerError(f"{service} operation failed: {error_message}", "AWS_ERROR")
