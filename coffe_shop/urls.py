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
# Explicit imports to prevent namespace clashes between user-facing and admin views
from shop import views as shop_views
from shop import admin_views as admin_views
from django.contrib.sitemaps.views import sitemap
from shop.sitemaps import ProductSitemap, CategorySitemap
from django.http import HttpResponse
# from shop.ai_assistant import ai_chat, voice_chat

sitemaps = {
    'products': ProductSitemap,
    'categories': CategorySitemap,
}

urlpatterns = [
    # Admin URLs (must come before admin.site.urls)
    path('admin/dashboard/', admin_views.admin_dashboard, name='admin_dashboard'),
    path('admin/notifications/', admin_views.admin_notifications, name='admin_notifications'),
    path('admin/notifications/<int:notification_id>/read/', admin_views.mark_notification_read, name='admin_mark_notification_read'),
    path('admin/notifications/read-all/', admin_views.mark_all_notifications_read, name='admin_mark_all_notifications_read'),
    path('admin/notifications/<int:notification_id>/delete/', admin_views.delete_notification, name='admin_delete_notification'),
    path('admin/orders/', admin_views.admin_order_list, name='admin_order_list'),
    path('admin/orders/<int:order_id>/', admin_views.admin_order_detail, name='admin_order_detail'),
    path('admin/orders/bulk-status/', admin_views.admin_bulk_order_status, name='admin_bulk_order_status'),
    path('admin/analytics/data/', admin_views.admin_analytics_data, name='admin_analytics_data'),
    path('admin/analytics/export.csv', admin_views.admin_export_orders_csv, name='admin_export_orders_csv'),
    path('admin/analytics/top-products/', admin_views.admin_analytics_top_products, name='admin_analytics_top_products'),
    path('admin/analytics/category-breakdown/', admin_views.admin_analytics_category_breakdown, name='admin_analytics_category_breakdown'),
    path('admin/users/<int:user_id>/update-tier/', admin_views.admin_update_user_tier, name='admin_update_user_tier'),
    path('admin/orders/summary/', admin_views.admin_orders_summary, name='admin_orders_summary'),
    path('admin/orders/recent.json', admin_views.admin_recent_orders_json, name='admin_recent_orders_json'),
    
    # Django Admin (must come after custom admin URLs)
    path('admin/', admin.site.urls),
    
    # Main site URLs
    path('', shop_views.video_intro, name='video_intro'),  # Show video intro first
    path('home/', shop_views.home, name='home'),
    path('shop/', include('shop.urls')),
    
    # User notification URLs
    path('shop/profile/notifications/', shop_views.notifications, name='user_notifications'),
    path('shop/profile/notifications/mark-read/<int:notification_id>/', shop_views.mark_notification_read, name='user_mark_notification_read'),
    path('shop/profile/notifications/mark-all-read/', shop_views.mark_all_notifications_read, name='user_mark_all_notifications_read'),
    
    # AI Assistant URLs
    # path('ai/chat/', ai_chat, name='ai_chat'),
    # path('ai/voice/', voice_chat, name='voice_chat'),

    # SEO
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
]

# Simple robots.txt
def robots_txt(_request):
    lines = [
        "User-agent: *",
        "Disallow:",
        "Sitemap: " + _request.build_absolute_uri('/sitemap.xml')
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")

urlpatterns += [
    path('robots.txt', robots_txt, name='robots_txt'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
