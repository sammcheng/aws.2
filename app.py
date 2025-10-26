#!/usr/bin/env python3
"""
Zillow Image Scraper Web Application

A Flask web application that provides a frontend for the Zillow image scraper.
Users can enter Zillow URLs and get back organized image collections.

Author: AI Assistant
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for
import os
import json
from datetime import datetime
from zillow_image_scraper import (
    fetch_page_content, 
    extract_json_from_page, 
    extract_image_urls, 
    extract_images_from_html,
    filter_unique_images,
    download_and_upload_to_s3,
    generate_listing_id
)

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Global variables to store results
processing_results = {}

@app.route('/')
def index():
    """Main page with URL input form."""
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process_url():
    """Process a Zillow URL and extract images."""
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        
        if not url:
            return jsonify({'error': 'URL is required'}), 400
        
        if not url.startswith('https://www.zillow.com/'):
            return jsonify({'error': 'Please provide a valid Zillow listing URL'}), 400
        
        # Generate unique job ID
        job_id = generate_listing_id(url)
        
        # Store initial status
        processing_results[job_id] = {
            'status': 'processing',
            'url': url,
            'started_at': datetime.now().isoformat(),
            'images': [],
            'error': None
        }
        
        # Process the URL
        result = process_zillow_url(url, job_id)
        
        # Update results
        processing_results[job_id].update(result)
        
        return jsonify({
            'job_id': job_id,
            'status': result['status'],
            'message': result.get('message', 'Processing completed'),
            'image_count': len(result.get('images', [])),
            's3_urls': result.get('s3_urls', [])
        })
        
    except Exception as e:
        return jsonify({'error': f'Processing failed: {str(e)}'}), 500

@app.route('/status/<job_id>')
def get_status(job_id):
    """Get the status of a processing job."""
    if job_id not in processing_results:
        return jsonify({'error': 'Job not found'}), 404
    
    result = processing_results[job_id]
    return jsonify({
        'job_id': job_id,
        'status': result['status'],
        'url': result['url'],
        'started_at': result['started_at'],
        'image_count': len(result.get('images', [])),
        's3_urls': result.get('s3_urls', []),
        'error': result.get('error')
    })

@app.route('/results/<job_id>')
def get_results(job_id):
    """Get detailed results for a completed job."""
    if job_id not in processing_results:
        return jsonify({'error': 'Job not found'}), 404
    
    result = processing_results[job_id]
    return jsonify(result)

@app.route('/gallery/<job_id>')
def view_gallery(job_id):
    """View the image gallery for a completed job."""
    if job_id not in processing_results:
        return render_template('error.html', message='Job not found'), 404
    
    result = processing_results[job_id]
    if result['status'] != 'completed':
        return render_template('error.html', message='Job not completed yet'), 400
    
    return render_template('gallery.html', 
                         job_id=job_id, 
                         images=result.get('s3_urls', []),
                         url=result['url'])

def process_zillow_url(url, job_id):
    """
    Process a Zillow URL and extract images.
    
    Args:
        url (str): Zillow listing URL
        job_id (str): Unique job identifier
        
    Returns:
        dict: Processing results
    """
    try:
        # Fetch page content
        html_content = fetch_page_content(url)
        if not html_content:
            return {
                'status': 'error',
                'error': 'Failed to fetch the page. Please check the URL and try again.',
                'images': []
            }
        
        # Extract JSON data
        json_data = extract_json_from_page(html_content)
        
        image_urls = []
        if json_data:
            # Extract image URLs from JSON
            image_urls = extract_image_urls(json_data)
            # Filter JSON results to get unique images only
            image_urls = filter_unique_images(image_urls)
        
        # If no images found in JSON, try extracting from HTML directly
        if not image_urls:
            image_urls = extract_images_from_html(html_content)
        
        if not image_urls:
            return {
                'status': 'completed',
                'message': 'No images found on this listing.',
                'images': [],
                's3_urls': []
            }
        
        # Upload to S3
        s3_result = download_and_upload_to_s3(image_urls, job_id)
        
        return {
            'status': 'completed',
            'message': f'Successfully processed {len(image_urls)} images',
            'images': image_urls,
            's3_urls': s3_result.get('s3_urls', []),
            'upload_success': s3_result.get('success', 0),
            'upload_total': s3_result.get('total', 0)
        }
        
    except Exception as e:
        return {
            'status': 'error',
            'error': f'Processing failed: {str(e)}',
            'images': []
        }

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return render_template('error.html', message='Page not found'), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    return render_template('error.html', message='Internal server error'), 500

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    
    # Run the application
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    app.run(host='0.0.0.0', port=port, debug=debug)
