#!/usr/bin/env python3
"""
Image Generator for Persian Coffee Products - Stability AI Version
Generates images using Stability AI's API (more cost-effective alternative)
"""

import os
import requests
import json
import time
from pathlib import Path
import base64

# List of Persian product names (same as OpenAI version)
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
    "قهوه": "coffee beans in elegant packaging",
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

def generate_image_stability(api_key, product_name, english_description):
    """Generate an image using Stability AI's API"""
    try:
        url = "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image"
        
        prompt = f"Professional product photography of {english_description}, elegant commercial packaging design, high quality, studio lighting, clean white background, commercial style"
        
        print(f"Generating image for: {product_name}")
        print(f"Prompt: {prompt}")
        
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }
        
        payload = {
            "text_prompts": [
                {
                    "text": prompt,
                    "weight": 1
                }
            ],
            "cfg_scale": 7,
            "height": 1024,
            "width": 1024,
            "samples": 1,
            "steps": 30,
        }
        
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            data = response.json()
            return data["artifacts"][0]["base64"]
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"Error generating image for {product_name}: {str(e)}")
        return None

def save_base64_image(base64_string, filename):
    """Save base64 encoded image to file"""
    try:
        image_data = base64.b64decode(base64_string)
        
        with open(filename, 'wb') as f:
            f.write(image_data)
        
        print(f"Image saved as: {filename}")
        return True
        
    except Exception as e:
        print(f"Error saving image: {str(e)}")
        return False

def main():
    # Check for Stability AI API key
    api_key = os.getenv('STABILITY_API_KEY')
    if not api_key:
        print("Error: Please set your STABILITY_API_KEY environment variable")
        print("You can get an API key from: https://platform.stability.ai/account/keys")
        return
    
    # Create output directory
    output_dir = Path("generated_images_stability")
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
        base64_image = generate_image_stability(api_key, product_name, english_description)
        
        if base64_image:
            # Create safe filename
            safe_filename = f"{i:02d}_{product_name.replace('*', 'x').replace('/', '_')}.png"
            filepath = output_dir / safe_filename
            
            # Save image
            if save_base64_image(base64_image, filepath):
                successful_generations += 1
            else:
                failed_generations += 1
        else:
            failed_generations += 1
        
        # Add delay to respect rate limits
        if i < len(product_names):
            print("Waiting 2 seconds before next generation...")
            time.sleep(2)
    
    print(f"\n=== Generation Complete ===")
    print(f"Successful: {successful_generations}")
    print(f"Failed: {failed_generations}")
    print(f"Total: {len(product_names)}")
    print(f"Images saved in: {output_dir.absolute()}")

if __name__ == "__main__":
    main()