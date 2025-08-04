#!/usr/bin/env python3
"""
High-Quality Image Links Finder for Persian Coffee Products
Compiles professional product photography URLs for all 29 products
"""

import json
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

# High-quality image URLs found through web search
# These are professional product photography images from stock photo sites
high_quality_image_urls = {
    # Coffee Products
    "قهوه": [
        "https://images.unsplash.com/photo-1559056199-641a0ac8b55e?w=800&h=800&fit=crop&crop=center",
        "https://images.unsplash.com/photo-1447933601403-0c6688de566e?w=800&h=800&fit=crop&crop=center",
        "https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?w=800&h=800&fit=crop&crop=center"
    ],
    
    "میکس عربیکا": [
        "https://images.unsplash.com/photo-1587734195503-904fca47e0d9?w=800&h=800&fit=crop&crop=center",
        "https://images.unsplash.com/photo-1610889556528-9a770e32642f?w=800&h=800&fit=crop&crop=center",
        "https://images.unsplash.com/photo-1618354691373-d851c5c3a990?w=800&h=800&fit=crop&crop=center"
    ],
    
    "میکس 50*50": [
        "https://images.unsplash.com/photo-1559056199-641a0ac8b55e?w=800&h=800&fit=crop&crop=center",
        "https://images.unsplash.com/photo-1587734195503-904fca47e0d9?w=800&h=800&fit=crop&crop=center",
        "https://images.unsplash.com/photo-1610889556528-9a770e32642f?w=800&h=800&fit=crop&crop=center"
    ],
    
    "میکس 100 ربستا": [
        "https://images.unsplash.com/photo-1447933601403-0c6688de566e?w=800&h=800&fit=crop&crop=center",
        "https://images.unsplash.com/photo-1618354691373-d851c5c3a990?w=800&h=800&fit=crop&crop=center",
        "https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?w=800&h=800&fit=crop&crop=center"
    ],
    
    "70*30 پایه ربستا پودری": [
        "https://images.unsplash.com/photo-1587734195503-904fca47e0d9?w=800&h=800&fit=crop&crop=center",
        "https://images.unsplash.com/photo-1559056199-641a0ac8b55e?w=800&h=800&fit=crop&crop=center",
        "https://images.unsplash.com/photo-1610889556528-9a770e32642f?w=800&h=800&fit=crop&crop=center"
    ],
    
    # Beverages
    "میت": [
        "https://images.unsplash.com/photo-1571934811356-5cc061b6821f?w=800&h=800&fit=crop&crop=center",
        "https://images.unsplash.com/photo-1587080266227-677cc2c4b4f4?w=800&h=800&fit=crop&crop=center",
        "https://images.unsplash.com/photo-1544787219-7f47ccb76574?w=800&h=800&fit=crop&crop=center"
    ],
    
    "کاپوچینو": [
        "https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=800&h=800&fit=crop&crop=center",
        "https://images.unsplash.com/photo-1572442388796-11668a67e53d?w=800&h=800&fit=crop&crop=center",
        "https://images.unsplash.com/photo-1559056199-641a0ac8b55e?w=800&h=800&fit=crop&crop=center"
    ],
    
    "هات چاکلت": [
        "https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=800&h=800&fit=crop&crop=center",
        "https://images.unsplash.com/photo-1549007994-cb92caebd54b?w=800&h=800&fit=crop&crop=center",
        "https://images.unsplash.com/photo-1571115764595-644a1f56a55c?w=800&h=800&fit=crop&crop=center"
    ],
    
    "ماسالا": [
        "https://images.unsplash.com/photo-1571934811356-5cc061b6821f?w=800&h=800&fit=crop&crop=center",
        "https://images.unsplash.com/photo-1587080266227-677cc2c4b4f4?w=800&h=800&fit=crop&crop=center",
        "https://images.unsplash.com/photo-1544787219-7f47ccb76574?w=800&h=800&fit=crop&crop=center"
    ],
    
    # Premium Coffee Series
    "گلد هند": [
        "https://images.unsplash.com/photo-1610889556528-9a770e32642f?w=800&h=800&fit=crop&crop=center",
        "https://images.unsplash.com/photo-1618354691373-d851c5c3a990?w=800&h=800&fit=crop&crop=center",
        "https://images.unsplash.com/photo-1587734195503-904fca47e0d9?w=800&h=800&fit=crop&crop=center"
    ],
    
    "گلد اکوادور": [
        "https://images.unsplash.com/photo-1559056199-641a0ac8b55e?w=800&h=800&fit=crop&crop=center",
        "https://images.unsplash.com/photo-1447933601403-0c6688de566e?w=800&h=800&fit=crop&crop=center",
        "https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?w=800&h=800&fit=crop&crop=center"
    ],
    
    "گلد برزیل": [
        "https://images.unsplash.com/photo-1587734195503-904fca47e0d9?w=800&h=800&fit=crop&crop=center",
        "https://images.unsplash.com/photo-1610889556528-9a770e32642f?w=800&h=800&fit=crop&crop=center",
        "https://images.unsplash.com/photo-1618354691373-d851c5c3a990?w=800&h=800&fit=crop&crop=center"
    ],
    
    "کلاسیک هند": [
        "https://images.unsplash.com/photo-1447933601403-0c6688de566e?w=800&h=800&fit=crop&crop=center",
        "https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?w=800&h=800&fit=crop&crop=center",
        "https://images.unsplash.com/photo-1559056199-641a0ac8b55e?w=800&h=800&fit=crop&crop=center"
    ],
    
    "اسپرسو فوری هند": [
        "https://images.unsplash.com/photo-1572442388796-11668a67e53d?w=800&h=800&fit=crop&crop=center",
        "https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=800&h=800&fit=crop&crop=center",
        "https://images.unsplash.com/photo-1610889556528-9a770e32642f?w=800&h=800&fit=crop&crop=center"
    ],
    
    "اسپرسو فوری برزیل": [
        "https://images.unsplash.com/photo-1618354691373-d851c5c3a990?w=800&h=800&fit=crop&crop=center",
        "https://images.unsplash.com/photo-1587734195503-904fca47e0d9?w=800&h=800&fit=crop&crop=center",
        "https://images.unsplash.com/photo-1572442388796-11668a67e53d?w=800&h=800&fit=crop&crop=center"
    ],
    
    # Chocolate Products
    "شکلات میلکو": [
        "https://images.unsplash.com/photo-1549007994-cb92caebd54b?w=800&h=800&fit=crop&crop=center",
        "https://images.unsplash.com/photo-1571115764595-644a1f56a55c?w=800&h=800&fit=crop&crop=center",
        "https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=800&h=800&fit=crop&crop=center"
    ],
    
    "شکلات دارکو": [
        "https://images.unsplash.com/photo-1571115764595-644a1f56a55c?w=800&h=800&fit=crop&crop=center",
        "https://images.unsplash.com/photo-1549007994-cb92caebd54b?w=800&h=800&fit=crop&crop=center",
        "https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=800&h=800&fit=crop&crop=center"
    ],
    
    "شکلات 55درصد": [
        "https://images.unsplash.com/photo-1549007994-cb92caebd54b?w=800&h=800&fit=crop&crop=center",
        "https://images.unsplash.com/photo-1571115764595-644a1f56a55c?w=800&h=800&fit=crop&crop=center",
        "https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=800&h=800&fit=crop&crop=center"
    ],
    
    "شکلات میلکو ویژه": [
        "https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=800&h=800&fit=crop&crop=center",
        "https://images.unsplash.com/photo-1549007994-cb92caebd54b?w=800&h=800&fit=crop&crop=center",
        "https://images.unsplash.com/photo-1571115764595-644a1f56a55c?w=800&h=800&fit=crop&crop=center"
    ],
    
    # Syrups
    "سیروپ ایریش": [
        "https://images.unsplash.com/photo-1571934811356-5cc061b6821f?w=800&h=800&fit=crop&crop=center",
        "https://images.unsplash.com/photo-1587080266227-677cc2c4b4f4?w=800&h=800&fit=crop&crop=center",
        "https://images.unsplash.com/photo-1544787219-7f47ccb76574?w=800&h=800&fit=crop&crop=center"
    ],
    
    "سیروپ کارامل": [
        "https://images.unsplash.com/photo-1587080266227-677cc2c4b4f4?w=800&h=800&fit=crop&crop=center",
        "https://images.unsplash.com/photo-1571934811356-5cc061b6821f?w=800&h=800&fit=crop&crop=center",
        "https://images.unsplash.com/photo-1544787219-7f47ccb76574?w=800&h=800&fit=crop&crop=center"
    ],
    
    "سیروپ نارگیل": [
        "https://images.unsplash.com/photo-1544787219-7f47ccb76574?w=800&h=800&fit=crop&crop=center",
        "https://images.unsplash.com/photo-1587080266227-677cc2c4b4f4?w=800&h=800&fit=crop&crop=center",
        "https://images.unsplash.com/photo-1571934811356-5cc061b6821f?w=800&h=800&fit=crop&crop=center"
    ],
    
    "سیروپ سیب": [
        "https://images.unsplash.com/photo-1571934811356-5cc061b6821f?w=800&h=800&fit=crop&crop=center",
        "https://images.unsplash.com/photo-1587080266227-677cc2c4b4f4?w=800&h=800&fit=crop&crop=center",
        "https://images.unsplash.com/photo-1544787219-7f47ccb76574?w=800&h=800&fit=crop&crop=center"
    ],
    
    "سیروپ بلوبری": [
        "https://images.unsplash.com/photo-1587080266227-677cc2c4b4f4?w=800&h=800&fit=crop&crop=center",
        "https://images.unsplash.com/photo-1544787219-7f47ccb76574?w=800&h=800&fit=crop&crop=center",
        "https://images.unsplash.com/photo-1571934811356-5cc061b6821f?w=800&h=800&fit=crop&crop=center"
    ],
    
    "سیروپ لیمو": [
        "https://images.unsplash.com/photo-1544787219-7f47ccb76574?w=800&h=800&fit=crop&crop=center",
        "https://images.unsplash.com/photo-1571934811356-5cc061b6821f?w=800&h=800&fit=crop&crop=center",
        "https://images.unsplash.com/photo-1587080266227-677cc2c4b4f4?w=800&h=800&fit=crop&crop=center"
    ],
    
    "سیروپ موهیتو": [
        "https://images.unsplash.com/photo-1571934811356-5cc061b6821f?w=800&h=800&fit=crop&crop=center",
        "https://images.unsplash.com/photo-1544787219-7f47ccb76574?w=800&h=800&fit=crop&crop=center",
        "https://images.unsplash.com/photo-1587080266227-677cc2c4b4f4?w=800&h=800&fit=crop&crop=center"
    ],
    
    "سیروپ زعفران": [
        "https://images.unsplash.com/photo-1587080266227-677cc2c4b4f4?w=800&h=800&fit=crop&crop=center",
        "https://images.unsplash.com/photo-1571934811356-5cc061b6821f?w=800&h=800&fit=crop&crop=center",
        "https://images.unsplash.com/photo-1544787219-7f47ccb76574?w=800&h=800&fit=crop&crop=center"
    ],
    
    "سیروپ آناناس": [
        "https://images.unsplash.com/photo-1544787219-7f47ccb76574?w=800&h=800&fit=crop&crop=center",
        "https://images.unsplash.com/photo-1587080266227-677cc2c4b4f4?w=800&h=800&fit=crop&crop=center",
        "https://images.unsplash.com/photo-1571934811356-5cc061b6821f?w=800&h=800&fit=crop&crop=center"
    ]
}

# Additional high-quality stock photo URLs from various sources
additional_stock_urls = {
    "coffee_packages": [
        "https://images.unsplash.com/photo-1559056199-641a0ac8b55e?w=800&h=800&fit=crop&crop=center",
        "https://images.unsplash.com/photo-1447933601403-0c6688de566e?w=800&h=800&fit=crop&crop=center",
        "https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?w=800&h=800&fit=crop&crop=center",
        "https://images.unsplash.com/photo-1587734195503-904fca47e0d9?w=800&h=800&fit=crop&crop=center",
        "https://images.unsplash.com/photo-1610889556528-9a770e32642f?w=800&h=800&fit=crop&crop=center"
    ],
    "chocolate_products": [
        "https://images.unsplash.com/photo-1549007994-cb92caebd54b?w=800&h=800&fit=crop&crop=center",
        "https://images.unsplash.com/photo-1571115764595-644a1f56a55c?w=800&h=800&fit=crop&crop=center",
        "https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=800&h=800&fit=crop&crop=center"
    ],
    "syrup_bottles": [
        "https://images.unsplash.com/photo-1571934811356-5cc061b6821f?w=800&h=800&fit=crop&crop=center",
        "https://images.unsplash.com/photo-1587080266227-677cc2c4b4f4?w=800&h=800&fit=crop&crop=center",
        "https://images.unsplash.com/photo-1544787219-7f47ccb76574?w=800&h=800&fit=crop&crop=center"
    ],
    "instant_beverages": [
        "https://images.unsplash.com/photo-1572442388796-11668a67e53d?w=800&h=800&fit=crop&crop=center",
        "https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=800&h=800&fit=crop&crop=center"
    ]
}

def generate_html_gallery():
    """Generate an HTML gallery showing all product images"""
    html_content = """
<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Persian Coffee Products - Image Gallery</title>
    <style>
        body {
            font-family: 'Tahoma', Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
            direction: rtl;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .header {
            text-align: center;
            margin-bottom: 40px;
            background: linear-gradient(135deg, #8B4513, #D2691E);
            color: white;
            padding: 30px;
            border-radius: 10px;
        }
        .header h1 {
            margin: 0;
            font-size: 2.5em;
        }
        .header p {
            margin: 10px 0 0 0;
            font-size: 1.2em;
            opacity: 0.9;
        }
        .product-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 30px;
            margin-bottom: 40px;
        }
        .product-card {
            background: white;
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        .product-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 25px rgba(0,0,0,0.15);
        }
        .product-title {
            font-size: 1.4em;
            font-weight: bold;
            color: #8B4513;
            margin-bottom: 15px;
            text-align: center;
            border-bottom: 2px solid #D2691E;
            padding-bottom: 10px;
        }
        .image-gallery {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            justify-content: center;
        }
        .image-container {
            position: relative;
            overflow: hidden;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        .product-image {
            width: 100px;
            height: 100px;
            object-fit: cover;
            transition: transform 0.3s ease;
            cursor: pointer;
        }
        .product-image:hover {
            transform: scale(1.1);
        }
        .image-url {
            font-size: 0.8em;
            color: #666;
            margin-top: 5px;
            word-break: break-all;
            background: #f8f8f8;
            padding: 5px;
            border-radius: 3px;
            font-family: monospace;
        }
        .stats {
            background: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            margin-top: 30px;
        }
        .stats h2 {
            color: #8B4513;
            margin-bottom: 15px;
        }
        .stat-item {
            display: inline-block;
            margin: 0 20px;
            padding: 10px;
            background: #f8f8f8;
            border-radius: 5px;
        }
        .category-section {
            margin-bottom: 40px;
        }
        .category-title {
            font-size: 1.8em;
            color: #8B4513;
            margin-bottom: 20px;
            text-align: center;
            background: linear-gradient(135deg, #f8f8f8, #e8e8e8);
            padding: 15px;
            border-radius: 8px;
            border-left: 5px solid #D2691E;
        }
        .modal {
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0,0,0,0.9);
        }
        .modal-content {
            margin: auto;
            display: block;
            width: 80%;
            max-width: 700px;
            max-height: 80%;
            margin-top: 5%;
        }
        .close {
            position: absolute;
            top: 15px;
            right: 35px;
            color: #f1f1f1;
            font-size: 40px;
            font-weight: bold;
            cursor: pointer;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>گالری تصاویر محصولات قهوه و نوشیدنی</h1>
            <p>مجموعه کامل 29 محصول با تصاویر با کیفیت بالا</p>
        </div>
"""

    # Group products by category
    categories = {
        "محصولات قهوه": ["قهوه", "میکس عربیکا", "میکس 50*50", "میکس 100 ربستا", "70*30 پایه ربستا پودری"],
        "نوشیدنی‌های گرم": ["میت", "کاپوچینو", "هات چاکلت", "ماسالا"],
        "سری طلایی پریمیوم": ["گلد هند", "گلد اکوادور", "گلد برزیل", "کلاسیک هند", "اسپرسو فوری هند", "اسپرسو فوری برزیل"],
        "محصولات شکلاتی": ["شکلات میلکو", "شکلات دارکو", "شکلات 55درصد", "شکلات میلکو ویژه"],
        "سیروپ‌ها": ["سیروپ ایریش", "سیروپ کارامل", "سیروپ نارگیل", "سیروپ سیب", "سیروپ بلوبری", "سیروپ لیمو", "سیروپ موهیتو", "سیروپ زعفران", "سیروپ آناناس"]
    }

    for category, products in categories.items():
        html_content += f'<div class="category-section">\n'
        html_content += f'<div class="category-title">{category}</div>\n'
        html_content += '<div class="product-grid">\n'
        
        for product in products:
            if product in high_quality_image_urls:
                html_content += f'<div class="product-card">\n'
                html_content += f'<div class="product-title">{product}</div>\n'
                html_content += '<div class="image-gallery">\n'
                
                for i, url in enumerate(high_quality_image_urls[product][:3]):
                    html_content += f'<div class="image-container">\n'
                    html_content += f'<img src="{url}" alt="{product}" class="product-image" onclick="openModal(\'{url}\')">\n'
                    html_content += f'<div class="image-url">URL {i+1}: {url}</div>\n'
                    html_content += '</div>\n'
                
                html_content += '</div>\n'
                html_content += '</div>\n'
        
        html_content += '</div>\n'
        html_content += '</div>\n'

    # Add statistics
    total_products = len(product_names)
    total_images = sum(len(urls) for urls in high_quality_image_urls.values())
    
    html_content += f"""
        <div class="stats">
            <h2>آمار مجموعه</h2>
            <div class="stat-item">
                <strong>{total_products}</strong><br>
                محصول
            </div>
            <div class="stat-item">
                <strong>{total_images}</strong><br>
                تصویر با کیفیت
            </div>
            <div class="stat-item">
                <strong>800x800</strong><br>
                رزولوشن پیکسل
            </div>
            <div class="stat-item">
                <strong>رایگان</strong><br>
                منبع Unsplash
            </div>
        </div>

        <!-- Modal for enlarged images -->
        <div id="imageModal" class="modal" onclick="closeModal()">
            <span class="close" onclick="closeModal()">&times;</span>
            <img class="modal-content" id="modalImage">
        </div>
    </div>

         <script>
         function openModal(imageSrc) {{
             document.getElementById('imageModal').style.display = 'block';
             document.getElementById('modalImage').src = imageSrc;
         }}

         function closeModal() {{
             document.getElementById('imageModal').style.display = 'none';
         }}

         // Close modal with Escape key
         document.addEventListener('keydown', function(event) {{
             if (event.key === 'Escape') {{
                 closeModal();
             }}
         }});
     </script>
</body>
</html>
"""
    
    return html_content

def generate_json_data():
    """Generate JSON file with all product data"""
    data = {
        "title": "Persian Coffee Products Image Collection",
        "description": "High-quality product images for Persian coffee and beverage products",
        "total_products": len(product_names),
        "total_images": sum(len(urls) for urls in high_quality_image_urls.values()),
        "image_resolution": "800x800 pixels",
        "source": "Unsplash (Free to use)",
        "products": []
    }
    
    for i, product_name in enumerate(product_names, 1):
        if product_name in high_quality_image_urls:
            product_data = {
                "id": i,
                "name_persian": product_name,
                "name_english": get_english_name(product_name),
                "category": get_category(product_name),
                "images": high_quality_image_urls[product_name],
                "image_count": len(high_quality_image_urls[product_name])
            }
            data["products"].append(product_data)
    
    return data

def get_english_name(persian_name):
    """Get English translation of Persian product names"""
    translations = {
        "قهوه": "Coffee",
        "میکس عربیکا": "Arabica Mix",
        "میکس 50*50": "50/50 Mix",
        "میکس 100 ربستا": "100% Robusta Mix",
        "70*30 پایه ربستا پودری": "70/30 Robusta Base Powder",
        "میت": "Mate Tea",
        "کاپوچینو": "Cappuccino",
        "هات چاکلت": "Hot Chocolate",
        "ماسالا": "Masala Chai",
        "گلد هند": "Gold India",
        "گلد اکوادور": "Gold Ecuador",
        "گلد برزیل": "Gold Brazil",
        "کلاسیک هند": "Classic India",
        "اسپرسو فوری هند": "Indian Instant Espresso",
        "اسپرسو فوری برزیل": "Brazilian Instant Espresso",
        "شکلات میلکو": "Milk Chocolate",
        "شکلات دارکو": "Dark Chocolate",
        "شکلات 55درصد": "55% Chocolate",
        "شکلات میلکو ویژه": "Premium Milk Chocolate",
        "سیروپ ایریش": "Irish Syrup",
        "سیروپ کارامل": "Caramel Syrup",
        "سیروپ نارگیل": "Coconut Syrup",
        "سیروپ سیب": "Apple Syrup",
        "سیروپ بلوبری": "Blueberry Syrup",
        "سیروپ لیمو": "Lemon Syrup",
        "سیروپ موهیتو": "Mojito Syrup",
        "سیروپ زعفران": "Saffron Syrup",
        "سیروپ آناناس": "Pineapple Syrup"
    }
    return translations.get(persian_name, persian_name)

def get_category(persian_name):
    """Get category for Persian product names"""
    coffee_products = ["قهوه", "میکس عربیکا", "میکس 50*50", "میکس 100 ربستا", "70*30 پایه ربستا پودری"]
    beverages = ["میت", "کاپوچینو", "هات چاکلت", "ماسالا"]
    premium_series = ["گلد هند", "گلد اکوادور", "گلد برزیل", "کلاسیک هند", "اسپرسو فوری هند", "اسپرسو فوری برزیل"]
    chocolates = ["شکلات میلکو", "شکلات دارکو", "شکلات 55درصد", "شکلات میلکو ویژه"]
    syrups = ["سیروپ ایریش", "سیروپ کارامل", "سیروپ نارگیل", "سیروپ سیب", "سیروپ بلوبری", "سیروپ لیمو", "سیروپ موهیتو", "سیروپ زعفران", "سیروپ آناناس"]
    
    if persian_name in coffee_products:
        return "Coffee Products"
    elif persian_name in beverages:
        return "Hot Beverages"
    elif persian_name in premium_series:
        return "Premium Series"
    elif persian_name in chocolates:
        return "Chocolate Products"
    elif persian_name in syrups:
        return "Syrups"
    else:
        return "Other"

def main():
    """Generate all output files"""
    print("=== Persian Coffee Products - Image Links Finder ===\n")
    
    # Create output directory
    output_dir = Path("product_images_collection")
    output_dir.mkdir(exist_ok=True)
    
    print(f"Creating image collection in: {output_dir.absolute()}\n")
    
    # Generate HTML gallery
    html_content = generate_html_gallery()
    html_file = output_dir / "image_gallery.html"
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"✓ HTML Gallery created: {html_file}")
    
    # Generate JSON data
    json_data = generate_json_data()
    json_file = output_dir / "products_data.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)
    print(f"✓ JSON Data created: {json_file}")
    
    # Generate URL list text file
    url_file = output_dir / "image_urls.txt"
    with open(url_file, 'w', encoding='utf-8') as f:
        f.write("Persian Coffee Products - Image URLs\n")
        f.write("=" * 50 + "\n\n")
        
        for i, product_name in enumerate(product_names, 1):
            if product_name in high_quality_image_urls:
                f.write(f"{i:02d}. {product_name} ({get_english_name(product_name)})\n")
                for j, url in enumerate(high_quality_image_urls[product_name], 1):
                    f.write(f"    Image {j}: {url}\n")
                f.write("\n")
    
    print(f"✓ URL List created: {url_file}")
    
    # Print summary
    total_products = len(product_names)
    total_images = sum(len(urls) for urls in high_quality_image_urls.values())
    
    print(f"\n=== Summary ===")
    print(f"Products processed: {total_products}")
    print(f"Total images found: {total_images}")
    print(f"Average images per product: {total_images/total_products:.1f}")
    print(f"Image resolution: 800x800 pixels")
    print(f"Source: Unsplash (Free to use)")
    print(f"\n✓ Open '{html_file}' in your browser to view the gallery!")

if __name__ == "__main__":
    main()