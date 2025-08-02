#!/usr/bin/env python
"""
Debug script for the AI Assistant
"""
import os
import sys
import django
import json
import requests

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'coffe_shop.settings')
django.setup()

from shop.ai_assistant import CoffeeAI
from shop.ai_config import OPENAI_API_KEY

def test_ai_config():
    """Test AI configuration"""
    print("🔧 Testing AI Configuration...")
    print("-" * 50)
    
    # Check API key
    print(f"API Key (first 10 chars): {OPENAI_API_KEY[:10]}...")
    print(f"API Key length: {len(OPENAI_API_KEY)}")
    print(f"API Key is placeholder: {'your-openai-api-key-here' in OPENAI_API_KEY}")
    
    if 'your-openai-api-key-here' in OPENAI_API_KEY:
        print("❌ WARNING: You're using a placeholder API key!")
        print("   Please set a real OpenAI API key in shop/ai_config.py")
        return False
    
    print("✅ API Key format looks correct")
    return True

def test_ai_initialization():
    """Test AI assistant initialization"""
    print("\n🤖 Testing AI Assistant Initialization...")
    print("-" * 50)
    
    try:
        ai = CoffeeAI()
        print("✅ AI Assistant initialized successfully")
        return ai
    except Exception as e:
        print(f"❌ AI Assistant initialization failed: {str(e)}")
        return None

def test_ai_response(ai):
    """Test AI response generation"""
    print("\n💬 Testing AI Response Generation...")
    print("-" * 50)
    
    if ai is None:
        print("❌ Cannot test response - AI Assistant not initialized")
        return False
    
    try:
        test_message = "سلام! من می‌خواهم قهوه‌ای بخرم. چه نوع قهوه‌ای پیشنهاد می‌کنید؟"
        print(f"Test message: {test_message}")
        
        response = ai.generate_response(test_message)
        print(f"✅ AI Response: {response[:100]}...")
        return True
        
    except Exception as e:
        print(f"❌ AI Response generation failed: {str(e)}")
        return False

def test_api_endpoint():
    """Test the API endpoint"""
    print("\n🌐 Testing API Endpoint...")
    print("-" * 50)
    
    try:
        # Test the chat endpoint
        url = "http://127.0.0.1:8000/ai/chat/"
        data = {
            "message": "سلام! تست"
        }
        
        response = requests.post(url, json=data, timeout=10)
        print(f"Chat Status Code: {response.status_code}")
        print(f"Chat Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Chat API endpoint is working")
        else:
            print("❌ Chat API endpoint returned error")
            
        # Test the voice endpoint
        voice_url = "http://127.0.0.1:8000/ai/voice/"
        voice_data = {
            "transcribed_text": "سلام! تست صوتی"
        }
        
        voice_response = requests.post(voice_url, json=voice_data, timeout=10)
        print(f"Voice Status Code: {voice_response.status_code}")
        print(f"Voice Response: {voice_response.text}")
        
        if voice_response.status_code == 501:
            print("✅ Voice API endpoint is working (placeholder)")
            return True
        elif voice_response.status_code == 200:
            print("✅ Voice API endpoint is working")
            return True
        else:
            print("❌ Voice API endpoint returned error")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Make sure Django server is running.")
        return False
    except Exception as e:
        print(f"❌ API endpoint test failed: {str(e)}")
        return False

def main():
    """Run all debug tests"""
    print("🔍 AI Assistant Debug Tool")
    print("=" * 50)
    
    # Test configuration
    config_ok = test_ai_config()
    
    # Test initialization
    ai = test_ai_initialization()
    
    # Test response generation
    if ai:
        response_ok = test_ai_response(ai)
    else:
        response_ok = False
    
    # Test API endpoint
    api_ok = test_api_endpoint()
    
    # Summary
    print("\n📊 Debug Summary")
    print("=" * 50)
    print(f"Configuration: {'✅ OK' if config_ok else '❌ FAILED'}")
    print(f"Initialization: {'✅ OK' if ai else '❌ FAILED'}")
    print(f"Response Generation: {'✅ OK' if response_ok else '❌ FAILED'}")
    print(f"API Endpoint: {'✅ OK' if api_ok else '❌ FAILED'}")
    
    if not config_ok:
        print("\n🔧 To fix configuration issues:")
        print("1. Get an OpenAI API key from https://platform.openai.com/")
        print("2. Update shop/ai_config.py with your real API key")
        print("3. Restart the Django server")
    
    if not ai:
        print("\n🔧 To fix initialization issues:")
        print("1. Check your internet connection")
        print("2. Verify your OpenAI API key is valid")
        print("3. Check the console logs for detailed error messages")
    
    if not response_ok:
        print("\n🔧 To fix response generation issues:")
        print("1. Check your OpenAI account balance")
        print("2. Verify your API key has the correct permissions")
        print("3. Check the console logs for detailed error messages")
    
    if not api_ok:
        print("\n🔧 To fix API endpoint issues:")
        print("1. Make sure Django server is running: python manage.py runserver")
        print("2. Check that the server is accessible at http://127.0.0.1:8000/")
        print("3. Check the Django console for error messages")

if __name__ == "__main__":
    main() 