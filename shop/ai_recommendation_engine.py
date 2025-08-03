"""
AI-Powered Recommendation Engine for Coffee Shop
Features: TF-IDF Vectorization, Cosine Similarity, User Behavior Analysis, Collaborative Filtering
"""

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from django.db.models import Count, Avg, Sum, F, Q
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.cache import cache
from datetime import datetime, timedelta
import logging
import json
from collections import defaultdict

from .models import (
    Product, Category, Order, OrderItem, UserActivity, 
    ProductRecommendation, CustomerSegment, ProductInteraction
)

logger = logging.getLogger(__name__)

class AIRecommendationEngine:
    """Advanced AI recommendation engine with multiple algorithms"""
    
    def __init__(self):
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words=None,  # Persian text
            ngram_range=(1, 2),
            max_df=0.85,
            min_df=2
        )
        self.product_similarity_matrix = None
        self.products_df = None
        self.user_item_matrix = None
        
    def build_product_similarity_matrix(self):
        """Build TF-IDF based product similarity matrix"""
        try:
            # Get all active products
            products = Product.objects.filter(stock__gt=0).select_related('category')
            
            if not products.exists():
                logger.warning("No products found for similarity matrix")
                return
            
            # Create product features text
            product_features = []
            product_ids = []
            
            for product in products:
                features = f"{product.name} {product.description} {product.category.name} {product.category.description}"
                product_features.append(features)
                product_ids.append(product.id)
            
            # Build TF-IDF matrix
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(product_features)
            
            # Calculate cosine similarity
            self.product_similarity_matrix = cosine_similarity(tfidf_matrix)
            
            # Create products DataFrame
            self.products_df = pd.DataFrame({
                'product_id': product_ids,
                'name': [p.name for p in products],
                'category_id': [p.category.id for p in products],
                'price': [float(p.price) for p in products],
                'stock': [p.stock for p in products]
            })
            
            # Cache the similarity matrix
            cache.set('product_similarity_matrix', self.product_similarity_matrix, timeout=3600)
            cache.set('products_df', self.products_df.to_dict(), timeout=3600)
            
            logger.info(f"Built similarity matrix for {len(product_ids)} products")
            
        except Exception as e:
            logger.error(f"Error building similarity matrix: {e}")
    
    def get_product_similarities(self, product_id, limit=6):
        """Get similar products based on TF-IDF cosine similarity"""
        try:
            if self.product_similarity_matrix is None:
                # Try to load from cache
                cached_matrix = cache.get('product_similarity_matrix')
                cached_df = cache.get('products_df')
                
                if cached_matrix is not None and cached_df is not None:
                    self.product_similarity_matrix = cached_matrix
                    self.products_df = pd.DataFrame(cached_df)
                else:
                    self.build_product_similarity_matrix()
            
            if self.products_df is None or self.product_similarity_matrix is None:
                return []
            
            # Find product index
            try:
                product_idx = self.products_df[self.products_df['product_id'] == product_id].index[0]
            except IndexError:
                logger.warning(f"Product {product_id} not found in similarity matrix")
                return []
            
            # Get similarity scores
            similarity_scores = list(enumerate(self.product_similarity_matrix[product_idx]))
            
            # Sort by similarity score
            similarity_scores = sorted(similarity_scores, key=lambda x: x[1], reverse=True)
            
            # Get top similar products (excluding the product itself)
            similar_products = []
            for idx, score in similarity_scores[1:limit+1]:  # Skip first (itself)
                if score > 0.1:  # Minimum similarity threshold
                    product_id_similar = self.products_df.iloc[idx]['product_id']
                    similar_products.append({
                        'product_id': product_id_similar,
                        'similarity_score': score,
                        'reason': 'محصولات مشابه بر اساس ویژگی‌ها'
                    })
            
            return similar_products
            
        except Exception as e:
            logger.error(f"Error getting product similarities: {e}")
            return []
    
    def analyze_user_behavior(self, user):
        """Analyze user behavior patterns for personalized recommendations"""
        try:
            # Get user activities
            activities = UserActivity.objects.filter(
                user=user,
                timestamp__gte=timezone.now() - timedelta(days=90)
            ).select_related('product', 'category')
            
            # Get purchase history
            orders = Order.objects.filter(
                user=user,
                status__in=['paid', 'processing', 'shipped', 'delivered']
            ).prefetch_related('items__product__category')
            
            # Analyze category preferences
            category_scores = defaultdict(float)
            
            # Weight activities
            activity_weights = {
                'view': 1.0,
                'like': 2.0,
                'favorite': 3.0,
                'add_to_cart': 4.0,
                'purchase': 5.0
            }
            
            for activity in activities:
                if activity.category:
                    weight = activity_weights.get(activity.action, 1.0)
                    category_scores[activity.category.id] += weight
            
            # Weight purchases more heavily
            for order in orders:
                for item in order.items.all():
                    category_scores[item.product.category.id] += 10.0 * item.quantity
            
            # Calculate price range preference
            purchase_prices = []
            for order in orders:
                for item in order.items.all():
                    purchase_prices.extend([float(item.price)] * item.quantity)
            
            price_preference = {
                'min': min(purchase_prices) if purchase_prices else 0,
                'max': max(purchase_prices) if purchase_prices else 1000000,
                'avg': sum(purchase_prices) / len(purchase_prices) if purchase_prices else 100000
            }
            
            return {
                'category_preferences': dict(category_scores),
                'price_preference': price_preference,
                'total_activities': activities.count(),
                'total_orders': orders.count()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing user behavior: {e}")
            return {}
    
    def get_collaborative_recommendations(self, user, limit=6):
        """Get recommendations based on similar users' preferences"""
        try:
            # Find users with similar purchase patterns
            user_orders = Order.objects.filter(
                user=user,
                status__in=['paid', 'processing', 'shipped', 'delivered']
            ).values_list('items__product__id', flat=True)
            
            if not user_orders:
                return []
            
            user_products = set(user_orders)
            
            # Find similar users
            similar_users = []
            all_users = User.objects.filter(
                orders__status__in=['paid', 'processing', 'shipped', 'delivered']
            ).distinct()
            
            for other_user in all_users[:100]:  # Limit for performance
                if other_user == user:
                    continue
                    
                other_orders = Order.objects.filter(
                    user=other_user,
                    status__in=['paid', 'processing', 'shipped', 'delivered']
                ).values_list('items__product__id', flat=True)
                
                other_products = set(other_orders)
                
                if other_products:
                    # Calculate Jaccard similarity
                    intersection = len(user_products.intersection(other_products))
                    union = len(user_products.union(other_products))
                    
                    if union > 0:
                        similarity = intersection / union
                        if similarity > 0.1:  # Minimum similarity threshold
                            similar_users.append((other_user, similarity))
            
            # Sort by similarity
            similar_users.sort(key=lambda x: x[1], reverse=True)
            
            # Get recommendations from similar users
            recommended_products = defaultdict(float)
            
            for similar_user, similarity_score in similar_users[:10]:  # Top 10 similar users
                similar_user_products = Order.objects.filter(
                    user=similar_user,
                    status__in=['paid', 'processing', 'shipped', 'delivered']
                ).values_list('items__product__id', flat=True)
                
                for product_id in similar_user_products:
                    if product_id not in user_products:  # Don't recommend already purchased
                        recommended_products[product_id] += similarity_score
            
            # Sort recommendations by score
            sorted_recommendations = sorted(
                recommended_products.items(),
                key=lambda x: x[1],
                reverse=True
            )
            
            # Get product details
            recommendations = []
            for product_id, score in sorted_recommendations[:limit]:
                try:
                    product = Product.objects.get(id=product_id, stock__gt=0)
                    recommendations.append({
                        'product_id': product_id,
                        'similarity_score': score,
                        'reason': 'مشتریان مشابه این محصول را خریده‌اند'
                    })
                except Product.DoesNotExist:
                    continue
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error getting collaborative recommendations: {e}")
            return []
    
    def get_trending_products(self, days=7, limit=6):
        """Get trending products based on recent activity"""
        try:
            since_date = timezone.now() - timedelta(days=days)
            
            # Get trending based on recent orders
            trending = Product.objects.filter(
                orderitem__order__created_at__gte=since_date,
                orderitem__order__status__in=['paid', 'processing', 'shipped', 'delivered'],
                stock__gt=0
            ).annotate(
                recent_sales=Sum('orderitem__quantity'),
                recent_revenue=Sum(F('orderitem__quantity') * F('orderitem__price'))
            ).filter(
                recent_sales__gt=0
            ).order_by('-recent_sales', '-recent_revenue')[:limit]
            
            recommendations = []
            for product in trending:
                recommendations.append({
                    'product_id': product.id,
                    'similarity_score': float(product.recent_sales) / 10.0,  # Normalize
                    'reason': f'محصول محبوب (در {days} روز گذشته)'
                })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error getting trending products: {e}")
            return []
    
    def generate_recommendations(self, user, limit=12):
        """Generate comprehensive recommendations using multiple algorithms"""
        try:
            recommendations = []
            
            # Get user behavior analysis
            user_behavior = self.analyze_user_behavior(user)
            
            # 1. Content-based recommendations (from user's purchase history)
            recent_purchases = Order.objects.filter(
                user=user,
                status__in=['paid', 'processing', 'shipped', 'delivered'],
                created_at__gte=timezone.now() - timedelta(days=60)
            ).values_list('items__product__id', flat=True)
            
            content_based = []
            for product_id in recent_purchases[:3]:  # Last 3 purchased products
                similar = self.get_product_similarities(product_id, limit=2)
                content_based.extend(similar)
            
            # 2. Collaborative filtering
            collaborative = self.get_collaborative_recommendations(user, limit=4)
            
            # 3. Trending products
            trending = self.get_trending_products(days=7, limit=3)
            
            # 4. Category-based recommendations
            category_based = []
            if user_behavior.get('category_preferences'):
                top_categories = sorted(
                    user_behavior['category_preferences'].items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:2]
                
                for category_id, score in top_categories:
                    products = Product.objects.filter(
                        category_id=category_id,
                        stock__gt=0
                    ).exclude(
                        id__in=recent_purchases
                    ).order_by('-featured', '?')[:2]
                    
                    for product in products:
                        category_based.append({
                            'product_id': product.id,
                            'similarity_score': score / 10.0,
                            'reason': 'بر اساس علاقه‌مندی‌های شما'
                        })
            
            # Combine all recommendations
            all_recommendations = content_based + collaborative + trending + category_based
            
            # Remove duplicates and filter by user preferences
            seen_products = set()
            final_recommendations = []
            
            for rec in all_recommendations:
                if rec['product_id'] not in seen_products:
                    try:
                        product = Product.objects.get(id=rec['product_id'], stock__gt=0)
                        
                        # Filter by price preference if available
                        if user_behavior.get('price_preference'):
                            price_pref = user_behavior['price_preference']
                            product_price = float(product.price)
                            
                            # Allow ±50% of average price preference
                            if price_pref['avg'] > 0:
                                price_range_min = price_pref['avg'] * 0.5
                                price_range_max = price_pref['avg'] * 1.5
                                
                                if not (price_range_min <= product_price <= price_range_max):
                                    continue
                        
                        seen_products.add(rec['product_id'])
                        final_recommendations.append(rec)
                        
                        if len(final_recommendations) >= limit:
                            break
                            
                    except Product.DoesNotExist:
                        continue
            
            # If not enough recommendations, add popular products
            if len(final_recommendations) < limit:
                popular_products = Product.objects.filter(
                    stock__gt=0,
                    featured=True
                ).exclude(
                    id__in=seen_products
                ).order_by('?')[:limit - len(final_recommendations)]
                
                for product in popular_products:
                    final_recommendations.append({
                        'product_id': product.id,
                        'similarity_score': 0.5,
                        'reason': 'محصولات محبوب'
                    })
            
            # Store recommendations in database
            self.store_recommendations(user, final_recommendations)
            
            return final_recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return self.get_fallback_recommendations(limit)
    
    def store_recommendations(self, user, recommendations):
        """Store recommendations in database for tracking"""
        try:
            # Clear old recommendations
            ProductRecommendation.objects.filter(
                user=user,
                created_at__lt=timezone.now() - timedelta(days=7)
            ).delete()
            
            # Store new recommendations
            for rec in recommendations:
                ProductRecommendation.objects.update_or_create(
                    user=user,
                    product_id=rec['product_id'],
                    defaults={
                        'score': rec['similarity_score'],
                        'reason': rec['reason'],
                        'recommendation_type': 'ai_generated'
                    }
                )
        except Exception as e:
            logger.error(f"Error storing recommendations: {e}")
    
    def get_fallback_recommendations(self, limit=12):
        """Fallback recommendations when AI fails"""
        try:
            products = Product.objects.filter(
                stock__gt=0
            ).order_by('-featured', '?')[:limit]
            
            return [{
                'product_id': product.id,
                'similarity_score': 0.3,
                'reason': 'پیشنهادات عمومی'
            } for product in products]
            
        except Exception as e:
            logger.error(f"Error getting fallback recommendations: {e}")
            return []
    
    def track_recommendation_interaction(self, user, product_id, interaction_type):
        """Track user interactions with recommendations"""
        try:
            # Update recommendation tracking
            ProductRecommendation.objects.filter(
                user=user,
                product_id=product_id
            ).update(
                is_viewed=True if interaction_type == 'view' else F('is_viewed'),
                is_purchased=True if interaction_type == 'purchase' else F('is_purchased')
            )
            
            # Store interaction
            ProductInteraction.objects.create(
                user=user,
                product_id=product_id,
                interaction_type=interaction_type
            )
            
        except Exception as e:
            logger.error(f"Error tracking recommendation interaction: {e}")
    
    def get_user_recommendation_stats(self, user):
        """Get user's recommendation interaction statistics"""
        try:
            recommendations = ProductRecommendation.objects.filter(user=user)
            
            total = recommendations.count()
            viewed = recommendations.filter(is_viewed=True).count()
            purchased = recommendations.filter(is_purchased=True).count()
            
            return {
                'total_recommendations': total,
                'viewed_count': viewed,
                'purchased_count': purchased,
                'view_rate': (viewed / total * 100) if total > 0 else 0,
                'conversion_rate': (purchased / viewed * 100) if viewed > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error getting recommendation stats: {e}")
            return {}

# Global AI engine instance
ai_engine = AIRecommendationEngine() 