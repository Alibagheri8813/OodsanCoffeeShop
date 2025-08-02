# AI Assistant Setup Guide

This guide will help you set up the AI assistant for the coffee shop website. The assistant uses ElevenLabs API for both Speech-to-Text (STT) and Text-to-Speech (TTS) functionality.

## Prerequisites

- Python 3.8 or higher
- Django 4.0 or higher
- Internet connection for API calls

## Step 1: Get ElevenLabs API Key

1. Go to [ElevenLabs](https://elevenlabs.io/)
2. Create a free account
3. Navigate to your profile settings
4. Copy your API key
5. The free tier includes:
   - 10,000 characters per month for TTS
   - Speech-to-Text functionality
   - Multiple voice options

## Step 2: Configure Environment Variables

1. Create a `.env` file in your project root (same level as `manage.py`)
2. Add your API key:

```env
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
```

**Important**: Replace `your_elevenlabs_api_key_here` with your actual API key.

## Step 3: Install Dependencies

Make sure you have the required packages installed:

```bash
pip install python-dotenv requests
```

## Step 4: Test the Setup

1. Start your Django development server:
   ```bash
   python manage.py runserver
   ```

2. Navigate to your website (e.g., http://127.0.0.1:8000)

3. Look for the microphone icon in the bottom-right corner

4. Click on the microphone icon to open the AI assistant

5. Click the "صحبت کنید" (Speak) button and allow microphone access

6. Speak in Persian and test the voice functionality

## Step 5: Troubleshooting

### Common Issues:

1. **"Cannot load PSReadline module"** - This is a PowerShell warning and can be ignored
2. **Microphone access denied** - Make sure to allow microphone access in your browser
3. **API key errors** - Verify your ElevenLabs API key is correct
4. **Voice not working** - Check browser console for errors

### Browser Compatibility:

- Chrome (recommended)
- Firefox
- Safari
- Edge

### Mobile Support:

The AI assistant works on mobile devices but may have limited functionality depending on the browser.

## Step 6: Customization

### Changing Voice Settings:

Edit `shop/ai_assistant.py` to modify:
- Voice ID (default: "21m00Tcm4TlvDq8ikWAM")
- Voice stability and similarity settings
- Response patterns

### Adding New Responses:

In the `CoffeeAI` class, add new keywords and responses to the `coffee_responses` dictionary.

## Step 7: Production Deployment

For production:

1. Use environment variables for API keys
2. Implement rate limiting
3. Add error handling
4. Consider using a paid ElevenLabs plan for higher limits
5. Implement caching for common responses

## Features

- **Voice Input**: Speak in Persian to ask questions
- **Voice Output**: AI responses are spoken back to you
- **Text Display**: All conversations are displayed as text
- **Quick Actions**: Pre-defined buttons for common questions
- **Coffee Expert**: Specialized knowledge about coffee, brewing methods, and shop information

## API Usage

The assistant uses:
- **ElevenLabs STT**: Converts your Persian speech to text
- **ElevenLabs TTS**: Converts AI responses to speech
- **Custom Logic**: Provides coffee-specific responses in Persian

## Support

If you encounter issues:
1. Check the browser console for errors
2. Verify your API key is correct
3. Ensure microphone permissions are granted
4. Test with different browsers

The AI assistant is designed to be a helpful coffee expert that can answer questions about coffee, brewing methods, shop information, and more - all in Persian! 