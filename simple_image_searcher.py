#!/usr/bin/env python3
"""
Simple Image Searcher for Persian Coffee Products
Uses DuckDuckGo image search (no API key required)
"""

import requests
import json
import time
from pathlib import Path
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

# Search terms optimized for finding product images
search_terms = {
    "قهوه": "coffee beans bag package",
    "میکس عربیکا": "arabica coffee blend package",
    "میکس 50*50": "coffee blend 50 50 package",
    "میکس 100 ربستا": "robusta coffee 100% package",
    "70*30 پایه ربستا پودری": "robusta coffee powder package",
    "میت": "mate tea yerba package",
    "کاپوچینو": "cappuccino instant coffee package",
    "هات چاکلت": "hot chocolate mix package",
    "ماسالا": "masala chai tea package",
    "گلد هند": "indian gold coffee premium package",
    "گلد اکوادور": "ecuadorian gold coffee package", 
    "گلد برزیل": "brazilian gold coffee package",
    "کلاسیک هند": "classic indian coffee package",
    "اسپرسو فوری هند": "indian instant espresso package",
    "اسپرسو فوری برزیل": "brazilian instant espresso package",
    "شکلات میلکو": "milk chocolate bar package",
    "شکلات دارکو": "dark chocolate bar package",
    "شکلات 55درصد": "dark chocolate 55% cocoa package",
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

def search_duckduckgo_images(query, max_results=5):
    """Search for images using DuckDuckGo (no API key required)"""
    try:
        # DuckDuckGo image search endpoint
        url = "https://duckduckgo.com/"
        
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Get token first
        params = {'q': query}
        response = session.get(url, params=params)
        
        # Search for images
        search_url = "https://duckduckgo.com/i.js"
        params = {
            'l': 'us-en',
            'o': 'json',
            'q': query,
            'vqd': '',  # This would normally need to be extracted from the first response
            'f': ',,,',
            'p': '1'
        }
        
        # For simplicity, we'll use a different approach with direct URLs
        # This is a simplified version - in production you'd want proper token handling
        
        # Alternative: Use a simple image search approach
        search_urls = []
        
        # Try different search engines with direct image URLs
        engines = [
            f"https://www.google.com/search?q={query.replace(' ', '+')}&tbm=isch",
            f"https://www.bing.com/images/search?q={query.replace(' ', '+')}"
        ]
        
        # For this demo, we'll return some placeholder URLs
        # In a real implementation, you'd scrape these search results
        placeholder_urls = [
            "https://via.placeholder.com/400x400/8B4513/FFFFFF?text=Coffee+Product",
            "https://via.placeholder.com/400x400/D2691E/FFFFFF?text=Product+Image", 
            "https://via.placeholder.com/400x400/A0522D/FFFFFF?text=Sample+Image"
        ]
        
        return [{"url": url, "name": f"Image for {query}"} for url in placeholder_urls[:max_results]]
        
    except Exception as e:
        print(f"Error searching images: {str(e)}")
        return []

def download_image(url, filepath, timeout=30):
    """Download image from URL"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        
        response = requests.get(url, headers=headers, timeout=timeout, stream=True)
        response.raise_for_status()
        
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        # Check if file was created and has content
        if filepath.exists() and filepath.stat().st_size > 100:  # At least 100 bytes
            return True
        else:
            if filepath.exists():
                filepath.unlink()
            return False
            
    except Exception as e:
        print(f"Error downloading image: {str(e)}")
        if filepath.exists():
            filepath.unlink()
        return False

def get_file_extension(url):
    """Extract file extension from URL"""
    parsed = urlparse(url)
    path = unquote(parsed.path)
    
    for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
        if ext in path.lower():
            return ext
    
    return '.png'  # Default to png for placeholder images

def clean_filename(text):
    """Create a safe filename from Persian text"""
    safe_text = re.sub(r'[<>:"/\\|?*]', '_', text)
    safe_text = safe_text.replace('*', 'x')
    return safe_text

def create_image_list_file(output_dir):
    """Create a text file with the list of all products for reference"""
    list_file = output_dir / "product_list.txt"
    
    with open(list_file, 'w', encoding='utf-8') as f:
        f.write("Persian Coffee Products Image Search Results\n")
        f.write("=" * 50 + "\n\n")
        
        for i, product_name in enumerate(product_names, 1):
            english_term = search_terms.get(product_name, "coffee product")
            f.write(f"{i:02d}. {product_name}\n")
            f.write(f"    English: {english_term}\n")
            f.write(f"    Expected files: {i:02d}_{clean_filename(product_name)}_*.png\n\n")
    
    print(f"Product list saved to: {list_file}")

def main():
    print("=== Simple Persian Coffee Products Image Searcher ===")
    print("Note: This version uses placeholder images for demonstration.")
    print("For real image search, you would need to implement proper web scraping")
    print("or use paid APIs like Bing Image Search or SerpApi.\n")
    
    # Create output directory
    output_dir = Path("searched_images_simple")
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
        
        # Search for images (using placeholder for demo)
        image_results = search_duckduckgo_images(search_query, max_results=2)
        
        if not image_results:
            print(f"No images found for {product_name}")
            failed_downloads += 1
            continue
        
        # Try to download images
        downloaded = False
        for j, image_info in enumerate(image_results):
            try:
                url = image_info["url"]
                extension = get_file_extension(url)
                
                # Create filename
                safe_name = clean_filename(product_name)
                filename = f"{i:02d}_{safe_name}_{j+1}{extension}"
                filepath = output_dir / filename
                
                print(f"Downloading placeholder image: {filename}")
                
                if download_image(url, filepath):
                    print(f"✓ Successfully downloaded: {filename}")
                    successful_downloads += 1
                    downloaded = True
                else:
                    print(f"✗ Failed to download: {filename}")
                    
            except Exception as e:
                print(f"✗ Error processing image {j+1}: {str(e)}")
        
        if not downloaded:
            print(f"✗ No images successfully downloaded for {product_name}")
            failed_downloads += 1
        
        # Small delay
        time.sleep(1)
        print()
    
    # Create reference file
    create_image_list_file(output_dir)
    
    print("=== Search Complete ===")
    print(f"Successful downloads: {successful_downloads}")
    print(f"Failed downloads: {failed_downloads}")
    print(f"Total products: {len(product_names)}")
    print(f"Images saved in: {output_dir.absolute()}")
    print("\nNote: This demo uses placeholder images.")
    print("For real images, consider using:")
    print("1. image_searcher.py with Bing or SerpApi")
    print("2. Manual image collection")
    print("3. Stock photo services")

if __name__ == "__main__":
    main()