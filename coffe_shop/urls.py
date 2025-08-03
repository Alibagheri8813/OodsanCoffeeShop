"""
URL configuration for coffe_shop project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from shop.views import *
from shop.admin_views import *
# from shop.ai_assistant import ai_chat, voice_chat

urlpatterns = [
    # Admin URLs (must come before admin.site.urls)
    path('admin/dashboard/', admin_dashboard, name='admin_dashboard'),
    path('admin/notifications/', admin_notifications, name='admin_notifications'),
    path('admin/notifications/<int:notification_id>/read/', mark_notification_read, name='mark_notification_read'),
    path('admin/notifications/read-all/', mark_all_notifications_read, name='mark_all_notifications_read'),
    path('admin/notifications/<int:notification_id>/delete/', delete_notification, name='delete_notification'),
    path('admin/orders/', admin_order_list, name='admin_order_list'),
    path('admin/orders/<int:order_id>/', admin_order_detail, name='admin_order_detail'),
    path('admin/orders/bulk-status/', admin_bulk_order_status, name='admin_bulk_order_status'),
    
    # Django Admin (must come after custom admin URLs)
    path('admin/', admin.site.urls),
    
    # Main site URLs
    path('', video_intro, name='video_intro'),  # Show video intro first
    path('home/', home, name='home'),
    path('shop/', include('shop.urls')),
    
    # User notification URLs
    path('shop/profile/notifications/', notifications, name='user_notifications'),
    path('shop/profile/notifications/mark-read/<int:notification_id>/', mark_notification_read, name='user_mark_notification_read'),
    path('shop/profile/notifications/mark-all-read/', mark_all_notifications_read, name='user_mark_all_notifications_read'),
    
    # AI Assistant URLs
    # path('ai/chat/', ai_chat, name='ai_chat'),
    # path('ai/voice/', voice_chat, name='voice_chat'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
