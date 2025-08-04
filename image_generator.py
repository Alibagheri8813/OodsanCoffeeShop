#!/usr/bin/env python3
"""
Image Generator for Persian Coffee Products
Generates images for a list of Persian coffee and beverage product names using OpenAI's DALL-E API
"""

import os
import requests
from openai import OpenAI
import time
from pathlib import Path

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

# Translation mapping for better image generation
translations = {
    "قهوه": "coffee beans in a elegant package",
    "میکس عربیکا": "arabica coffee blend package",
    "میکس 50*50": "50/50 coffee blend package",
    "میکس 100 ربستا": "100% robusta coffee blend package",
    "70*30 پایه ربستا پودری": "70/30 robusta base coffee powder package",
    "میت": "mate tea package",
    "کاپوچینو": "cappuccino coffee package",
    "هات چاکلت": "hot chocolate package",
    "ماسالا": "masala chai tea package",
    "گلد هند": "premium Indian gold coffee package",
    "گلد اکوادور": "premium Ecuadorian gold coffee package", 
    "گلد برزیل": "premium Brazilian gold coffee package",
    "کلاسیک هند": "classic Indian coffee package",
    "اسپرسو فوری هند": "Indian instant espresso package",
    "اسپرسو فوری برزیل": "Brazilian instant espresso package",
    "شکلات میلکو": "milk chocolate package",
    "شکلات دارکو": "dark chocolate package",
    "شکلات 55درصد": "55% cocoa chocolate package",
    "شکلات میلکو ویژه": "premium milk chocolate package",
    "سیروپ ایریش": "Irish syrup bottle",
    "سیروپ کارامل": "caramel syrup bottle",
    "سیروپ نارگیل": "coconut syrup bottle",
    "سیروپ سیب": "apple syrup bottle",
    "سیروپ بلوبری": "blueberry syrup bottle",
    "سیروپ لیمو": "lemon syrup bottle",
    "سیروپ موهیتو": "mojito syrup bottle",
    "سیروپ زعفران": "saffron syrup bottle",
    "سیروپ آناناس": "pineapple syrup bottle"
}

def generate_image(client, product_name, english_description):
    """Generate an image for a given product using DALL-E"""
    try:
        prompt = f"A professional product photography of {english_description}, elegant packaging design, high quality, commercial style, clean background, studio lighting"
        
        print(f"Generating image for: {product_name}")
        print(f"Prompt: {prompt}")
        
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1,
        )
        
        image_url = response.data[0].url
        return image_url
        
    except Exception as e:
        print(f"Error generating image for {product_name}: {str(e)}")
        return None

def download_image(url, filename):
    """Download image from URL and save to file"""
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        with open(filename, 'wb') as f:
            f.write(response.content)
        
        print(f"Image saved as: {filename}")
        return True
        
    except Exception as e:
        print(f"Error downloading image: {str(e)}")
        return False

def main():
    # Check for OpenAI API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("Error: Please set your OPENAI_API_KEY environment variable")
        print("You can get an API key from: https://platform.openai.com/api-keys")
        return
    
    # Initialize OpenAI client
    client = OpenAI(api_key=api_key)
    
    # Create output directory
    output_dir = Path("generated_images")
    output_dir.mkdir(exist_ok=True)
    
    print(f"Starting image generation for {len(product_names)} products...")
    print(f"Images will be saved in: {output_dir.absolute()}")
    
    successful_generations = 0
    failed_generations = 0
    
    for i, product_name in enumerate(product_names, 1):
        print(f"\n--- Processing {i}/{len(product_names)} ---")
        
        # Get English description
        english_description = translations.get(product_name, f"coffee product package with Persian text: {product_name}")
        
        # Generate image
        image_url = generate_image(client, product_name, english_description)
        
        if image_url:
            # Create safe filename
            safe_filename = f"{i:02d}_{product_name.replace('*', 'x').replace('/', '_')}.png"
            filepath = output_dir / safe_filename
            
            # Download image
            if download_image(image_url, filepath):
                successful_generations += 1
            else:
                failed_generations += 1
        else:
            failed_generations += 1
        
        # Add delay to respect rate limits
        if i < len(product_names):
            print("Waiting 3 seconds before next generation...")
            time.sleep(3)
    
    print(f"\n=== Generation Complete ===")
    print(f"Successful: {successful_generations}")
    print(f"Failed: {failed_generations}")
    print(f"Total: {len(product_names)}")
    print(f"Images saved in: {output_dir.absolute()}")

if __name__ == "__main__":
    main()