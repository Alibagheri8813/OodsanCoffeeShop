#!/usr/bin/env python3
"""
Image Searcher for Persian Coffee Products
Searches and downloads images for Persian coffee and beverage products from the web
"""

import os
import requests
from pathlib import Path
import time
import json
from urllib.parse import urlparse, unquote
import re

# List of Persian product names
product_names = [
    "قهوه",
    "میکس عربیکا",
    "میکس 50*50", 
    "میکس 100 ربستا",
    "70*30 پایه ربستا پودری",
    "میت",
    "کاپوچینو",
    "هات چاکلت",
    "ماسالا",
    "گلد هند",
    "گلد اکوادور",
    "گلد برزیل",
    "کلاسیک هند",
    "اسپرسو فوری هند",
    "اسپرسو فوری برزیل",
    "شکلات میلکو",
    "شکلات دارکو",
    "شکلات 55درصد",
    "شکلات میلکو ویژه",
    "سیروپ ایریش",
    "سیروپ کارامل",
    "سیروپ نارگیل",
    "سیروپ سیب",
    "سیروپ بلوبری",
    "سیروپ لیمو",
    "سیروپ موهیتو",
    "سیروپ زعفران",
    "سیروپ آناناس"
]

# English search terms for better results
search_terms = {
    "قهوه": "coffee beans package product",
    "میکس عربیکا": "arabica coffee mix blend package",
    "میکس 50*50": "50 50 coffee blend mix package",
    "میکس 100 ربستا": "100% robusta coffee package",
    "70*30 پایه ربستا پودری": "robusta coffee powder base package",
    "میت": "mate tea yerba package",
    "کاپوچینو": "cappuccino coffee package instant",
    "هات چاکلت": "hot chocolate package mix",
    "ماسالا": "masala chai tea package spice",
    "گلد هند": "premium indian gold coffee package",
    "گلد اکوادور": "premium ecuadorian gold coffee package", 
    "گلد برزیل": "premium brazilian gold coffee package",
    "کلاسیک هند": "classic indian coffee package",
    "اسپرسو فوری هند": "indian instant espresso coffee package",
    "اسپرسو فوری برزیل": "brazilian instant espresso coffee package",
    "شکلات میلکو": "milk chocolate bar package",
    "شکلات دارکو": "dark chocolate bar package",
    "شکلات 55درصد": "55% cocoa dark chocolate package",
    "شکلات میلکو ویژه": "premium milk chocolate package",
    "سیروپ ایریش": "irish cream syrup bottle",
    "سیروپ کارامل": "caramel syrup bottle",
    "سیروپ نارگیل": "coconut syrup bottle",
    "سیروپ سیب": "apple syrup bottle",
    "سیروپ بلوبری": "blueberry syrup bottle",
    "سیروپ لیمو": "lemon syrup bottle",
    "سیروپ موهیتو": "mojito mint syrup bottle",
    "سیروپ زعفران": "saffron syrup bottle",
    "سیروپ آناناس": "pineapple syrup bottle"
}

def search_images_bing(query, api_key, count=5):
    """Search for images using Bing Image Search API"""
    try:
        endpoint = "https://api.bing.microsoft.com/v7.0/images/search"
        headers = {"Ocp-Apim-Subscription-Key": api_key}
        params = {
            "q": query,
            "count": count,
            "imageType": "Photo",
            "size": "Medium",
            "aspect": "Square",
            "color": "ColorOnly"
        }
        
        response = requests.get(endpoint, headers=headers, params=params)
        response.raise_for_status()
        
        data = response.json()
        image_urls = []
        
        for image in data.get("value", []):
            image_urls.append({
                "url": image["contentUrl"],
                "name": image.get("name", ""),
                "width": image.get("width", 0),
                "height": image.get("height", 0)
            })
        
        return image_urls
        
    except Exception as e:
        print(f"Error searching images: {str(e)}")
        return []

def search_images_serpapi(query, api_key, count=5):
    """Search for images using SerpApi Google Images"""
    try:
        url = "https://serpapi.com/search"
        params = {
            "engine": "google_images",
            "q": query,
            "api_key": api_key,
            "num": count,
            "safe": "active",
            "ijn": "0"
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        image_urls = []
        
        for image in data.get("images_results", []):
            image_urls.append({
                "url": image.get("original", image.get("link", "")),
                "name": image.get("title", ""),
                "width": 0,
                "height": 0
            })
        
        return image_urls
        
    except Exception as e:
        print(f"Error searching images with SerpApi: {str(e)}")
        return []

def download_image(url, filepath, timeout=30):
    """Download image from URL"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=timeout, stream=True)
        response.raise_for_status()
        
        # Check if it's actually an image
        content_type = response.headers.get('content-type', '').lower()
        if not any(img_type in content_type for img_type in ['image/', 'jpeg', 'jpg', 'png', 'gif', 'webp']):
            return False
        
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        # Check if file was created and has content
        if filepath.exists() and filepath.stat().st_size > 1000:  # At least 1KB
            return True
        else:
            if filepath.exists():
                filepath.unlink()  # Delete empty/small file
            return False
            
    except Exception as e:
        print(f"Error downloading image: {str(e)}")
        if filepath.exists():
            filepath.unlink()  # Clean up partial download
        return False

def get_file_extension(url):
    """Extract file extension from URL"""
    parsed = urlparse(url)
    path = unquote(parsed.path)
    
    # Common image extensions
    for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
        if ext in path.lower():
            return ext
    
    # Default to jpg
    return '.jpg'

def clean_filename(text):
    """Create a safe filename from Persian text"""
    # Remove or replace problematic characters
    safe_text = re.sub(r'[<>:"/\\|?*]', '_', text)
    safe_text = safe_text.replace('*', 'x')
    return safe_text

def main():
    print("=== Persian Coffee Products Image Searcher ===\n")
    
    # Check for API keys
    bing_key = os.getenv('BING_SEARCH_API_KEY')
    serpapi_key = os.getenv('SERPAPI_KEY')
    
    if not bing_key and not serpapi_key:
        print("Error: Please set either BING_SEARCH_API_KEY or SERPAPI_KEY environment variable")
        print("\nTo get API keys:")
        print("- Bing: https://www.microsoft.com/en-us/bing/apis/bing-image-search-api")
        print("- SerpApi: https://serpapi.com/")
        return
    
    # Choose search method
    if bing_key:
        print("Using Bing Image Search API")
        search_func = lambda q: search_images_bing(q, bing_key, count=3)
    else:
        print("Using SerpApi Google Images")
        search_func = lambda q: search_images_serpapi(q, serpapi_key, count=3)
    
    # Create output directory
    output_dir = Path("searched_images")
    output_dir.mkdir(exist_ok=True)
    
    print(f"Starting image search for {len(product_names)} products...")
    print(f"Images will be saved in: {output_dir.absolute()}\n")
    
    successful_downloads = 0
    failed_downloads = 0
    
    for i, product_name in enumerate(product_names, 1):
        print(f"--- Processing {i}/{len(product_names)}: {product_name} ---")
        
        # Get search term
        search_query = search_terms.get(product_name, f"coffee product {product_name}")
        print(f"Search query: {search_query}")
        
        # Search for images
        image_results = search_func(search_query)
        
        if not image_results:
            print(f"No images found for {product_name}")
            failed_downloads += 1
            continue
        
        # Try to download the first few images
        downloaded = False
        for j, image_info in enumerate(image_results[:3]):  # Try up to 3 images
            try:
                url = image_info["url"]
                extension = get_file_extension(url)
                
                # Create filename
                safe_name = clean_filename(product_name)
                filename = f"{i:02d}_{safe_name}_{j+1}{extension}"
                filepath = output_dir / filename
                
                print(f"Attempting to download: {url}")
                
                if download_image(url, filepath):
                    print(f"✓ Successfully downloaded: {filename}")
                    successful_downloads += 1
                    downloaded = True
                    break
                else:
                    print(f"✗ Failed to download from: {url}")
                    
            except Exception as e:
                print(f"✗ Error processing image {j+1}: {str(e)}")
        
        if not downloaded:
            print(f"✗ No images successfully downloaded for {product_name}")
            failed_downloads += 1
        
        # Rate limiting
        if i < len(product_names):
            print("Waiting 2 seconds before next search...")
            time.sleep(2)
        
        print()
    
    print("=== Search Complete ===")
    print(f"Successful downloads: {successful_downloads}")
    print(f"Failed downloads: {failed_downloads}")
    print(f"Total products: {len(product_names)}")
    print(f"Images saved in: {output_dir.absolute()}")

if __name__ == "__main__":
    main()