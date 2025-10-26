"""
Batch processing utilities for Rekognition operations.
Optimizes multiple image analyses by batching API calls.
"""

import json
import time
from typing import Dict, Any, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from utils.structured_logger import get_logger
from utils.exceptions import RekognitionError, handle_aws_error
from utils.cache import ConnectionPool, BatchProcessor, PerformanceMonitor

logger = get_logger(__name__)

class RekognitionBatchProcessor:
    """Batch processor for Rekognition operations."""
    
    def __init__(self, max_concurrent: int = 10, batch_size: int = 5):
        """
        Initialize batch processor.
        
        Args:
            max_concurrent: Maximum concurrent operations
            batch_size: Number of images per batch
        """
        self.max_concurrent = max_concurrent
        self.batch_size = batch_size
        self.rekognition = ConnectionPool.get_client('rekognition')
        self.performance_monitor = PerformanceMonitor()
    
    def process_images_batch(self, images: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """
        Process multiple images in batches.
        
        Args:
            images: List of image objects with bucket and key
            
        Returns:
            List of analysis results
        """
        timer_id = self.performance_monitor.start_timer("batch_rekognition")
        
        try:
            # Create batches
            batch_processor = BatchProcessor(self.batch_size)
            batches = batch_processor.create_batches(images)
            
            logger.info(f"Processing {len(images)} images in {len(batches)} batches")
            
            # Process batches concurrently
            all_results = []
            with ThreadPoolExecutor(max_workers=self.max_concurrent) as executor:
                # Submit all batches
                future_to_batch = {
                    executor.submit(self._process_single_batch, batch): batch 
                    for batch in batches
                }
                
                # Collect results as they complete
                for future in as_completed(future_to_batch):
                    batch = future_to_batch[future]
                    try:
                        batch_results = future.result()
                        all_results.extend(batch_results)
                        logger.info(f"Completed batch with {len(batch_results)} results")
                    except Exception as e:
                        logger.error(f"Batch processing failed: {str(e)}")
                        # Add error results for failed batch
                        for image in batch:
                            all_results.append({
                                'error': str(e),
                                'image_key': image.get('key', 'unknown'),
                                'bucket': image.get('bucket', 'unknown')
                            })
            
            duration = self.performance_monitor.end_timer(timer_id)
            logger.info(f"Batch processing completed in {duration:.2f}s")
            
            return all_results
            
        except Exception as e:
            logger.error(f"Batch processing failed: {str(e)}")
            raise RekognitionError(
                f"Batch processing failed: {str(e)}",
                operation="process_images_batch"
            )
    
    def _process_single_batch(self, batch: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """
        Process a single batch of images.
        
        Args:
            batch: List of images in the batch
            
        Returns:
            List of analysis results for the batch
        """
        results = []
        
        for image in batch:
            try:
                result = self._analyze_single_image(image)
                results.append(result)
            except Exception as e:
                logger.error(f"Error processing image {image.get('key', 'unknown')}: {str(e)}")
                results.append({
                    'error': str(e),
                    'image_key': image.get('key', 'unknown'),
                    'bucket': image.get('bucket', 'unknown')
                })
        
        return results
    
    def _analyze_single_image(self, image: Dict[str, str]) -> Dict[str, Any]:
        """
        Analyze a single image with Rekognition.
        
        Args:
            image: Image object with bucket and key
            
        Returns:
            Analysis results
        """
        try:
            # Detect labels with optimized parameters
            response = self.rekognition.detect_labels(
                Image={'S3Object': {'Bucket': image['bucket'], 'Name': image['key']}},
                MaxLabels=50,
                MinConfidence=70,
                Features=['GENERAL_LABELS']
            )
            
            # Filter for accessibility-relevant labels
            accessibility_labels = self._filter_accessibility_labels(response.get('Labels', []))
            
            return {
                'image_key': image['key'],
                'bucket': image['bucket'],
                'labels': accessibility_labels,
                'total_labels': len(response.get('Labels', [])),
                'accessibility_labels': len(accessibility_labels),
                'analysis_timestamp': time.time()
            }
            
        except Exception as e:
            logger.error(f"Rekognition analysis failed for {image.get('key', 'unknown')}: {str(e)}")
            raise handle_aws_error(e, "detect_labels", "rekognition")
    
    def _filter_accessibility_labels(self, labels: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter labels for accessibility relevance.
        
        Args:
            labels: List of detected labels
            
        Returns:
            Filtered accessibility-relevant labels
        """
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
        
        return filtered_labels
    
    def get_batch_statistics(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Get statistics for batch processing results.
        
        Args:
            results: List of batch processing results
            
        Returns:
            Processing statistics
        """
        total_images = len(results)
        successful_analyses = len([r for r in results if 'error' not in r])
        failed_analyses = total_images - successful_analyses
        
        total_labels = sum(r.get('total_labels', 0) for r in results if 'error' not in r)
        accessibility_labels = sum(r.get('accessibility_labels', 0) for r in results if 'error' not in r)
        
        return {
            'total_images': total_images,
            'successful_analyses': successful_analyses,
            'failed_analyses': failed_analyses,
            'success_rate': (successful_analyses / total_images * 100) if total_images > 0 else 0,
            'total_labels_detected': total_labels,
            'accessibility_labels_detected': accessibility_labels,
            'average_labels_per_image': total_labels / successful_analyses if successful_analyses > 0 else 0
        }


class OptimizedRekognitionClient:
    """Optimized Rekognition client with caching and batching."""
    
    def __init__(self, cache_table: Optional[str] = None):
        """
        Initialize optimized Rekognition client.
        
        Args:
            cache_table: DynamoDB table name for caching
        """
        self.batch_processor = RekognitionBatchProcessor()
        self.cache = None
        if cache_table:
            from utils.cache import ImageAnalysisCache
            self.cache = ImageAnalysisCache(cache_table)
    
    def analyze_images_optimized(self, images: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """
        Analyze multiple images with optimizations.
        
        Args:
            images: List of image objects
            
        Returns:
            List of analysis results
        """
        results = []
        cache_hits = 0
        cache_misses = 0
        
        # Check cache for each image
        if self.cache:
            for image in images:
                cached_result = self.cache.get_cached_analysis(image['key'])
                if cached_result:
                    results.append(cached_result)
                    cache_hits += 1
                else:
                    cache_misses += 1
        
        # Process uncached images in batches
        if cache_misses > 0:
            uncached_images = [img for img in images if not any(
                r.get('image_key') == img['key'] for r in results
            )]
            
            batch_results = self.batch_processor.process_images_batch(uncached_images)
            
            # Cache new results
            if self.cache:
                for result in batch_results:
                    if 'error' not in result:
                        self.cache.cache_analysis(
                            result['image_key'], 
                            result
                        )
            
            results.extend(batch_results)
        
        logger.info(f"Cache hits: {cache_hits}, Cache misses: {cache_misses}")
        return results
