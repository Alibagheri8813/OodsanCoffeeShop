from django.urls import path, include
from . import views
# from . import voice_ai_assistant
# from . import ai_assistant
# from . import advanced_views
# from django.contrib.auth import views as auth_views

# app_name = 'shop'  # Commented out to remove namespace conflict

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
    path('order/<int:order_id>/pay/', views.pay_order, name='pay_order'),
    
    # Social Features
    path('like/', views.toggle_like, name='toggle_like'),
    path('like/<int:product_id>/', views.like_product, name='like_product'),
    path('unlike/<int:product_id>/', views.unlike_product, name='unlike_product'),
    path('product/<int:product_id>/like/', views.toggle_product_like, name='toggle_product_like'),
    path('product/<int:product_id>/favorite/', views.toggle_product_favorite, name='toggle_product_favorite'),
    path('product/<int:product_id>/comment/', views.add_product_comment, name='add_product_comment'),
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
    # path('ai/chat/', ai_assistant.ai_chat, name='ai_chat'),
    
    # Voice-based AI Chat
    # path('ai/voice/', ai_assistant.voice_chat, name='voice_chat'),
    
    # Speech-to-Text
    # path('ai/speech-to-text/', ai_assistant.speech_to_text, name='speech_to_text'),
    
    # Text-to-Speech
    # path('ai/text-to-speech/', ai_assistant.text_to_speech, name='text_to_speech'),
    
    # ===== PHASE 3: ADVANCED FEATURES =====
    
    # AI-Powered Recommendations
    path('recommendations/', views.personalized_recommendations, name='personalized_recommendations'),
    path('track-recommendation/<int:product_id>/', views.track_recommendation_view, name='track_recommendation_view'),
    
    # Advanced Search & Filters
    path('advanced-search/', views.advanced_search, name='advanced_search'),
    path('search/', views.search_products, name='search_products'),
    
    # Real-time Analytics Dashboard (Admin Only)
    path('analytics/', views.analytics_dashboard, name='analytics_dashboard'),
    path('customer-insights/', views.customer_insights, name='customer_insights'),
    
    # Enhanced Product Views
    path('enhanced-product/<int:product_id>/', views.enhanced_product_detail, name='enhanced_product_detail'),
    
    # Loyalty Program
    path('loyalty/', views.loyalty_dashboard, name='loyalty_dashboard'),
    path('redeem-points/', views.redeem_points, name='redeem_points'),
    
    # API Endpoints
    path('api/recommendations/', views.api_recommendations, name='api_recommendations'),
    path('api/analytics/', views.api_analytics, name='api_analytics'),
    
    # Voice AI Assistant - Temporarily disabled
    # path('voice-ai/', views.voice_ai_assistant_page, name='voice_ai_assistant'),
    # path('voice-ai/initialize/', voice_ai_assistant.initialize_ai, name='voice_ai_initialize'),
    # path('voice-ai/chat/', voice_ai_assistant.voice_chat, name='voice_ai_chat'),
    # path('voice-ai/text-chat/', voice_ai_assistant.text_chat, name='voice_ai_text_chat'),
    # path('voice-ai/stop/', voice_ai_assistant.stop_speech, name='voice_ai_stop'),
    # path('voice-ai/status/', voice_ai_assistant.ai_status, name='voice_ai_status'),
    
    # Existing URLs (keep them for compatibility)
    path('categories/', views.category_list, name='category_list'),
    path('category/<int:category_id>/', views.category_detail, name='category_detail'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('order-history/', views.order_history, name='order_history'),
    path('change-password/', views.change_password, name='change_password'),
    path('submit-order-feedback/<int:order_id>/', views.submit_order_feedback, name='submit_order_feedback'),
    
    # Health & Monitoring Endpoints
    path('health/', views.health_check, name='health_check'),
    path('system-status/', views.system_status, name='system_status'),
    
    # Profile management
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    
    # Address management
    path('address/add/', views.add_address, name='add_address'),
    path('address/edit/<int:address_id>/', views.edit_address, name='edit_address'),
    path('address/delete/<int:address_id>/', views.delete_address, name='delete_address'),
    
    # Order Status Management API
    path('api/orders/<int:order_id>/transition/', views.transition_order_status, name='transition_order_status'),
    path('api/orders/<int:order_id>/mark-paid/', views.mark_order_as_paid, name='mark_order_as_paid'),
    path('api/orders/<int:order_id>/mark-ready/', views.mark_order_as_ready, name='mark_order_as_ready'),
    path('api/orders/<int:order_id>/start-shipping/', views.start_order_shipping_preparation, name='start_order_shipping_preparation'),
    path('api/orders/<int:order_id>/mark-transit/', views.mark_order_in_transit, name='mark_order_in_transit'),
    path('api/orders/<int:order_id>/status/', views.get_order_status, name='get_order_status'),
] 