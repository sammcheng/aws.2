# Error Handling & Validation Guide

This document describes the comprehensive error handling and validation system implemented across all Lambda functions in the Accessibility Checker API.

## 🛡️ Error Handling Architecture

### Custom Exception Hierarchy
```
AccessibilityCheckerError (Base)
├── InvalidInputError
├── S3Error
├── RekognitionError
├── LLMError
├── LambdaInvocationError
├── ServiceUnavailableError
├── RateLimitError
├── ValidationError
├── ConfigurationError
├── TimeoutError
└── QuotaExceededError
```

### HTTP Status Code Mapping
- **400 Bad Request**: Invalid input, validation errors
- **500 Internal Server Error**: Unexpected errors, system failures
- **503 Service Unavailable**: External service failures, rate limits

## 🔍 Input Validation

### Pydantic Models
All Lambda functions use Pydantic models for robust input validation:

```python
# Presigned URL Request
class PresignedUrlRequest(BaseModel):
    filename: str = Field(..., min_length=1, max_length=255)
    content_type: str = Field(..., description="MIME type")
    
    @validator('content_type')
    def validate_content_type(cls, v):
        allowed_types = {'image/jpeg', 'image/png', 'image/webp'}
        if v not in allowed_types:
            raise InvalidInputError("Unsupported content type")
        return v

# Image Analysis Request
class AnalyzeRequest(BaseModel):
    images: List[ImageInfo] = Field(..., min_items=1, max_items=10)
    
    @validator('images')
    def validate_images_not_empty(cls, v):
        if not v:
            raise InvalidInputError("Images list cannot be empty")
        return v
```

### Validation Features
- **Type checking**: Automatic type validation
- **Range validation**: Min/max values for numeric fields
- **Format validation**: Regex patterns for strings
- **Custom validators**: Business logic validation
- **Security validation**: Filename sanitization, dangerous character detection

## 📊 Structured Logging

### Log Entry Format
```json
{
  "timestamp": "2023-12-01T10:30:00Z",
  "level": "ERROR",
  "message": "S3 operation failed",
  "service": "accessibility-checker-api",
  "request_id": "abc-123-def",
  "function_name": "presigned-url-generator",
  "operation": "generate_presigned_post",
  "error_type": "S3Error",
  "duration_ms": 150.5,
  "error_code": "S3_ERROR",
  "error_details": {
    "operation": "generate_presigned_post",
    "bucket": "my-bucket",
    "key": "uploads/file.jpg"
  },
  "exception": {
    "type": "ClientError",
    "message": "The specified bucket does not exist"
  }
}
```

### Contextual Information
- **Request ID**: Unique identifier for request tracing
- **Function Name**: Lambda function that generated the log
- **Operation**: Specific operation being performed
- **Error Type**: Categorized error type
- **Duration**: Performance metrics
- **Exception Details**: Full exception information

## 🚨 Error Monitoring

### CloudWatch Alarms
- **Error Rate Alarms**: Trigger when error count exceeds threshold
- **Duration Alarms**: Monitor function execution time
- **Throttle Alarms**: Detect rate limiting issues
- **DLQ Alarms**: Monitor dead letter queue messages

### Alarm Configuration
```yaml
PresignedUrlErrorAlarm:
  Type: AWS::CloudWatch::Alarm
  Properties:
    MetricName: Errors
    Namespace: AWS/Lambda
    Statistic: Sum
    Period: 300
    EvaluationPeriods: 2
    Threshold: 5
    ComparisonOperator: GreaterThanThreshold
```

### SNS Notifications
- **Error Notifications**: Real-time alerts for critical errors
- **Escalation Policies**: Different notification channels for different error types
- **Digest Notifications**: Periodic summaries of error patterns

## 🔄 Dead Letter Queues

### DLQ Configuration
```yaml
DeadLetterQueue:
  Type: AWS::SQS::Queue
  Properties:
    QueueName: accessibility-checker-dlq
    MessageRetentionPeriod: 1209600  # 14 days
    VisibilityTimeoutSeconds: 60
```

### DLQ Processing
- **Failed Lambda Invocations**: Automatically sent to DLQ
- **Retry Logic**: Configurable retry attempts
- **Dead Letter Processing**: Manual intervention for failed messages
- **Monitoring**: CloudWatch metrics for DLQ depth

## 🛠️ Error Response Format

### Standardized Error Response
```json
{
  "statusCode": 400,
  "body": {
    "error": "Invalid input validation failed",
    "error_code": "INVALID_INPUT",
    "details": {
      "field": "filename",
      "value": "invalid-file.exe"
    }
  }
}
```

### Error Categories

#### Input Validation Errors (400)
```json
{
  "error": "Input validation failed",
  "error_code": "INVALID_INPUT",
  "details": {
    "field": "content_type",
    "value": "application/pdf"
  }
}
```

#### Service Errors (500)
```json
{
  "error": "S3 operation failed",
  "error_code": "S3_ERROR",
  "details": {
    "operation": "generate_presigned_post",
    "bucket": "my-bucket",
    "key": "uploads/file.jpg"
  }
}
```

#### Service Unavailable (503)
```json
{
  "error": "External service unavailable",
  "error_code": "SERVICE_UNAVAILABLE",
  "details": {
    "service": "rekognition",
    "retry_after": 30
  }
}
```

## 🔧 Error Handling Best Practices

### 1. Graceful Degradation
- Continue processing when non-critical services fail
- Provide fallback responses when possible
- Log errors for later analysis

### 2. Retry Logic
- Implement exponential backoff for transient failures
- Set maximum retry attempts
- Distinguish between retryable and non-retryable errors

### 3. Error Context
- Include relevant context in error messages
- Log request IDs for tracing
- Provide actionable error information

### 4. Security
- Sanitize error messages to prevent information leakage
- Log security-relevant events
- Implement rate limiting for error responses

## 📈 Monitoring and Alerting

### Key Metrics
- **Error Rate**: Percentage of failed requests
- **Error Count**: Absolute number of errors
- **Duration**: Function execution time
- **Throttles**: Rate limiting events
- **DLQ Depth**: Number of messages in dead letter queue

### Alert Thresholds
- **Error Rate**: > 5% over 5 minutes
- **Error Count**: > 5 errors in 5 minutes
- **Duration**: > 30 seconds execution time
- **DLQ Depth**: > 10 messages

### Dashboard Queries
```sql
-- Error rate by function
SELECT function_name, 
       COUNT(*) as total_requests,
       SUM(CASE WHEN error_code IS NOT NULL THEN 1 ELSE 0 END) as errors,
       (SUM(CASE WHEN error_code IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*)) * 100 as error_rate
FROM cloudwatch_logs
WHERE timestamp >= NOW() - INTERVAL 1 HOUR
GROUP BY function_name

-- Top error types
SELECT error_code, COUNT(*) as count
FROM cloudwatch_logs
WHERE error_code IS NOT NULL
  AND timestamp >= NOW() - INTERVAL 1 HOUR
GROUP BY error_code
ORDER BY count DESC
```

## 🧪 Testing Error Scenarios

### Unit Tests
```python
def test_invalid_input_error():
    """Test handling of invalid input."""
    event = {"filename": "", "content_type": "image/jpeg"}
    response = lambda_handler(event, context)
    
    assert response['statusCode'] == 400
    body = json.loads(response['body'])
    assert body['error_code'] == 'INVALID_INPUT'

def test_s3_error_handling():
    """Test S3 error handling."""
    with patch('boto3.client') as mock_client:
        mock_client.side_effect = ClientError(
            {'Error': {'Code': 'NoSuchBucket'}}, 'GetObject'
        )
        
        response = lambda_handler(event, context)
        assert response['statusCode'] == 500
```

### Integration Tests
```python
def test_end_to_end_error_flow():
    """Test complete error handling flow."""
    # Test invalid input
    response = test_client.post('/presigned-url', json={
        "filename": "test.exe",
        "content_type": "application/exe"
    })
    
    assert response.status_code == 400
    assert 'INVALID_INPUT' in response.json()['error_code']
```

## 🔍 Debugging Guide

### Common Error Scenarios

1. **Input Validation Failures**
   - Check Pydantic model validation
   - Verify field types and constraints
   - Review custom validators

2. **AWS Service Errors**
   - Check IAM permissions
   - Verify resource existence
   - Review service quotas

3. **Timeout Errors**
   - Check function timeout settings
   - Optimize function performance
   - Review external service response times

4. **Rate Limiting**
   - Check service quotas
   - Implement exponential backoff
   - Consider request batching

### Debugging Tools
- **CloudWatch Logs**: Detailed error logs with context
- **X-Ray Tracing**: Request flow analysis
- **CloudWatch Metrics**: Performance and error metrics
- **DLQ Messages**: Failed request details

## 📚 Error Handling Checklist

- [ ] Input validation with Pydantic models
- [ ] Custom exception hierarchy
- [ ] Structured logging with context
- [ ] Dead letter queue configuration
- [ ] CloudWatch alarms for error monitoring
- [ ] SNS notifications for critical errors
- [ ] Error response standardization
- [ ] Retry logic for transient failures
- [ ] Security error message sanitization
- [ ] Performance monitoring and alerting
