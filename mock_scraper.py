#!/usr/bin/env python3
"""
Mock Zillow Image Scraper for Testing

Returns sample images when Zillow blocks the real scraper.
"""

import json
import sys
import argparse
from datetime import datetime

def main():
    parser = argparse.ArgumentParser(description="Mock Zillow scraper for testing")
    parser.add_argument('url', help='Zillow property listing URL')
    parser.add_argument('--download', action='store_true', help='Download images')
    parser.add_argument('--s3', action='store_true', help='Upload to S3')
    parser.add_argument('--max-images', type=int, default=20, help='Maximum number of images')
    
    args = parser.parse_args()
    
    print("Mock Zillow Image Scraper")
    print("=" * 50)
    print(f"Fetching page: {args.url}")
    print("Extracting property details...")
    print("Extracting property images from page...")
    
    # Generate mock images
    mock_images = []
    for i in range(1, min(args.max_images + 1, 11)):  # Generate up to 10 mock images
        mock_images.append(f"https://photos.zillowstatic.com/fp/mock_image_{i:02d}-cc_ft_1536.webp")
    
    print(f"\nFound {len(mock_images)} image(s):")
    print("-" * 50)
    for i, url in enumerate(mock_images, 1):
        print(f" {i}. {url}")
    
    # Mock property details
    property_details = {
        'address': '1014 Teal Dr',
        'city': 'Santa Clara',
        'state': 'CA',
        'zipCode': '95051',
        'propertyType': 'Single Family Residence',
        'bedrooms': '3',
        'bathrooms': '2',
        'squareFeet': '1,200',
        'yearBuilt': '1985',
        'lotSize': '6,000 sqft',
        'price': '$1,200,000'
    }
    
    print(f"\nProperty Details:")
    print(f"Address: {property_details['address']}")
    print(f"City: {property_details['city']}")
    print(f"State: {property_details['state']}")
    print(f"ZIP: {property_details['zipCode']}")
    print(f"Type: {property_details['propertyType']}")
    print(f"Bedrooms: {property_details['bedrooms']}")
    print(f"Bathrooms: {property_details['bathrooms']}")
    print(f"Square Feet: {property_details['squareFeet']}")
    print(f"Year Built: {property_details['yearBuilt']}")
    print(f"Lot Size: {property_details['lotSize']}")
    print(f"Price: {property_details['price']}")
    
    # Return JSON result
    result = {
        'images': mock_images,
        'propertyDetails': property_details,
        'timestamp': datetime.now().isoformat()
    }
    
    print(json.dumps(result))
    return 0

if __name__ == "__main__":
    sys.exit(main())

