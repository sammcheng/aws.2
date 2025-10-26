"""
Caching utilities for the Accessibility Checker API.
Implements DynamoDB-based caching for identical image analyses.
"""

import json
import hashlib
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
import boto3
from botocore.exceptions import ClientError
from utils.structured_logger import get_logger
from utils.exceptions import AccessibilityCheckerError, S3Error

logger = get_logger(__name__)

class ImageAnalysisCache:
    """DynamoDB-based cache for image analysis results."""
    
    def __init__(self, table_name: str, ttl_hours: int = 24):
        """
        Initialize the cache.
        
        Args:
            table_name: DynamoDB table name
            ttl_hours: Time-to-live in hours
        """
        self.table_name = table_name
        self.ttl_hours = ttl_hours
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table(table_name)
    
    def _generate_cache_key(self, image_key: str, analysis_type: str = "accessibility") -> str:
        """
        Generate a unique cache key for the image analysis.
        
        Args:
            image_key: S3 object key
            analysis_type: Type of analysis performed
            
        Returns:
            Unique cache key
        """
        # Create hash of image key and analysis type
        content = f"{image_key}:{analysis_type}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    def _get_ttl_timestamp(self) -> int:
        """Get TTL timestamp for DynamoDB."""
        return int(time.time()) + (self.ttl_hours * 3600)
    
    def get_cached_analysis(self, image_key: str, analysis_type: str = "accessibility") -> Optional[Dict[str, Any]]:
        """
        Get cached analysis results.
        
        Args:
            image_key: S3 object key
            analysis_type: Type of analysis
            
        Returns:
            Cached analysis results or None if not found
        """
        try:
            cache_key = self._generate_cache_key(image_key, analysis_type)
            
            response = self.table.get_item(
                Key={'cache_key': cache_key}
            )
            
            if 'Item' in response:
                item = response['Item']
                
                # Check if item has expired
                if item.get('ttl', 0) < int(time.time()):
                    logger.info(f"Cache item expired for key: {cache_key}")
                    return None
                
                logger.info(f"Cache hit for key: {cache_key}")
                return json.loads(item['analysis_result'])
            else:
                logger.info(f"Cache miss for key: {cache_key}")
                return None
                
        except ClientError as e:
            logger.error(f"Error retrieving from cache: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error retrieving from cache: {str(e)}")
            return None
    
    def cache_analysis(self, image_key: str, analysis_result: Dict[str, Any], analysis_type: str = "accessibility") -> bool:
        """
        Cache analysis results.
        
        Args:
            image_key: S3 object key
            analysis_result: Analysis results to cache
            analysis_type: Type of analysis
            
        Returns:
            True if successful, False otherwise
        """
        try:
            cache_key = self._generate_cache_key(image_key, analysis_type)
            
            item = {
                'cache_key': cache_key,
                'image_key': image_key,
                'analysis_type': analysis_type,
                'analysis_result': json.dumps(analysis_result),
                'created_at': datetime.now(timezone.utc).isoformat(),
                'ttl': self._get_ttl_timestamp()
            }
            
            self.table.put_item(Item=item)
            logger.info(f"Cached analysis for key: {cache_key}")
            return True
            
        except ClientError as e:
            logger.error(f"Error caching analysis: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error caching analysis: {str(e)}")
            return False
    
    def invalidate_cache(self, image_key: str, analysis_type: str = "accessibility") -> bool:
        """
        Invalidate cached analysis.
        
        Args:
            image_key: S3 object key
            analysis_type: Type of analysis
            
        Returns:
            True if successful, False otherwise
        """
        try:
            cache_key = self._generate_cache_key(image_key, analysis_type)
            
            self.table.delete_item(
                Key={'cache_key': cache_key}
            )
            
            logger.info(f"Invalidated cache for key: {cache_key}")
            return True
            
        except ClientError as e:
            logger.error(f"Error invalidating cache: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error invalidating cache: {str(e)}")
            return False
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Cache statistics
        """
        try:
            # Get item count
            response = self.table.scan(
                Select='COUNT'
            )
            
            return {
                'item_count': response['Count'],
                'table_name': self.table_name,
                'ttl_hours': self.ttl_hours
            }
            
        except Exception as e:
            logger.error(f"Error getting cache stats: {str(e)}")
            return {'error': str(e)}


class BatchProcessor:
    """Batch processor for multiple image analyses."""
    
    def __init__(self, max_batch_size: int = 10):
        """
        Initialize batch processor.
        
        Args:
            max_batch_size: Maximum number of images per batch
        """
        self.max_batch_size = max_batch_size
    
    def create_batches(self, images: List[Dict[str, str]]) -> List[List[Dict[str, str]]]:
        """
        Create batches from image list.
        
        Args:
            images: List of image objects
            
        Returns:
            List of image batches
        """
        batches = []
        for i in range(0, len(images), self.max_batch_size):
            batch = images[i:i + self.max_batch_size]
            batches.append(batch)
        
        logger.info(f"Created {len(batches)} batches from {len(images)} images")
        return batches
    
    def process_batch(self, batch: List[Dict[str, str]], processor_func) -> List[Dict[str, Any]]:
        """
        Process a batch of images.
        
        Args:
            batch: List of images in the batch
            processor_func: Function to process each image
            
        Returns:
            List of results
        """
        results = []
        
        for image in batch:
            try:
                result = processor_func(image)
                results.append(result)
            except Exception as e:
                logger.error(f"Error processing image {image.get('key', 'unknown')}: {str(e)}")
                results.append({
                    'error': str(e),
                    'image_key': image.get('key', 'unknown')
                })
        
        return results


class ConnectionPool:
    """Connection pool for boto3 clients."""
    
    _clients = {}
    _lock = None
    
    @classmethod
    def get_client(cls, service_name: str, **kwargs):
        """
        Get a boto3 client from the connection pool.
        
        Args:
            service_name: AWS service name
            **kwargs: Additional client configuration
            
        Returns:
            Boto3 client
        """
        # Create a key for the client configuration
        config_key = f"{service_name}:{hash(frozenset(kwargs.items()))}"
        
        if config_key not in cls._clients:
            cls._clients[config_key] = boto3.client(service_name, **kwargs)
            logger.info(f"Created new client for {service_name}")
        
        return cls._clients[config_key]
    
    @classmethod
    def get_resource(cls, service_name: str, **kwargs):
        """
        Get a boto3 resource from the connection pool.
        
        Args:
            service_name: AWS service name
            **kwargs: Additional resource configuration
            
        Returns:
            Boto3 resource
        """
        # Create a key for the resource configuration
        config_key = f"resource:{service_name}:{hash(frozenset(kwargs.items()))}"
        
        if config_key not in cls._clients:
            cls._clients[config_key] = boto3.resource(service_name, **kwargs)
            logger.info(f"Created new resource for {service_name}")
        
        return cls._clients[config_key]
    
    @classmethod
    def clear_pool(cls):
        """Clear the connection pool."""
        cls._clients.clear()
        logger.info("Connection pool cleared")


class PerformanceMonitor:
    """Performance monitoring utilities."""
    
    def __init__(self):
        self.metrics = {}
    
    def start_timer(self, operation: str) -> str:
        """
        Start timing an operation.
        
        Args:
            operation: Operation name
            
        Returns:
            Timer ID
        """
        timer_id = f"{operation}_{int(time.time() * 1000)}"
        self.metrics[timer_id] = {
            'operation': operation,
            'start_time': time.time()
        }
        return timer_id
    
    def end_timer(self, timer_id: str) -> float:
        """
        End timing an operation.
        
        Args:
            timer_id: Timer ID from start_timer
            
        Returns:
            Duration in seconds
        """
        if timer_id in self.metrics:
            duration = time.time() - self.metrics[timer_id]['start_time']
            self.metrics[timer_id]['duration'] = duration
            logger.info(f"Operation {self.metrics[timer_id]['operation']} took {duration:.2f}s")
            return duration
        return 0.0
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics."""
        return self.metrics.copy()
