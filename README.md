# Persian Coffee Products Image Tools

This repository contains tools for both generating and searching for images of Persian coffee and beverage products.

## Available Tools

### 1. Image Generation Scripts
- **`image_generator.py`** - Uses OpenAI DALL-E 3 API
- **`image_generator_stability.py`** - Uses Stability AI API (more cost-effective)

### 2. Image Search Scripts  
- **`image_searcher.py`** - Professional image search using Bing or SerpApi
- **`simple_image_searcher.py`** - Simple demo version (uses placeholders)

## Features

**Image Generation:**
- Generates high-quality product images for 29 Persian coffee and beverage items
- Professional product photography style with clean backgrounds
- Automatic translation of Persian product names to English descriptions

**Image Search:**
- Searches web for existing product images
- Downloads and organizes images with Persian filenames
- Supports multiple search engines (Bing, Google via SerpApi)
- Free demo version available

**Common Features:**
- Rate limiting to respect API constraints
- Progress tracking and error handling
- Images saved with organized filenames

## Product List

The script generates images for these Persian products:

**Coffee Products:**
- قهوه (Coffee)
- میکس عربیکا (Arabica Mix)
- میکس 50*50 (50/50 Mix)
- میکس 100 ربستا (100% Robusta Mix)
- 70*30 پایه ربستا پودری (70/30 Robusta Base Powder)

**Beverages:**
- میت (Mate)
- کاپوچینو (Cappuccino)
- هات چاکلت (Hot Chocolate)
- ماسالا (Masala)

**Premium Coffee Series:**
- گلد هند (Gold India)
- گلد اکوادور (Gold Ecuador)
- گلد برزیل (Gold Brazil)
- کلاسیک هند (Classic India)
- اسپرسو فوری هند (Indian Instant Espresso)
- اسپرسو فوری برزیل (Brazilian Instant Espresso)

**Chocolate Products:**
- شکلات میلکو (Milk Chocolate)
- شکلات دارکو (Dark Chocolate)
- شکلات 55درصد (55% Chocolate)
- شکلات میلکو ویژه (Premium Milk Chocolate)

**Syrups:**
- سیروپ ایریش (Irish Syrup)
- سیروپ کارامل (Caramel Syrup)
- سیروپ نارگیل (Coconut Syrup)
- سیروپ سیب (Apple Syrup)
- سیروپ بلوبری (Blueberry Syrup)
- سیروپ لیمو (Lemon Syrup)
- سیروپ موهیتو (Mojito Syrup)
- سیروپ زعفران (Saffron Syrup)
- سیروپ آناناس (Pineapple Syrup)

## Setup

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Get OpenAI API Key:**
   - Visit https://platform.openai.com/api-keys
   - Create a new API key
   - Copy the key for the next step

3. **Set your OpenAI API key:**
   ```bash
   export OPENAI_API_KEY="your-api-key-here"
   ```
   
   Or on Windows:
   ```cmd
   set OPENAI_API_KEY=your-api-key-here
   ```

## Usage

### Image Generation

**OpenAI DALL-E 3:**
```bash
export OPENAI_API_KEY="your-openai-key"
python image_generator.py
```

**Stability AI (cheaper):**
```bash
export STABILITY_API_KEY="your-stability-key"
python image_generator_stability.py
```

### Image Search

**Professional Search (requires API key):**
```bash
# Using Bing Image Search
export BING_SEARCH_API_KEY="your-bing-key"
python image_searcher.py

# OR using SerpApi (Google Images)
export SERPAPI_KEY="your-serpapi-key"
python image_searcher.py
```

**Simple Demo (no API key needed):**
```bash
python simple_image_searcher.py
```

### What the scripts do:
1. Create output directories (`generated_images/`, `searched_images/`, etc.)
2. Process all 29 products automatically
3. Save images with Persian names in filenames
4. Show progress and success/failure statistics

## Output

- **Directory:** `generated_images/`
- **Format:** PNG files (1024x1024 pixels)
- **Naming:** `{number}_{persian_name}.png`
- **Style:** Professional product photography with clean backgrounds

## Cost Estimation

Using DALL-E 3 standard quality (1024x1024):
- Cost per image: ~$0.040
- Total for 29 images: ~$1.16

## Rate Limiting

The script includes a 3-second delay between generations to respect OpenAI's rate limits and avoid errors.

## Error Handling

- Missing API key detection
- Network error handling
- Image download verification
- Progress tracking with success/failure counts

## Customization

You can modify the script to:
- Change image size (512x512, 1024x1024, 1792x1024)
- Adjust image quality (standard/hd)
- Modify prompts for different styles
- Add or remove products from the list
- Change output directory or filename format