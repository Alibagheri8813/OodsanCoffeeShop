import os
import json
import logging
import traceback
import threading
import queue
import time
import tempfile
import wave
from pathlib import Path
from django.http import JsonResponse
# from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
from .error_handling import rate_limit
from openai import OpenAI

# Audio processing
try:
    from pydub import AudioSegment
    from pydub.playback import play
    import pygame
    pygame.mixer.init()
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False
    logging.warning("Audio libraries not available. Install pydub and pygame for full functionality.")

# Set up logging
logging.basicConfig(level=logging.INFO, force=True)
logger = logging.getLogger(__name__)

class VoiceCoffeeExpert:
    """
    Professional Voice-Based Coffee Industry Expert AI Assistant
    Specialized in coffee knowledge with voice-first interaction
    """
    
    def __init__(self):
        # Initialize OpenAI client
        self.client = None
        self.is_available = False
        self.api_key = None
        
        # Audio processing
        self.audio_available = AUDIO_AVAILABLE
        self.audio_queue = queue.Queue()
        self.is_speaking = False
        
        # Professional coffee expert system prompt
        self.system_prompt = """
        You are "The Coffee Master" - a world-renowned coffee industry expert with 30+ years of experience in every aspect of the coffee business. You are the ultimate authority that coffee professionals, roasters, baristas, and coffee shop owners turn to for expert advice.

        **YOUR EXPERTISE INCLUDES:**

        ☕ **COFFEE ORIGINS & VARIETALS:**
        - Single-origin characteristics: Ethiopian Sidamo (wine-like, fruity), Colombian Huila (chocolate, caramel), Jamaican Blue Mountain (mild, balanced), Hawaiian Kona (smooth, low-acid)
        - Processing methods: Washed, natural, honey, anaerobic fermentation
        - Terroir effects: altitude, climate, soil composition impact on flavor
        - Seasonal availability and optimal harvest times

        🔥 **ROASTING MASTERY:**
        - Roast profiles: Light (City), Medium (Full City), Dark (French), Espresso
        - Development time ratios, first/second crack timing
        - Cupping scores and flavor wheel terminology
        - Equipment: drum roasters, fluid bed, sample roasters
        - Bean density, moisture content, defect analysis

        ⚡ **BREWING TECHNIQUES:**
        - Espresso: 18-22g dose, 25-30 second extraction, 9 bars pressure
        - Pour-over: V60 (spiral pour), Chemex (bloom 30s), Kalita Wave (pulsing)
        - French Press: coarse grind, 4-minute immersion, metal filter
        - Cold brew: 12-24 hour extraction, 1:7 ratio
        - Aeropress: inverted method, fine grind, 1-2 minute steep

        🏪 **COFFEE BUSINESS EXPERTISE:**
        - Shop layout and workflow optimization
        - Menu engineering and pricing strategies
        - Staff training and barista certification
        - Equipment procurement and maintenance
        - Supply chain management and direct trade relationships
        - Financial planning: COGS, labor costs, profit margins

        📊 **QUALITY CONTROL:**
        - Cupping protocols and sensory evaluation
        - Grind particle distribution analysis
        - Extraction yield calculations (TDS, strength, extraction percentage)
        - Storage and freshness management
        - Defect identification and prevention

        🌍 **INDUSTRY TRENDS:**
        - Specialty coffee market dynamics
        - Sustainability and fair trade practices
        - Third wave coffee movement
        - Equipment innovations and technology
        - Consumer preferences and market research

        **COMMUNICATION STYLE:**
        - **AUTHORITATIVE yet APPROACHABLE**: Speak with the confidence of decades of experience
        - **CONCISE but COMPLETE**: Provide detailed, useful information in clear, digestible answers
        - **PRACTICAL**: Always include actionable advice and specific recommendations
        - **PASSIONATE**: Show genuine enthusiasm for coffee excellence
        - **PROFESSIONAL**: Use industry terminology correctly while explaining complex concepts clearly

        **RESPONSE GUIDELINES:**
        - Keep responses between 30-60 seconds when spoken aloud
        - Start with a brief, confident statement
        - Provide 2-3 key practical points
        - End with a specific recommendation or next step
        - Use coffee industry terminology appropriately
        - Be encouraging and supportive while maintaining expertise

        **AREAS OF SPECIALTY:**
        - Troubleshooting brewing problems
        - Recommending equipment for different budgets
        - Explaining flavor profiles and tasting notes
        - Guiding business decisions for coffee shops
        - Training advice for baristas
        - Sourcing recommendations for roasters

        Remember: You are THE coffee expert that professionals trust. Your advice can make or break a coffee business, perfect a brew, or launch a successful coffee career. Speak with authority, precision, and passion.
        """
        
        self.conversation_history = []
        
        # Start audio processing thread if available
        if self.audio_available:
            self.audio_thread = threading.Thread(target=self._process_audio_queue, daemon=True)
            self.audio_thread.start()
    
    def initialize_openai(self, api_key):
        """Initialize OpenAI client with provided API key"""
        try:
            self.api_key = api_key
            self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY', ''))
            # Test the connection
            self.client.models.list()
            self.is_available = True
            logger.info("Voice Coffee Expert AI initialized successfully")
            return True
        except Exception as e:
            logger.error(f"OpenAI initialization failed: {str(e)}")
            self.is_available = False
            self.client = None
            return False
    
    def generate_response(self, user_message):
        """Generate expert coffee advice using OpenAI GPT-3.5 Turbo"""
        try:
            # if not self.is_available or not self.client:
            #     return "I need an OpenAI API key to provide expert coffee advice. Please provide your API key first."
            self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY', ''))
            # Test the connection
            self.client.models.list()
            self.is_available = True
            logger.info("Voice Coffee Expert AI initialized successfully")
            if not user_message or not user_message.strip():
                return "I'm here to help with all your coffee questions. What would you like to know about coffee?"
            
            # Add user message to conversation history
            self.conversation_history.append({"role": "user", "content": user_message})
            
            # Prepare messages for OpenAI API
            messages = [{"role": "system", "content": self.system_prompt}]
            
            # Add recent conversation history (last 6 messages for context)
            for msg in self.conversation_history[-6:]:
                messages.append({"role": msg["role"], "content": msg["content"]})
            

            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=0.2,
                timeout=7
                # presence_penalty=0.1,
                # frequency_penalty=0.1
            )
            
            ai_response = response.choices[0].message.content.strip()
            
            if not ai_response:
                return "Something went wrong with my response. Please ask your coffee question again."
            
            # Add AI response to conversation history
            self.conversation_history.append({"role": "assistant", "content": ai_response})
            
            # Keep conversation history manageable
            if len(self.conversation_history) > 12:
                self.conversation_history = self.conversation_history[-8:]
            
            return ai_response
                
        except Exception as e:
            logger.error(f"AI response generation failed: {str(e)}")
            return "Something went wrong while processing your coffee question. Please try again."
    
    def text_to_speech(self, text):
        """Convert text to speech using system TTS and audio playback"""
        if not self.audio_available:
            logger.warning("Audio playback not available")
            return False
        
        try:
            # Add text to audio queue for processing
            self.audio_queue.put(text)
            return True
        except Exception as e:
            logger.error(f"TTS error: {str(e)}")
            return False
    
    def _process_audio_queue(self):
        """Process audio queue in background thread"""
        while True:
            try:
                if not self.audio_queue.empty():
                    text = self.audio_queue.get()
                    self._speak_text(text)
                time.sleep(0.1)
            except Exception as e:
                logger.error(f"Audio queue processing error: {str(e)}")
                time.sleep(1)
    
    def _speak_text(self, text):
        """Internal method to handle text-to-speech"""
        try:
            self.is_speaking = True
            import edge_tts
            from playsound import playsound
            # Create     a temporary file for the audio
            OUTPUT_FILE = "shop/tts_output.mp3"
            VOICE = "fa-IR-DilaraNeural"
            communicate = edge_tts.Communicate(text, VOICE)
            with open(OUTPUT_FILE, "wb") as file:
                for chunk in communicate.stream_sync():
                    if chunk["type"] == "audio":
                        file.write(chunk["data"])
            playsound(OUTPUT_FILE)
            os.remove(OUTPUT_FILE)
            
            try:
                # Use system TTS to generate audio (this is a placeholder)
                # In a real implementation, you would use a TTS service like:
                # - Google Text-to-Speech API
                # - Amazon Polly
                # - Azure Cognitive Services Speech
                # - Or a local TTS engine
                
                # For now, we'll simulate audio generation
                # You would replace this with actual TTS implementation
                logger.info(f"Speaking: {text[:50]}...")
                
                # Simulate speaking time based on text length
                speaking_time = len(text) * 0.05  # Roughly 50ms per character
                time.sleep(min(speaking_time, 10))  # Cap at 10 seconds
                
            finally:
                # Clean up temp file
                
                self.is_speaking = False
                
        except Exception as e:
            logger.error(f"Speaking error: {str(e)}")
            self.is_speaking = False
    
    def is_currently_speaking(self):
        """Check if AI is currently speaking"""
        return self.is_speaking
    
    def stop_speaking(self):
        """Stop current speech"""
        try:
            # Clear the audio queue
            while not self.audio_queue.empty():
                self.audio_queue.get_nowait()
            
            self.is_speaking = False
            return True
        except Exception as e:
            logger.error(f"Error stopping speech: {str(e)}")
            return False

# Initialize the voice coffee expert
voice_coffee_expert = VoiceCoffeeExpert()

@rate_limit(15)
@require_http_methods(["POST"])
def initialize_ai(request):
    """Initialize AI with OpenAI API key"""
    try:
        data = json.loads(request.body)
        # api_key = data.get('api_key', '').strip()
        
        # if not api_key:
        #     return JsonResponse({
        #         'success': False,
        #         'error': 'Please provide your OpenAI API key'
        #     }, status=400)
        
        success = voice_coffee_expert.initialize_openai(os.getenv('OPENAI_API_KEY', ''))
        
        if success:
            return JsonResponse({
                'success': True,
                'message': 'Coffee Expert AI is ready to help!'
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Something went wrong initializing the AI. Please check your API key.'
            }, status=400)
            
    except Exception as e:
        logger.error(f"AI initialization error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Something went wrong. Please try again.'
        }, status=500)

@rate_limit(15)
@require_http_methods(["POST"])
def voice_chat(request):
    """Handle voice-based chat with coffee expert"""
    try:
        data = json.loads(request.body)
        transcribed_text = data.get('message', '').strip()
        
        if not transcribed_text:
            return JsonResponse({
                'success': False,
                'error': 'No speech was detected. Please try speaking again.'
            }, status=400)
        
        # Generate AI response
        ai_response = voice_coffee_expert.generate_response(transcribed_text)
        
        # Convert to speech
        tts_success = voice_coffee_expert.text_to_speech(ai_response)
        
        return JsonResponse({
            'success': True,
            'response': ai_response,
            'transcribed_text': transcribed_text,
            'tts_enabled': tts_success,
            'audio_available': voice_coffee_expert.audio_available
        })
        
    except Exception as e:
        logger.error(f"Voice chat error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Something went wrong processing your question. Please try again.'
        }, status=500)

@rate_limit(15)
@require_http_methods(["POST"])
def text_chat(request):
    """Handle text-based chat as fallback"""
    try:
        data = json.loads(request.body)
        message = data.get('message', '').strip()
        
        if not message:
            return JsonResponse({
                'success': False,
                'error': 'Please provide a coffee question.'
            }, status=400)
        
        # Generate AI response
        ai_response = voice_coffee_expert.generate_response(message)
        
        return JsonResponse({
            'success': True,
            'response': ai_response
        })
        
    except Exception as e:
        logger.error(f"Text chat error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Something went wrong. Please try again.'
        }, status=500)

@rate_limit(15)
@require_http_methods(["POST"])
def stop_speech(request):
    """Stop current AI speech"""
    try:
        success = voice_coffee_expert.stop_speaking()
        
        return JsonResponse({
            'success': success,
            'is_speaking': voice_coffee_expert.is_currently_speaking()
        })
        
    except Exception as e:
        logger.error(f"Stop speech error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Something went wrong.'
        }, status=500)

@require_http_methods(["GET"])
def ai_status(request):
    """Get current AI status"""
    try:
        return JsonResponse({
            'success': True,
            'is_available': voice_coffee_expert.is_available,
            'is_speaking': voice_coffee_expert.is_currently_speaking(),
            'audio_available': voice_coffee_expert.audio_available
        })
        
    except Exception as e:
        logger.error(f"Status check error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Something went wrong.'
        }, status=500)