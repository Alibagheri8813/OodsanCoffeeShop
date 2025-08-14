from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.http import JsonResponse
from django.core.exceptions import ObjectDoesNotExist
from decimal import Decimal
import json
from unittest.mock import patch, MagicMock

from .models import Product, Category, Cart, CartItem, UserProfile


class CartViewTestCase(TestCase):
    """Test cases for cart view functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create user profile
        self.profile = UserProfile.objects.create(
            user=self.user,
            phone_number='09123456789'
        )
        # Create an address to mark profile as complete under new rules
        from .models import UserAddress
        UserAddress.objects.create(
            user=self.user,
            title='Home',
            full_address='Test Address 123',
            city='Tehran',
            state='Tehran',
            is_default=True
        )
        
        # Create test category
        self.category = Category.objects.create(
            name='Coffee',
            description='Coffee products'
        )
        
        # Create test products
        self.product1 = Product.objects.create(
            name='Espresso',
            description='Strong coffee',
            price=Decimal('50000'),
            stock=10,
            category=self.category
        )
        
        self.product2 = Product.objects.create(
            name='Latte',
            description='Milk coffee',
            price=Decimal('75000'),
            stock=5,
            category=self.category
        )
        
        # Create cart and cart items
        self.cart = Cart.objects.create(user=self.user)
        self.cart_item1 = CartItem.objects.create(
            cart=self.cart,
            product=self.product1,
            quantity=2
        )
        self.cart_item2 = CartItem.objects.create(
            cart=self.cart,
            product=self.product2,
            quantity=1
        )
        # Ensure welcome credit is awarded after address creation
        self.profile.refresh_from_db()
        self.profile.ensure_intro_margin_awarded()
    
    def test_cart_view_authenticated(self):
        """Test cart view for authenticated user"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('cart_view'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'سبد خرید')
        self.assertContains(response, 'Espresso')
        self.assertContains(response, 'Latte')
        self.assertContains(response, '50000')  # Product price
        self.assertContains(response, '75000')  # Product price
        
        # Check context data
        self.assertEqual(len(response.context['cart_items']), 2)
        self.assertEqual(response.context['subtotal'], Decimal('175000'))  # 2*50000 + 1*75000
        self.assertFalse(response.context['is_cart_empty'])
        self.assertTrue(response.context['has_complete_address'])
    
    def test_cart_view_unauthenticated(self):
        """Test cart view redirects unauthenticated users"""
        response = self.client.get(reverse('cart_view'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_cart_view_empty_cart(self):
        """Test cart view with empty cart"""
        # Clear cart items
        CartItem.objects.filter(cart=self.cart).delete()
        
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('cart_view'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'سبد خرید شما خالی است')
        self.assertTrue(response.context['is_cart_empty'])
        self.assertEqual(response.context['subtotal'], Decimal('0'))


class CartAPITestCase(TestCase):
    """Test cases for cart API endpoints"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create test category
        self.category = Category.objects.create(
            name='Coffee',
            description='Coffee products'
        )
        
        # Create test product
        self.product = Product.objects.create(
            name='Espresso',
            description='Strong coffee',
            price=Decimal('50000'),
            stock=10,
            category=self.category
        )
        
        # Create cart and cart item
        self.cart = Cart.objects.create(user=self.user)
        self.cart_item = CartItem.objects.create(
            cart=self.cart,
            product=self.product,
            quantity=2
        )
    
    def test_update_cart_item_success(self):
        """Test successful cart item update"""
        self.client.login(username='testuser', password='testpass123')
        
        data = {
            'item_id': self.cart_item.id,
            'quantity': 3
        }
        
        response = self.client.post(
            reverse('update_cart_item'),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        
        self.assertTrue(response_data['success'])
        self.assertEqual(response_data['cart_total'], 150000)  # 3 * 50000
        self.assertEqual(response_data['cart_count'], 3)
        
        # Verify database update
        self.cart_item.refresh_from_db()
        self.assertEqual(self.cart_item.quantity, 3)
    
    def test_update_cart_item_invalid_quantity(self):
        """Test cart item update with invalid quantity"""
        self.client.login(username='testuser', password='testpass123')
        
        data = {
            'item_id': self.cart_item.id,
            'quantity': 15  # Exceeds stock (10)
        }
        
        response = self.client.post(
            reverse('update_cart_item'),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        
        self.assertFalse(response_data['success'])
        self.assertIn('موجودی کافی نیست', response_data['message'])
        self.assertEqual(response_data['available_stock'], 10)
    
    def test_update_cart_item_zero_quantity(self):
        """Test cart item update with zero quantity (should remove item)"""
        self.client.login(username='testuser', password='testpass123')
        
        data = {
            'item_id': self.cart_item.id,
            'quantity': 0
        }
        
        response = self.client.post(
            reverse('update_cart_item'),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        
        self.assertTrue(response_data['success'])
        self.assertEqual(response_data['cart_total'], 0)
        self.assertEqual(response_data['cart_count'], 0)
        
        # Verify item was deleted
        with self.assertRaises(ObjectDoesNotExist):
            self.cart_item.refresh_from_db()
    
    def test_update_cart_item_unauthorized(self):
        """Test cart item update without authentication"""
        data = {
            'item_id': self.cart_item.id,
            'quantity': 3
        }
        
        response = self.client.post(
            reverse('update_cart_item'),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_update_cart_item_invalid_method(self):
        """Test cart item update with invalid HTTP method"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(reverse('update_cart_item'))
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        
        self.assertFalse(response_data['success'])
        self.assertEqual(response_data['message'], 'درخواست نامعتبر')
    
    def test_remove_from_cart_success(self):
        """Test successful item removal from cart"""
        self.client.login(username='testuser', password='testpass123')
        
        data = {
            'item_id': self.cart_item.id
        }
        
        response = self.client.post(
            reverse('remove_from_cart'),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        
        self.assertTrue(response_data['success'])
        self.assertIn('حذف شد', response_data['message'])
        self.assertEqual(response_data['cart_total'], 0)
        self.assertEqual(response_data['cart_count'], 0)
        
        # Verify item was deleted
        with self.assertRaises(ObjectDoesNotExist):
            self.cart_item.refresh_from_db()
        
        # Verify stock was restored
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 12)  # 10 + 2 (restored)
    
    def test_remove_from_cart_nonexistent_item(self):
        """Test removing non-existent item from cart"""
        self.client.login(username='testuser', password='testpass123')
        
        data = {
            'item_id': 99999  # Non-existent ID
        }
        
        response = self.client.post(
            reverse('remove_from_cart'),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 404)
    
    def test_cart_count_endpoint(self):
        """Test cart count endpoint"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(reverse('cart_count'))
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        
        self.assertEqual(response_data['count'], 2)  # Current cart item quantity
    
    def test_cart_count_no_cart(self):
        """Test cart count endpoint when user has no cart"""
        # Create new user without cart
        new_user = User.objects.create_user(
            username='newuser',
            email='new@example.com',
            password='newpass123'
        )
        
        self.client.login(username='newuser', password='newpass123')
        
        response = self.client.get(reverse('cart_count'))
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        
        self.assertEqual(response_data['count'], 0)


class CartModelTestCase(TestCase):
    """Test cases for cart models"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.category = Category.objects.create(
            name='Coffee',
            description='Coffee products'
        )
        
        self.product1 = Product.objects.create(
            name='Espresso',
            description='Strong coffee',
            price=Decimal('50000'),
            stock=10,
            category=self.category
        )
        
        self.product2 = Product.objects.create(
            name='Latte',
            description='Milk coffee',
            price=Decimal('75000'),
            stock=5,
            category=self.category
        )
        
        self.cart = Cart.objects.create(user=self.user)
    
    def test_cart_creation(self):
        """Test cart creation"""
        self.assertEqual(self.cart.user, self.user)
        self.assertIsNotNone(self.cart.created_at)
        self.assertIsNotNone(self.cart.updated_at)
    
    def test_cart_item_creation(self):
        """Test cart item creation"""
        cart_item = CartItem.objects.create(
            cart=self.cart,
            product=self.product1,
            quantity=2
        )
        
        self.assertEqual(cart_item.cart, self.cart)
        self.assertEqual(cart_item.product, self.product1)
        self.assertEqual(cart_item.quantity, 2)
        self.assertEqual(cart_item.get_total_price(), Decimal('100000'))  # 2 * 50000
    
    def test_cart_total_price(self):
        """Test cart total price calculation"""
        CartItem.objects.create(
            cart=self.cart,
            product=self.product1,
            quantity=2
        )
        CartItem.objects.create(
            cart=self.cart,
            product=self.product2,
            quantity=1
        )
        
        total = self.cart.get_total_price()
        expected_total = Decimal('175000')  # 2*50000 + 1*75000
        
        self.assertEqual(total, expected_total)
    
    def test_cart_total_quantity(self):
        """Test cart total quantity calculation"""
        CartItem.objects.create(
            cart=self.cart,
            product=self.product1,
            quantity=2
        )
        CartItem.objects.create(
            cart=self.cart,
            product=self.product2,
            quantity=3
        )
        
        total_quantity = self.cart.get_total_quantity()
        
        self.assertEqual(total_quantity, 5)  # 2 + 3
    
    def test_cart_empty_totals(self):
        """Test cart totals when empty"""
        self.assertEqual(self.cart.get_total_price(), Decimal('0'))
        self.assertEqual(self.cart.get_total_quantity(), 0)


class CartIntegrationTestCase(TestCase):
    """Integration tests for cart functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.category = Category.objects.create(
            name='Coffee',
            description='Coffee products'
        )
        
        self.product = Product.objects.create(
            name='Espresso',
            description='Strong coffee',
            price=Decimal('50000'),
            stock=10,
            category=self.category
        )
    
    def test_full_cart_workflow(self):
        """Test complete cart workflow: add -> update -> remove"""
        self.client.login(username='testuser', password='testpass123')
        
        # Step 1: Add to cart
        add_data = {
            'product_id': self.product.id,
            'quantity': 2
        }
        
        response = self.client.post(
            reverse('add_to_cart'),
            data=json.dumps(add_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        add_response = json.loads(response.content)
        self.assertTrue(add_response['success'])
        
        # Verify cart item was created
        cart = Cart.objects.get(user=self.user)
        cart_item = CartItem.objects.get(cart=cart, product=self.product)
        self.assertEqual(cart_item.quantity, 2)
        
        # Step 2: Update quantity
        update_data = {
            'item_id': cart_item.id,
            'quantity': 3
        }
        
        response = self.client.post(
            reverse('update_cart_item'),
            data=json.dumps(update_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        update_response = json.loads(response.content)
        self.assertTrue(update_response['success'])
        
        # Verify quantity was updated
        cart_item.refresh_from_db()
        self.assertEqual(cart_item.quantity, 3)
        
        # Step 3: Remove from cart
        remove_data = {
            'item_id': cart_item.id
        }
        
        response = self.client.post(
            reverse('remove_from_cart'),
            data=json.dumps(remove_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        remove_response = json.loads(response.content)
        self.assertTrue(remove_response['success'])
        
        # Verify item was removed
        self.assertFalse(CartItem.objects.filter(id=cart_item.id).exists())
        
        # Verify stock was restored
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 10)  # Back to original
    
    def test_cart_view_with_delivery_fee(self):
        """Test cart view calculation with delivery fee"""
        self.client.login(username='testuser', password='testpass123')
        
        # Create cart with low total (should have delivery fee)
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(
            cart=cart,
            product=self.product,
            quantity=1  # 50000 total, less than 500000 threshold
        )
        
        response = self.client.get(reverse('cart_view'))
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['subtotal'], Decimal('50000'))
        self.assertEqual(response.context['delivery_fee'], 50000)  # Should have delivery fee
        self.assertEqual(response.context['total'], Decimal('100000'))  # 50000 + 50000
    
    def test_cart_view_no_delivery_fee(self):
        """Test cart view calculation without delivery fee"""
        self.client.login(username='testuser', password='testpass123')
        
        # Create expensive product for high cart total
        expensive_product = Product.objects.create(
            name='Premium Coffee',
            description='Expensive coffee',
            price=Decimal('600000'),
            stock=5,
            category=self.category
        )
        
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(
            cart=cart,
            product=expensive_product,
            quantity=1  # 600000 total, more than 500000 threshold
        )
        
        response = self.client.get(reverse('cart_view'))
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['subtotal'], Decimal('600000'))
        self.assertEqual(response.context['delivery_fee'], 50000)  # Shipping is fixed
        self.assertEqual(response.context['total'], Decimal('650000'))  # 600000 + 50000 fixed shipping


class CartErrorHandlingTestCase(TestCase):
    """Test error handling in cart functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.category = Category.objects.create(
            name='Coffee',
            description='Coffee products'
        )
        
        self.product = Product.objects.create(
            name='Espresso',
            description='Strong coffee',
            price=Decimal('50000'),
            stock=2,  # Low stock for testing
            category=self.category
        )
        
        self.cart = Cart.objects.create(user=self.user)
        self.cart_item = CartItem.objects.create(
            cart=self.cart,
            product=self.product,
            quantity=1
        )
    
    def test_update_cart_item_malformed_json(self):
        """Test cart update with malformed JSON"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.post(
            reverse('update_cart_item'),
            data='invalid json',
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        
        self.assertFalse(response_data['success'])
        self.assertIn('خطا در به‌روزرسانی سبد خرید', response_data['message'])
    
    def test_update_cart_item_missing_fields(self):
        """Test cart update with missing required fields"""
        self.client.login(username='testuser', password='testpass123')
        
        data = {
            'quantity': 2  # Missing item_id
        }
        
        response = self.client.post(
            reverse('update_cart_item'),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        
        self.assertFalse(response_data['success'])
        self.assertIn('خطا در به‌روزرسانی سبد خرید', response_data['message'])
    
    def test_cross_user_cart_access(self):
        """Test that users cannot access other users' cart items"""
        # Create another user and cart item
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='otherpass123'
        )
        
        other_cart = Cart.objects.create(user=other_user)
        other_cart_item = CartItem.objects.create(
            cart=other_cart,
            product=self.product,
            quantity=1
        )
        
        # Login as first user and try to update other user's cart item
        self.client.login(username='testuser', password='testpass123')
        
        data = {
            'item_id': other_cart_item.id,
            'quantity': 5
        }
        
        response = self.client.post(
            reverse('update_cart_item'),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 404)  # Should not find item


if __name__ == '__main__':
    import unittest
    unittest.main()
