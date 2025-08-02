# AI Assistant Setup Guide

## Overview
The coffee shop now uses OpenAI's GPT-3.5-turbo model for intelligent coffee recommendations and assistance.

## Setup Instructions

### 1. Get OpenAI API Key
1. Go to [OpenAI Platform](https://platform.openai.com/)
2. Sign up or log in to your account
3. Navigate to "API Keys" section
4. Create a new API key
5. Copy the API key (starts with `sk-`)

### 2. Configure the API Key
1. Open `shop/ai_config.py`
2. Replace `"sk-proj-your-openai-api-key-here"` with your actual API key
3. Save the file

### 3. Test the AI Assistant
Run the test script to verify everything is working:
```bash
python test_ai_assistant.py
```

### 4. Features
- **Text Chat**: Users can ask coffee-related questions in Persian
- **Coffee Expertise**: Specialized knowledge about coffee varieties, brewing methods, and recommendations

### 5. API Endpoints
- `POST /ai/chat/` - Text-based chat

### 6. Usage Example
```javascript
// Text chat
fetch('/ai/chat/', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify({
        message: 'سلام! چه نوع قهوه‌ای پیشنهاد می‌کنید؟'
    })
})
.then(response => response.json())
.then(data => console.log(data.response));
```

## Troubleshooting

### Common Issues:
1. **API Key Error**: Make sure you've set a valid OpenAI API key
2. **Network Error**: Check your internet connection
3. **Import Error**: Run `pip install openai` to install the required package

### Cost Considerations:
- OpenAI charges per API call
- Monitor your usage in the OpenAI dashboard
- Consider setting usage limits to control costs

## Security Notes
- Never commit API keys to version control
- Consider using environment variables for production
- Regularly rotate your API keys 