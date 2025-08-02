import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import KMeans
from collections import defaultdict, Counter
from django.db.models import Q, Count, Sum, Avg
from django.utils import timezone
from datetime import timedelta
import logging
from .models import (
    Product, User, Order, OrderItem, ProductFavorite, ProductLike, 
    UserActivity, ProductRecommendation, CustomerSegment, AnalyticsEvent
)

logger = logging.getLogger(__name__)

class CoffeeShopAIEngine:
    """Advanced AI recommendation engine for coffee shop"""
    
    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words=None,
            ngram_range=(1, 2)
        )
        self.product_vectors = None
        self.product_similarity_matrix = None
        self.user_clusters = None
        
    def build_product_similarity_matrix(self):
        """Build product similarity matrix using TF-IDF and cosine similarity"""
        try:
            # Get all products with their descriptions
            products = Product.objects.filter(is_active=True)
            
            # Create product descriptions for vectorization
            product_descriptions = []
            product_ids = []
            
            for product in products:
                description = f"{product.name} {product.description} {product.category.name}"
                product_descriptions.append(description)
                product_ids.append(product.id)
            
            # Vectorize product descriptions
            self.product_vectors = self.vectorizer.fit_transform(product_descriptions)
            
            # Calculate cosine similarity
            self.product_similarity_matrix = cosine_similarity(self.product_vectors)
            
            # Create similarity dictionary
            self.product_similarities = {}
            for i, product_id in enumerate(product_ids):
                similarities = []
                for j, other_product_id in enumerate(product_ids):
                    if i != j:
                        similarities.append((other_product_id, self.product_similarity_matrix[i][j]))
                # Sort by similarity and take top 10
                similarities.sort(key=lambda x: x[1], reverse=True)
                self.product_similarities[product_id] = similarities[:10]
                
            logger.info(f"Built similarity matrix for {len(products)} products")
            
        except Exception as e:
            logger.error(f"Error building similarity matrix: {str(e)}")
    
    def analyze_user_behavior(self, user):
        """Analyze user behavior patterns"""
        try:
            # Get user's recent activities
            recent_activities = UserActivity.objects.filter(
                user=user,
                timestamp__gte=timezone.now() - timedelta(days=90)
            ).select_related('product', 'category')
            
            # Analyze purchase history
            orders = Order.objects.filter(
                user=user,
                status__in=['delivered', 'shipped']
            ).select_related('items__product__category')
            
            # Analyze favorites and likes
            favorites = ProductFavorite.objects.filter(user=user).select_related('product__category')
            likes = ProductLike.objects.filter(user=user).select_related('product__category')
            
            # Calculate user preferences
            preferences = {
                'categories': defaultdict(int),
                'price_range': {'min': float('inf'), 'max': 0},
                'favorite_products': [],
                'purchase_frequency': len(orders),
                'total_spent': sum(order.total_amount for order in orders),
                'avg_order_value': 0,
                'preferred_time': defaultdict(int),
                'device_preference': defaultdict(int)
            }
            
            # Analyze category preferences
            for activity in recent_activities:
                if activity.category:
                    preferences['categories'][activity.category.id] += 1
                if activity.product:
                    preferences['categories'][activity.product.category.id] += 1
                    
                # Track device preference
                preferences['device_preference'][activity.device_type] += 1
                
                # Track time preferences
                hour = activity.timestamp.hour
                if 6 <= hour < 12:
                    preferences['preferred_time']['morning'] += 1
                elif 12 <= hour < 18:
                    preferences['preferred_time']['afternoon'] += 1
                else:
                    preferences['preferred_time']['evening'] += 1
            
            # Analyze purchase patterns
            for order in orders:
                for item in order.items.all():
                    preferences['categories'][item.product.category.id] += 2  # Purchase gets higher weight
                    price = float(item.product.price)
                    preferences['price_range']['min'] = min(preferences['price_range']['min'], price)
                    preferences['price_range']['max'] = max(preferences['price_range']['max'], price)
            
            # Analyze favorites
            for favorite in favorites:
                preferences['categories'][favorite.product.category.id] += 1
                preferences['favorite_products'].append(favorite.product.id)
            
            # Analyze likes
            for like in likes:
                preferences['categories'][like.product.category.id] += 1
            
            # Calculate average order value
            if preferences['purchase_frequency'] > 0:
                preferences['avg_order_value'] = preferences['total_spent'] / preferences['purchase_frequency']
            
            # Normalize price range
            if preferences['price_range']['min'] == float('inf'):
                preferences['price_range']['min'] = 0
            
            return preferences
            
        except Exception as e:
            logger.error(f"Error analyzing user behavior: {str(e)}")
            return {}
    
    def generate_recommendations(self, user, limit=6):
        """Generate personalized product recommendations"""
        try:
            # Get user preferences
            preferences = self.analyze_user_behavior(user)
            
            if not preferences:
                # Fallback to popular products
                return self.get_popular_products(limit)
            
            # Get products user hasn't purchased or favorited
            purchased_products = set(OrderItem.objects.filter(
                order__user=user,
                order__status__in=['delivered', 'shipped']
            ).values_list('product_id', flat=True))
            
            favorited_products = set(ProductFavorite.objects.filter(
                user=user
            ).values_list('product_id', flat=True))
            
            excluded_products = purchased_products | favorited_products
            
            # Build recommendation candidates
            candidates = []
            
            # 1. Category-based recommendations
            top_categories = sorted(
                preferences['categories'].items(),
                key=lambda x: x[1],
                reverse=True
            )[:3]
            
            for category_id, weight in top_categories:
                category_products = Product.objects.filter(
                    category_id=category_id,
                    is_active=True
                ).exclude(id__in=excluded_products)
                
                for product in category_products:
                    score = weight * 0.4  # Category weight
                    candidates.append((product, score, f"Based on your interest in {product.category.name}"))
            
            # 2. Similarity-based recommendations
            if self.product_similarities:
                for product_id in preferences['favorite_products'][:5]:
                    if product_id in self.product_similarities:
                        for similar_product_id, similarity_score in self.product_similarities[product_id]:
                            try:
                                similar_product = Product.objects.get(id=similar_product_id, is_active=True)
                                if similar_product.id not in excluded_products:
                                    score = similarity_score * 0.6
                                    candidates.append((similar_product, score, "Similar to products you like"))
                            except Product.DoesNotExist:
                                continue
            
            # 3. Price-based recommendations
            if preferences['price_range']['max'] > 0:
                avg_price = (preferences['price_range']['min'] + preferences['price_range']['max']) / 2
                price_range_products = Product.objects.filter(
                    is_active=True,
                    price__range=(avg_price * 0.7, avg_price * 1.3)
                ).exclude(id__in=excluded_products)
                
                for product in price_range_products:
                    score = 0.3
                    candidates.append((product, score, "Matches your price preference"))
            
            # 4. Popular products in user's preferred categories
            for category_id, weight in top_categories[:2]:
                popular_products = Product.objects.filter(
                    category_id=category_id,
                    is_active=True
                ).annotate(
                    like_count=Count('likes'),
                    favorite_count=Count('favorites')
                ).order_by('-like_count', '-favorite_count')[:5]
                
                for product in popular_products:
                    if product.id not in excluded_products:
                        score = weight * 0.2
                        candidates.append((product, score, "Popular in categories you like"))
            
            # Sort candidates by score and remove duplicates
            seen_products = set()
            final_candidates = []
            
            for product, score, reason in sorted(candidates, key=lambda x: x[1], reverse=True):
                if product.id not in seen_products:
                    final_candidates.append((product, score, reason))
                    seen_products.add(product.id)
                    
                    if len(final_candidates) >= limit:
                        break
            
            # If we don't have enough recommendations, add popular products
            if len(final_candidates) < limit:
                popular_products = self.get_popular_products(limit - len(final_candidates))
                for product in popular_products:
                    if product.id not in seen_products:
                        final_candidates.append((product, 0.1, "Popular choice"))
                        seen_products.add(product.id)
            
            # Save recommendations to database
            self.save_recommendations(user, final_candidates)
            
            return [product for product, score, reason in final_candidates[:limit]]
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {str(e)}")
            return self.get_popular_products(limit)
    
    def get_popular_products(self, limit=6):
        """Get popular products based on likes, favorites, and purchases"""
        try:
            return Product.objects.filter(is_active=True).annotate(
                like_count=Count('likes'),
                favorite_count=Count('favorites'),
                purchase_count=Count('orderitem')
            ).order_by('-like_count', '-favorite_count', '-purchase_count')[:limit]
        except Exception as e:
            logger.error(f"Error getting popular products: {str(e)}")
            return Product.objects.filter(is_active=True)[:limit]
    
    def save_recommendations(self, user, recommendations):
        """Save recommendations to database"""
        try:
            # Clear old recommendations
            ProductRecommendation.objects.filter(user=user).delete()
            
            # Save new recommendations
            for product, score, reason in recommendations:
                ProductRecommendation.objects.create(
                    user=user,
                    product=product,
                    score=score,
                    reason=reason
                )
        except Exception as e:
            logger.error(f"Error saving recommendations: {str(e)}")
    
    def update_user_segment(self, user):
        """Update user's customer segment based on behavior"""
        try:
            # Get user statistics
            orders = Order.objects.filter(
                user=user,
                status__in=['delivered', 'shipped']
            )
            
            total_spent = orders.aggregate(total=Sum('total_amount'))['total'] or 0
            order_count = orders.count()
            last_order = orders.order_by('-created_at').first()
            
            # Get favorite categories
            favorite_categories = ProductFavorite.objects.filter(
                user=user
            ).values_list('product__category__name', flat=True)
            
            category_counts = Counter(favorite_categories)
            top_categories = [cat for cat, count in category_counts.most_common(3)]
            
            # Calculate average order value
            avg_order_value = total_spent / order_count if order_count > 0 else 0
            
            # Determine segment
            if total_spent >= 5000000:  # 5M toman
                segment_type = 'vip'
            elif total_spent >= 2000000:  # 2M toman
                segment_type = 'high_value'
            elif order_count >= 5:
                segment_type = 'regular'
            elif 'قهوه' in top_categories or 'کاپوچینو' in top_categories:
                segment_type = 'coffee_enthusiast'
            elif 'دسر' in top_categories or 'کیک' in top_categories:
                segment_type = 'dessert_lover'
            elif order_count == 0:
                segment_type = 'new'
            else:
                segment_type = 'casual'
            
            # Update or create segment
            segment, created = CustomerSegment.objects.get_or_create(user=user)
            segment.segment_type = segment_type
            segment.total_spent = total_spent
            segment.order_count = order_count
            segment.last_order_date = last_order.created_at if last_order else None
            segment.favorite_categories = top_categories
            segment.average_order_value = avg_order_value
            segment.save()
            
            return segment
            
        except Exception as e:
            logger.error(f"Error updating user segment: {str(e)}")
            return None
    
    def get_trending_products(self, days=7):
        """Get trending products based on recent activity"""
        try:
            recent_date = timezone.now() - timedelta(days=days)
            
            trending_products = Product.objects.filter(
                is_active=True,
                likes__created_at__gte=recent_date
            ).annotate(
                recent_likes=Count('likes', filter=Q(likes__created_at__gte=recent_date)),
                recent_favorites=Count('favorites', filter=Q(favorites__created_at__gte=recent_date)),
                recent_purchases=Count('orderitem', filter=Q(orderitem__order__created_at__gte=recent_date))
            ).order_by('-recent_likes', '-recent_favorites', '-recent_purchases')[:10]
            
            return trending_products
            
        except Exception as e:
            logger.error(f"Error getting trending products: {str(e)}")
            return []
    
    def get_collaborative_recommendations(self, user, limit=6):
        """Get recommendations based on similar users"""
        try:
            # Find users with similar preferences
            user_preferences = self.analyze_user_behavior(user)
            user_categories = set(user_preferences.get('categories', {}).keys())
            
            # Find users who like similar categories
            similar_users = UserActivity.objects.filter(
                category_id__in=user_categories,
                action__in=['like', 'favorite', 'purchase']
            ).exclude(user=user).values('user').distinct()
            
            # Get products liked by similar users
            similar_user_ids = [item['user'] for item in similar_users]
            
            recommendations = Product.objects.filter(
                is_active=True,
                likes__user_id__in=similar_user_ids
            ).exclude(
                likes__user=user
            ).annotate(
                similar_user_likes=Count('likes', filter=Q(likes__user_id__in=similar_user_ids))
            ).order_by('-similar_user_likes')[:limit]
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error getting collaborative recommendations: {str(e)}")
            return []

# Initialize the AI engine
ai_engine = CoffeeShopAIEngine() 