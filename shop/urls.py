from django.urls import path
from . import views
from . import ai_assistant
from . import advanced_views
# from django.contrib.auth import views as auth_views

urlpatterns = [
    # Main pages
    path('', views.product_list, name='shop_home'),
    path('products/', views.product_list, name='product_list'),
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),
    
    # Shopping Cart System
    path('cart/', views.cart_view, name='cart'),
    path('cart-view/', views.cart_view, name='cart_view'),
    path('cart/add/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/', views.update_cart_item, name='update_cart_item'),
    path('cart/remove/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/count/', views.cart_count, name='cart_count'),
    
    # User Authentication & Profile
    path('register/', views.register, name='register'),
    path('profile/', views.profile, name='profile'),
    path('user-profile/', views.user_profile, name='user_profile'),
    path('login/', views.custom_login, name='login'),
    path('logout/', views.custom_logout, name='logout'),
    path('signup/', views.signup, name='signup'),
    
    # Order Management
    path('checkout/', views.checkout, name='checkout'),
    path('orders/', views.order_list, name='order_list'),
    path('order/<int:order_id>/', views.order_detail, name='order_detail'),
    
    # Social Features
    path('like/', views.toggle_like, name='toggle_like'),
    path('favorite/', views.toggle_favorite, name='toggle_favorite'),
    path('favorites/', views.favorite_products, name='favorite_products'),
    path('add-to-favorites/<int:product_id>/', views.add_to_favorites, name='add_to_favorites'),
    path('remove-from-favorites/<int:product_id>/', views.remove_from_favorites, name='remove_from_favorites'),
    path('product-list-by-category/<int:category_id>/', views.product_list, name='product_list_by_category'),
    
    # Notifications
    path('notifications/', views.notifications, name='notifications'),
    path('notifications/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/<int:notification_id>/delete/', views.delete_notification, name='delete_notification'),
    path('notifications/read-all/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
    path('address-completion-check/', views.address_completion_check, name='address_completion_check'),
    path('user-notifications/', views.notifications, name='user_notifications'),
    
    # ===== AI ASSISTANT - VOICE INTERACTION =====
    
    # AI Assistant Page
    path('ai-assistant/', views.ai_assistant_view, name='ai_assistant'),
    
    # Text-based AI Chat
    path('ai/chat/', ai_assistant.ai_chat, name='ai_chat'),
    
    # Voice-based AI Chat
    path('ai/voice/', ai_assistant.voice_chat, name='voice_chat'),
    
    # Speech-to-Text
    path('ai/speech-to-text/', ai_assistant.speech_to_text, name='speech_to_text'),
    
    # Text-to-Speech
    path('ai/text-to-speech/', ai_assistant.text_to_speech, name='text_to_speech'),
    
    # ===== PHASE 3: ADVANCED FEATURES =====
    
    # AI-Powered Recommendations
    path('recommendations/', advanced_views.personalized_recommendations, name='personalized_recommendations'),
    path('track-recommendation/<int:product_id>/', advanced_views.track_recommendation_view, name='track_recommendation_view'),
    
    # Advanced Search & Filters
    path('advanced-search/', advanced_views.advanced_search, name='advanced_search'),
    path('search/', views.search_products, name='search_products'),
    
    # Real-time Analytics Dashboard
    path('analytics/', advanced_views.analytics_dashboard, name='analytics_dashboard'),
    path('customer-insights/', advanced_views.customer_insights, name='customer_insights'),
    
    # Enhanced Product Views
    path('enhanced-product/<int:product_id>/', advanced_views.enhanced_product_detail, name='enhanced_product_detail'),
    
    # Loyalty Program
    path('loyalty/', advanced_views.loyalty_dashboard, name='loyalty_dashboard'),
    path('redeem-points/', advanced_views.redeem_points, name='redeem_points'),
    
    # API Endpoints
    path('api/recommendations/', advanced_views.api_recommendations, name='api_recommendations'),
    path('api/analytics/', advanced_views.api_analytics, name='api_analytics'),
    
    # Existing URLs (keep them for compatibility)
    path('categories/', views.category_list, name='category_list'),
    path('category/<int:category_id>/', views.category_detail, name='category_detail'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('order-history/', views.order_history, name='order_history'),
    path('change-password/', views.change_password, name='change_password'),
    path('submit-order-feedback/<int:order_id>/', views.submit_order_feedback, name='submit_order_feedback'),
] 