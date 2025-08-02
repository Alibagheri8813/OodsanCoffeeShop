# 🤖 AI Coffee Assistant

## Overview
A professional AI coffee assistant that provides expert knowledge about coffee, brewing methods, bean varieties, and more. The assistant is available on every page of the coffee shop website with both text and voice capabilities.

## ✨ Features

### 🎯 Core Capabilities
- **Coffee Expert Knowledge**: Comprehensive knowledge about coffee beans, brewing methods, equipment
- **Brewing Guidance**: Step-by-step instructions for various brewing methods
- **Product Recommendations**: Personalized coffee recommendations based on preferences
- **Troubleshooting**: Help with common coffee brewing issues
- **Coffee Culture**: Interesting facts and stories about coffee

### 🎤 Voice Features
- **Text-to-Speech**: AI responses can be converted to voice
- **Speech-to-Text**: Users can speak their questions
- **Voice Chat**: Full voice conversation capability
- **Natural Voice**: High-quality, natural-sounding voice responses

### 🎨 UI/UX Features
- **Floating Widget**: Always accessible on every page
- **Beautiful Design**: Matches the coffee shop theme
- **Quick Actions**: Pre-defined coffee-related questions
- **Responsive**: Works perfectly on mobile and desktop
- **Real-time Chat**: Instant responses with loading animations

## 🛠 Technical Implementation

### Backend (Python/Django)
```python
# AI Assistant Module: shop/ai_assistant.py
- CoffeeAI class: Handles conversation and responses
- VoiceProcessor class: Manages voice input/output
- Professional coffee expert system prompt
- Fallback responses for offline scenarios
```

### Frontend (JavaScript/HTML/CSS)
```javascript
// Features:
- Real-time chat interface
- Voice recording and playback
- Quick action buttons
- Loading animations
- Responsive design
```

### APIs Used
1. **Hugging Face Inference API** (Free)
   - Text generation for AI responses
   - Speech-to-text conversion
   
2. **ElevenLabs API** (Free tier available)
   - High-quality text-to-speech
   - Natural voice synthesis

## 🚀 Setup Instructions

### 1. Get API Keys
```bash
# Hugging Face (Free)
1. Go to https://huggingface.co/settings/tokens
2. Create a new token
3. Copy the token

# ElevenLabs (Free tier available)
1. Go to https://elevenlabs.io/
2. Sign up for free account
3. Get your API key
```

### 2. Configure Environment Variables
```bash
# Create .env file in project root
HUGGINGFACE_API_KEY=your_huggingface_token_here
ELEVENLABS_API_KEY=your_elevenlabs_key_here
```

### 3. Install Dependencies
```bash
pip install requests
```

### 4. Run the Application
```bash
python manage.py runserver
```

## 📱 How to Use

### Text Chat
1. Click the coffee cup icon (bottom-right corner)
2. Type your coffee-related question
3. Press Enter or click send
4. Get expert coffee advice instantly

### Voice Chat
1. Click the coffee cup icon
2. Click the microphone button to enable voice
3. Speak your question
4. Listen to the AI's voice response

### Quick Actions
- **اسپرسو**: Learn about espresso brewing
- **دانه‌ها**: Discover coffee bean varieties
- **دم کردن**: Brewing method guides
- **توصیه**: Personalized recommendations

## 🎯 Professional Coffee Expert System

The AI assistant is trained with a comprehensive coffee expert system that includes:

### Knowledge Areas
- **Coffee Origins**: Geographic regions, climate effects
- **Bean Varieties**: Arabica, Robusta, hybrids
- **Roasting Levels**: Light, medium, dark roast characteristics
- **Brewing Methods**: 15+ different brewing techniques
- **Equipment**: Grinders, machines, accessories
- **Coffee Culture**: History, traditions, modern trends
- **Health Benefits**: Caffeine, antioxidants, effects
- **Business Insights**: Coffee shop management, industry trends

### Communication Style
- **Warm & Welcoming**: Friendly, approachable tone
- **Professional**: Accurate, detailed information
- **Encouraging**: Supports coffee enthusiasts at all levels
- **Educational**: Teaches concepts clearly
- **Practical**: Provides actionable advice

## 🔧 Customization

### Modify the System Prompt
Edit the `system_prompt` in `shop/ai_assistant.py` to customize:
- Knowledge areas
- Communication style
- Response format
- Special features

### Add New Quick Actions
```html
<!-- In shop/templates/shop/ai_assistant.html -->
<button class="ai-quick-btn" onclick="askAI('Your question here')">
    <i class="fas fa-icon"></i>
    Button Text
</button>
```

### Customize Voice Settings
```python
# In shop/ai_assistant.py - VoiceProcessor class
voice_settings = {
    "stability": 0.5,        # Voice stability (0-1)
    "similarity_boost": 0.5  # Voice similarity (0-1)
}
```

## 🎨 UI Customization

### Colors
```css
/* Main theme colors */
--coffee-primary: #4B2E2B;
--coffee-secondary: #7B3F00;
--coffee-accent: #C97C5D;
```

### Styling
- Modify CSS in `shop/templates/shop/ai_assistant.html`
- Adjust widget position, size, colors
- Customize animations and transitions

## 🔒 Security & Privacy

### Data Handling
- No personal data stored
- Conversations are not logged
- API keys are environment variables
- HTTPS required for production

### Voice Privacy
- Audio processing happens server-side
- No audio files stored permanently
- Temporary processing only

## 🚀 Performance Optimization

### Caching
- Conversation history (last 10 messages)
- Fallback responses for offline scenarios
- API response caching

### Error Handling
- Graceful fallback when APIs are unavailable
- User-friendly error messages
- Automatic retry mechanisms

## 📊 Analytics (Optional)

Track usage patterns:
- Most common questions
- Voice vs text usage
- Popular quick actions
- User engagement metrics

## 🎯 Future Enhancements

### Planned Features
- **Multi-language Support**: English, Arabic, Persian
- **Personalized Recommendations**: Based on user history
- **Coffee Quiz**: Interactive learning
- **Recipe Sharing**: User-generated content
- **Integration**: Connect with inventory system

### Advanced AI Features
- **Image Recognition**: Identify coffee beans, equipment
- **Voice Commands**: "Make me an espresso recipe"
- **Smart Recommendations**: Based on weather, time, mood
- **Conversation Memory**: Remember user preferences

## 🤝 Contributing

### Adding New Coffee Knowledge
1. Update the `coffee_responses` dictionary in `CoffeeAI._get_fallback_response()`
2. Add new keywords and responses
3. Test with various user inputs

### Improving Voice Quality
1. Experiment with different ElevenLabs voices
2. Adjust voice settings for better clarity
3. Test with different languages

## 📞 Support

For technical support or feature requests:
- Check the Django logs for errors
- Verify API keys are correctly set
- Test voice permissions in browser
- Ensure HTTPS is enabled for voice features

---

**Made with ☕ and ❤️ for coffee lovers everywhere!** 