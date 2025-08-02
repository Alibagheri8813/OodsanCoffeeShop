import os
from django.conf import settings

# AI Assistant Configuration
# Use environment variable for security - set OPENAI_API_KEY in your environment
OPENAI_API_KEY = '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'

# AI Configuration - Using GPT-3.5-turbo for cost efficiency
AI_MODEL = "gpt-3.5-turbo"  # Free tier compatible
AI_MAX_TOKENS = 800  # Increased for detailed coffee responses
AI_TEMPERATURE = 0.8  # Slightly higher for more creative responses
AI_TOP_P = 0.9

# Comprehensive fallback responses for coffee industry
FALLBACK_RESPONSES = {
    'greeting': 'سلام! من کافه‌مستر هستم، متخصص قهوه با 25 سال تجربه. چطور می‌تونم کمکتون کنم؟',
    
    'coffee_general': 'قهوه یکی از محبوب‌ترین نوشیدنی‌های جهان است! انواع مختلفی داریم: اسپرسو، آمریکانو، لاته، کاپوچینو، و قهوه‌های فیلتری. کدوم نوع قهوه رو بیشتر دوست دارید؟',
    
    'roasting': 'روست قهوه فرآیند حرارت دادن دانه‌های سبز قهوه است. سطوح مختلف داریم: لایت (350-400°F)، مدیوم (400-430°F)، مدیوم-دارک (430-450°F)، و دارک (450-480°F). هر سطح طعم و عطر متفاوتی داره.',
    
    'brewing': 'روش‌های دم کردن قهوه شامل: اسپرسو (9 بار فشار)، پور-اور (V60، کیمکس)، فرنچ پرس (4-5 دقیقه)، ایرپرس (1-2 دقیقه)، و کولد برو (12-24 ساعت). کدوم روش رو امتحان کردید؟',
    
    'equipment': 'تجهیزات قهوه شامل: دستگاه اسپرسو (نیمه-اتوماتیک، سوپر-اتوماتیک)، آسیاب (بر، تیغه‌ای)، ترازو (دقت 0.1 گرم)، دماسنج، و فیلترها. کدوم تجهیزات رو می‌خواید بشناسید؟',
    
    'pricing': 'قیمت قهوه بستگی به نوع دانه، روش روست، و برند داره. قهوه‌های تخصصی معمولاً 50-200 هزار تومان برای 250 گرم هستند. می‌تونم محصولات ما رو معرفی کنم.',
    
    'hours': 'ساعت کاری ما: شنبه تا چهارشنبه 8 صبح تا 10 شب، پنجشنبه و جمعه 9 صبح تا 11 شب. همیشه آماده سرویس‌دهی هستیم!',
    
    'delivery': 'سرویس تحویل در تهران در کمتر از 30 دقیقه. حداقل سفارش 50 هزار تومان. قهوه‌های تازه و داغ رو درب منزل تحویل می‌دیم.',
    
    'menu': 'منوی ما شامل: اسپرسو، آمریکانو، لاته، کاپوچینو، موکا، قهوه‌های فیلتری، و دسرهای قهوه‌ای. همچنین دانه‌های قهوه تخصصی برای فروش داریم.',
    
    'error': 'متأسفانه در حال حاضر دستیار هوشمند در دسترس نیست. لطفاً کمی بعد تلاش کنید یا با پشتیبانی تماس بگیرید. شماره تماس: 021-12345678'
}

# Coffee-specific knowledge base for fallback responses
COFFEE_KNOWLEDGE = {
    'origins': {
        'ethiopian': 'قهوه اتیوپی: طعم گل‌دار و مرکبات، اسیدیته روشن، معمولاً لایت تا مدیوم روست',
        'colombian': 'قهوه کلمبیا: متعادل و مغزدار، اسیدیته متوسط، مدیوم روست',
        'brazilian': 'قهوه برزیل: اسیدیته کم، طعم شکلاتی، دارک روست',
        'guatemalan': 'قهوه گواتمالا: ادویه‌ای و دودی، مدیوم-دارک روست',
        'kenyan': 'قهوه کنیا: اسیدیته شراب‌مانند، طعم توت، مدیوم روست'
    },
    
    'brewing_methods': {
        'espresso': 'اسپرسو: 9 بار فشار، 25-30 ثانیه، 18-21 گرم دوز',
        'pour_over': 'پور-اور: V60، کیمکس، کالیتا ویو - کنترل کامل روی دم کردن',
        'french_press': 'فرنچ پرس: آسیاب درشت، 4-5 دقیقه، غوطه‌وری کامل',
        'aeropress': 'ایرپرس: 1-2 دقیقه، روش معکوس، فیلتر کاغذی',
        'cold_brew': 'کولد برو: 12-24 ساعت، آسیاب درشت، دمای اتاق'
    },
    
    'roasting_levels': {
        'light': 'لایت روست: 350-400°F، اسیدیته بالا، طعم‌های اصلی دانه',
        'medium': 'مدیوم روست: 400-430°F، متعادل، طعم کارامل',
        'medium_dark': 'مدیوم-دارک: 430-450°F، غنی، طعم شکلات',
        'dark': 'دارک روست: 450-480°F، قوی، دودی، کافئین کمتر'
    }
}

# Voice interaction settings
VOICE_SETTINGS = {
    'speech_rate': 150,  # Words per minute
    'volume': 0.9,       # Volume level (0-1)
    'language': 'fa-IR', # Persian language
    'voice_type': 'persian'  # Preferred voice type
}

# AI model alternatives (free options)
FREE_AI_MODELS = {
    'gpt-3.5-turbo': 'OpenAI GPT-3.5 Turbo (free tier)',
    'gpt-4': 'OpenAI GPT-4 (paid)',
    'claude-3-sonnet': 'Anthropic Claude (paid)',
    'gemini-pro': 'Google Gemini Pro (free tier)'
} 