#!/usr/bin/env python
"""
Test script for the AI Assistant
"""
import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'coffe_shop.settings')
django.setup()

from shop.ai_assistant import CoffeeAI

def test_ai_assistant():
    """Test the AI assistant with a simple coffee question"""
    try:
        # Initialize the AI assistant
        ai = CoffeeAI()
        
        # Test message
        test_message = "سلام! من می‌خواهم قهوه‌ای بخرم. چه نوع قهوه‌ای پیشنهاد می‌کنید؟"
        
        print("Testing AI Assistant...")
        print(f"User message: {test_message}")
        print("-" * 50)
        
        # Generate response
        response = ai.generate_response(test_message)
        
        print(f"AI Response: {response}")
        print("-" * 50)
        print("✅ AI Assistant test completed successfully!")
        
    except Exception as e:
        print(f"❌ AI Assistant test failed: {str(e)}")
        print("\nMake sure you have:")
        print("1. Set a valid OpenAI API key in shop/ai_config.py")
        print("2. Installed the openai package: pip install openai")
        print("3. Have internet connection for API calls")

if __name__ == "__main__":
    test_ai_assistant() 