import os
import json
import requests
import logging
import traceback
import speech_recognition as sr
import threading
import queue
import time
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from openai import OpenAI
from .ai_config import OPENAI_API_KEY, AI_MODEL, AI_MAX_TOKENS, AI_TEMPERATURE, AI_TOP_P, FALLBACK_RESPONSES

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CoffeeExpertAI:
    """Advanced AI Assistant specialized in coffee industry with voice capabilities"""
    
    def __init__(self):
        # Initialize OpenAI client
        try:
            self.client = OpenAI(api_key=OPENAI_API_KEY)
            self.client.models.list()
            self.is_available = True
            logger.info("AI Assistant initialized successfully")
        except Exception as e:
            logger.error(f"AI Assistant initialization failed: {str(e)}")
            self.is_available = False
            self.client = None
        
        # Initialize speech recognition
        try:
            self.recognizer = sr.Recognizer()
            self.microphone = sr.Microphone()
            self.stt_available = True
            logger.info("Speech recognition initialized successfully")
        except Exception as e:
            logger.error(f"Speech recognition initialization failed: {str(e)}")
            self.stt_available = False
            self.recognizer = None
            self.microphone = None
        
        # Initialize text-to-speech (optional)
        self.tts_available = False
        self.tts_engine = None
        try:
            import pyttsx3
            self.tts_engine = pyttsx3.init()
            self.tts_engine.setProperty('rate', 150)
            self.tts_engine.setProperty('volume', 0.9)
            # Set Persian voice if available
            voices = self.tts_engine.getProperty('voices')
            for voice in voices:
                if 'persian' in voice.name.lower() or 'farsi' in voice.name.lower():
                    self.tts_engine.setProperty('voice', voice.id)
                    break
            self.tts_available = True
            logger.info("TTS initialized successfully")
        except Exception as e:
            logger.warning(f"TTS initialization failed (will use text-only mode): {str(e)}")
            self.tts_available = False
            self.tts_engine = None
        
        # Comprehensive coffee expert system prompt
        self.system_prompt = """
        You are "کافه‌مستر" (Cafe Master), a world-renowned coffee expert and barista with 25+ years of experience. You are the ultimate authority on everything coffee-related.

        **EXPERTISE DOMAINS:**

        🌍 **COFFEE ORIGINS & BEANS:**
        - Ethiopian Yirgacheffe: Floral, citrus notes, light to medium roast
        - Colombian Supremo: Balanced, nutty, medium roast
        - Brazilian Santos: Low acidity, chocolate notes, dark roast
        - Guatemalan Antigua: Spicy, smoky, medium-dark roast
        - Costa Rican Tarrazu: Bright acidity, honey notes, light roast
        - Kenyan AA: Wine-like acidity, berry notes, medium roast
        - Indonesian Sumatra: Earthy, full-bodied, dark roast
        - Jamaican Blue Mountain: Mild, balanced, expensive luxury coffee

        ☕ **BREWING METHODS & TECHNIQUES:**
        - Espresso: 9 bars pressure, 25-30 seconds, 18-21g dose
        - Pour-over: V60, Chemex, Kalita Wave techniques
        - French Press: Coarse grind, 4-5 minutes, full immersion
        - Aeropress: 1-2 minutes, inverted method, paper filter
        - Cold Brew: 12-24 hours, coarse grind, room temperature
        - Turkish Coffee: Fine grind, cezve, foam (köpük)
        - Moka Pot: Stovetop espresso, 3-chamber design
        - Siphon: Vacuum brewing, theatrical presentation

        🔥 **ROASTING LEVELS & PROFILES:**
        - Light Roast: 350-400°F, acidic, original bean flavors
        - Medium Roast: 400-430°F, balanced, caramel notes
        - Medium-Dark: 430-450°F, rich, chocolate notes
        - Dark Roast: 450-480°F, bold, smoky, less caffeine
        - French Roast: 480°F+, very dark, oily surface

        🛠️ **EQUIPMENT & MAINTENANCE:**
        - Espresso Machines: Semi-auto, super-auto, manual
        - Grinders: Burr vs blade, conical vs flat burrs
        - Scales: Precision to 0.1g, timing functions
        - Thermometers: Digital, analog, infrared
        - Filters: Paper, metal, cloth, reusable
        - Cleaning: Backflushing, descaling, daily maintenance

        🏆 **BARISTA TECHNIQUES:**
        - Latte Art: Heart, rosetta, tulip, swan patterns
        - Milk Steaming: Microfoam, temperature control
        - Tamping: 30lbs pressure, level surface
        - Grinding: Burr adjustment, particle size
        - Extraction: Time, pressure, temperature monitoring

        📊 **COFFEE BUSINESS & INDUSTRY:**
        - Coffee Shop Management: Operations, staffing, inventory
        - Market Trends: Specialty coffee, sustainability, fair trade
        - Pricing Strategies: Cost analysis, profit margins
        - Customer Service: Training, standards, experience
        - Quality Control: Cupping, scoring, consistency

        🏥 **HEALTH & SCIENCE:**
        - Caffeine Content: 95mg per 8oz cup average
        - Health Benefits: Antioxidants, mental alertness, metabolism
        - Side Effects: Jitters, insomnia, dependency
        - Decaf Process: Swiss Water, CO2, chemical methods
        - Allergies: Cross-reactivity, alternatives

        🎨 **COFFEE CULTURE & HISTORY:**
        - Coffee Discovery: Ethiopian legend, goat herder story
        - Global Spread: Yemen, Turkey, Europe, Americas
        - Cultural Significance: Social gatherings, ceremonies
        - Modern Trends: Third wave, specialty coffee movement
        - Coffee Houses: Historical meeting places, intellectual hubs

        **COMMUNICATION STYLE:**
        - Warm, passionate, and enthusiastic about coffee
        - Professional yet approachable and friendly
        - Use Persian (Farsi) with coffee terminology
        - Provide detailed, accurate, and practical information
        - Always offer actionable advice and recommendations
        - Be encouraging and supportive of coffee enthusiasts
        - Share interesting facts and stories about coffee

        **RESPONSE FORMAT:**
        - Start with warm greeting if new conversation
        - Provide comprehensive, well-structured answers in Persian
        - Include practical tips and step-by-step instructions
        - Ask follow-up questions to understand user needs better
        - Offer specific product recommendations when relevant
        - End with encouraging words or additional tips

        **SPECIAL CAPABILITIES:**
        - Recommend coffee products based on preferences
        - Suggest brewing methods for different occasions
        - Help troubleshoot coffee brewing issues
        - Share coffee facts, history, and culture
        - Provide seasonal coffee recommendations
        - Guide users through coffee tasting and cupping
        - Explain coffee terminology and concepts
        - Offer business advice for coffee shops

        Remember: You are not just an AI - you are a passionate coffee expert dedicated to sharing knowledge and helping people discover the wonderful world of coffee! Always respond in Persian with warmth and expertise.
        """
        
        self.conversation_history = []
        self.voice_queue = queue.Queue()
        
        # Start voice processing thread only if TTS is available
        if self.tts_available:
            self.voice_thread = threading.Thread(target=self._process_voice_queue, daemon=True)
            self.voice_thread.start()
    
    def get_fallback_response(self, intent=None):
        """Get appropriate fallback response based on user intent"""
        if intent and intent in FALLBACK_RESPONSES:
            return FALLBACK_RESPONSES[intent]
        return FALLBACK_RESPONSES['error']
    
    def detect_intent(self, message):
        """Detect user intent from message"""
        message_lower = message.lower()
        
        # Coffee-specific intents
        if any(word in message_lower for word in ['قهوه', 'کافه', 'اسپرسو']):
            return 'coffee_general'
        elif any(word in message_lower for word in ['روست', 'برشته', 'کباب']):
            return 'roasting'
        elif any(word in message_lower for word in ['دم', 'آماده', 'تهیه']):
            return 'brewing'
        elif any(word in message_lower for word in ['دستگاه', 'ماشین', 'تجهیزات']):
            return 'equipment'
        elif any(word in message_lower for word in ['قیمت', 'هزینه', 'خرید']):
            return 'pricing'
        elif any(word in message_lower for word in ['ساعت', 'زمان', 'باز']):
            return 'hours'
        elif any(word in message_lower for word in ['تحویل', 'ارسال', 'پیک']):
            return 'delivery'
        elif any(word in message_lower for word in ['سلام', 'خوش', 'هی']):
            return 'greeting'
        
        return None
    
    def generate_response(self, user_message, user_id=None):
        """Generate AI response using OpenAI API with enhanced error handling"""
        try:
            # Validate input
            if not user_message or not user_message.strip():
                raise Exception("پیام کاربر خالی است")
            
            # Check if AI is available
            if not self.is_available or not self.client:
                intent = self.detect_intent(user_message)
                return self.get_fallback_response(intent)
            
            # Add user message to conversation history
            self.conversation_history.append({"role": "user", "content": user_message})
            
            # Prepare messages for OpenAI API
            messages = [
                {"role": "system", "content": self.system_prompt}
            ]
            
            # Add conversation history (keep last 10 messages for context)
            for msg in self.conversation_history[-10:]:
                messages.append({"role": msg["role"], "content": msg["content"]})
            
            # Make API request to OpenAI with enhanced parameters
            response = self.client.chat.completions.create(
                model=AI_MODEL,
                messages=messages,
                max_tokens=AI_MAX_TOKENS,
                temperature=AI_TEMPERATURE,
                top_p=AI_TOP_P,
                presence_penalty=0.1,
                frequency_penalty=0.1
            )
            
            # Extract the AI response
            ai_response = response.choices[0].message.content.strip()
            
            # Validate AI response
            if not ai_response:
                raise Exception("دستیار هوشمند پاسخ خالی برگرداند")
            
            # Add AI response to conversation history
            self.conversation_history.append({"role": "assistant", "content": ai_response})
            
            return ai_response
                
        except Exception as e:
            logger.error(f"AI response generation failed: {str(e)}")
            # Provide fallback response based on detected intent
            intent = self.detect_intent(user_message)
            return self.get_fallback_response(intent)
    
    def speech_to_text(self, audio_data):
        """Convert speech to text using speech recognition"""
        if not self.stt_available:
            return "تشخیص صدا در دسترس نیست"
        
        try:
            # Use Google Speech Recognition (free)
            text = self.recognizer.recognize_google(audio_data, language='fa-IR')
            return text
        except sr.UnknownValueError:
            return "متأسفانه نتوانستم صدای شما را تشخیص دهم"
        except sr.RequestError as e:
            logger.error(f"Speech recognition error: {str(e)}")
            return "خطا در تشخیص صدا"
        except Exception as e:
            logger.error(f"STT error: {str(e)}")
            return "خطا در پردازش صدا"
    
    def text_to_speech(self, text):
        """Convert text to speech using pyttsx3"""
        if not self.tts_available or not self.tts_engine:
            logger.warning("TTS not available")
            return False
        
        try:
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()
            return True
        except Exception as e:
            logger.error(f"TTS error: {str(e)}")
            return False
    
    def _process_voice_queue(self):
        """Process voice queue in background thread"""
        while True:
            try:
                if not self.voice_queue.empty():
                    text = self.voice_queue.get()
                    self.text_to_speech(text)
                time.sleep(0.1)
            except Exception as e:
                logger.error(f"Voice queue processing error: {str(e)}")
                time.sleep(1)  # Wait longer on error
    
    def speak_response(self, text):
        """Add text to voice queue for TTS"""
        if self.tts_available and self.voice_queue:
            try:
                self.voice_queue.put(text)
            except Exception as e:
                logger.error(f"Error adding text to voice queue: {str(e)}")

# Initialize AI Assistant with error handling
try:
    coffee_ai = CoffeeExpertAI()
except Exception as e:
    logger.error(f"Failed to initialize Coffee Expert AI: {str(e)}")
    coffee_ai = None

@csrf_exempt
@require_http_methods(["POST"])
def ai_chat(request):
    """Handle text-based chat with AI assistant"""
    try:
        if coffee_ai is None:
            return JsonResponse({
                'error': 'دستیار هوشمند در دسترس نیست. لطفاً بعداً تلاش کنید.',
                'debug_info': 'AI Assistant not initialized',
                'fallback': True
            }, status=503)
        
        # Parse request body
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError as e:
            return JsonResponse({
                'error': 'داده‌های ارسالی نامعتبر است',
                'debug_info': f'JSON decode error: {str(e)}'
            }, status=400)
        
        user_message = data.get('message', '')
        
        if not user_message:
            return JsonResponse({
                'error': 'پیام خالی است',
                'debug_info': 'Empty message received'
            }, status=400)
        
        # Generate AI response
        ai_response = coffee_ai.generate_response(user_message)
        
        return JsonResponse({
            'response': ai_response,
            'success': True,
            'debug_info': 'Response generated successfully',
            'ai_available': coffee_ai.is_available if coffee_ai else False
        })
        
    except Exception as e:
        logger.error(f"AI chat error: {str(e)}")
        return JsonResponse({
            'error': str(e),
            'debug_info': f'Exception: {str(e)}, Type: {type(e).__name__}',
            'fallback': True
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def voice_chat(request):
    """Enhanced voice chat functionality with speech recognition and TTS"""
    try:
        # Parse request body
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError as e:
            return JsonResponse({
                'error': 'داده‌های صوتی نامعتبر است',
                'debug_info': f'JSON decode error: {str(e)}'
            }, status=400)
        
        transcribed_text = data.get('transcribed_text', '')
        
        if not transcribed_text:
            return JsonResponse({
                'error': 'متن ترجمه شده خالی است',
                'debug_info': 'Empty transcribed text'
            }, status=400)
        
        # Generate AI response
        if coffee_ai:
            ai_response = coffee_ai.generate_response(transcribed_text)
            # Add to voice queue for TTS (only if available)
            if coffee_ai.tts_available:
                coffee_ai.speak_response(ai_response)
        else:
            intent = coffee_ai.detect_intent(transcribed_text) if coffee_ai else None
            ai_response = coffee_ai.get_fallback_response(intent) if coffee_ai else FALLBACK_RESPONSES['error']
        
        return JsonResponse({
            'response': ai_response,
            'success': True,
            'transcribed_text': transcribed_text,
            'debug_info': 'Voice response generated successfully',
            'tts_available': coffee_ai.tts_available if coffee_ai else False,
            'stt_available': coffee_ai.stt_available if coffee_ai else False
        })
        
    except Exception as e:
        logger.error(f"Voice chat error: {str(e)}")
        return JsonResponse({
            'error': 'خطا در پردازش صدا. لطفاً دوباره تلاش کنید.',
            'debug_info': f'Voice exception: {str(e)}'
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def speech_to_text(request):
    """Handle speech-to-text conversion"""
    try:
        if coffee_ai is None:
            return JsonResponse({
                'error': 'دستیار صوتی در دسترس نیست',
                'debug_info': 'AI Assistant not initialized'
            }, status=503)
        
        if not coffee_ai.stt_available:
            return JsonResponse({
                'error': 'تشخیص صدا در دسترس نیست',
                'debug_info': 'Speech recognition not available'
            }, status=503)
        
        # Get audio data from request
        audio_file = request.FILES.get('audio')
        if not audio_file:
            return JsonResponse({
                'error': 'فایل صوتی ارسال نشده',
                'debug_info': 'No audio file provided'
            }, status=400)
        
        # Convert audio to speech recognition format
        try:
            with sr.AudioFile(audio_file) as source:
                audio_data = coffee_ai.recognizer.record(source)
                text = coffee_ai.speech_to_text(audio_data)
        except Exception as e:
            logger.error(f"Audio processing error: {str(e)}")
            return JsonResponse({
                'error': 'خطا در پردازش فایل صوتی',
                'debug_info': f'Audio processing error: {str(e)}'
            }, status=500)
        
        return JsonResponse({
            'text': text,
            'success': True,
            'debug_info': 'Speech to text conversion successful'
        })
        
    except Exception as e:
        logger.error(f"Speech to text error: {str(e)}")
        return JsonResponse({
            'error': 'خطا در تبدیل صدا به متن',
            'debug_info': f'STT exception: {str(e)}'
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def text_to_speech(request):
    """Handle text-to-speech conversion"""
    try:
        if coffee_ai is None or not coffee_ai.tts_available:
            return JsonResponse({
                'error': 'سرویس تبدیل متن به صدا در دسترس نیست',
                'debug_info': 'TTS not available'
            }, status=503)
        
        # Parse request body
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError as e:
            return JsonResponse({
                'error': 'داده‌های ارسالی نامعتبر است',
                'debug_info': f'JSON decode error: {str(e)}'
            }, status=400)
        
        text = data.get('text', '')
        
        if not text:
            return JsonResponse({
                'error': 'متن خالی است',
                'debug_info': 'Empty text provided'
            }, status=400)
        
        # Convert text to speech
        success = coffee_ai.text_to_speech(text)
        
        return JsonResponse({
            'success': success,
            'debug_info': 'Text to speech conversion completed'
        })
        
    except Exception as e:
        logger.error(f"Text to speech error: {str(e)}")
        return JsonResponse({
            'error': 'خطا در تبدیل متن به صدا',
            'debug_info': f'TTS exception: {str(e)}'
        }, status=500) 