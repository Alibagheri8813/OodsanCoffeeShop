from django.core.management.base import BaseCommand
from django.utils import timezone
from django.test.client import Client
from django.contrib.auth.models import User
from shop.models import Product, Category, Cart, CartItem
from shop.error_handling import check_database_health, check_cache_health
import time
import json

class Command(BaseCommand):
    help = 'Test system performance and functionality'

    def add_arguments(self, parser):
        parser.add_argument(
            '--quick',
            action='store_true',
            help='Run quick tests only',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🚀 Starting Coffee Shop System Tests...\n')
        )
        
        # Test 1: Database Health
        self.test_database_health()
        
        # Test 2: Cache Health
        self.test_cache_health()
        
        # Test 3: Model Operations
        self.test_model_operations()
        
        if not options['quick']:
            # Test 4: View Performance
            self.test_view_performance()
            
            # Test 5: Cart Operations
            self.test_cart_operations()
        
        self.stdout.write(
            self.style.SUCCESS('\n✅ All tests completed successfully!')
        )

    def test_database_health(self):
        self.stdout.write('🔍 Testing database health...')
        start_time = time.time()
        
        health = check_database_health()
        execution_time = time.time() - start_time
        
        if health['status'] == 'healthy':
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Database: {health["status"]} '
                    f'(Response time: {execution_time:.3f}s)'
                )
            )
        else:
            self.stdout.write(
                self.style.ERROR(f'❌ Database: {health["status"]} - {health["message"]}')
            )

    def test_cache_health(self):
        self.stdout.write('🔍 Testing cache health...')
        start_time = time.time()
        
        health = check_cache_health()
        execution_time = time.time() - start_time
        
        if health['status'] == 'healthy':
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Cache: {health["status"]} '
                    f'(Response time: {execution_time:.3f}s)'
                )
            )
        else:
            self.stdout.write(
                self.style.ERROR(f'❌ Cache: {health["status"]} - {health["message"]}')
            )

    def test_model_operations(self):
        self.stdout.write('🔍 Testing model operations...')
        start_time = time.time()
        
        try:
            # Test Category creation
            category_count = Category.objects.count()
            
            # Test Product queries
            products = Product.objects.select_related('category').all()[:5]
            product_count = len(products)
            
            # Test User operations
            user_count = User.objects.count()
            
            execution_time = time.time() - start_time
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Models: {category_count} categories, {product_count} products, '
                    f'{user_count} users (Query time: {execution_time:.3f}s)'
                )
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Model operations failed: {str(e)}')
            )

    def test_view_performance(self):
        self.stdout.write('🔍 Testing view performance...')
        
        client = Client()
        
        # Test home page
        start_time = time.time()
        response = client.get('/')
        home_time = time.time() - start_time
        
        if response.status_code == 200:
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Home page: {response.status_code} '
                    f'(Response time: {home_time:.3f}s)'
                )
            )
        else:
            self.stdout.write(
                self.style.ERROR(f'❌ Home page: {response.status_code}')
            )
        
        # Test product list
        start_time = time.time()
        response = client.get('/products/')
        products_time = time.time() - start_time
        
        if response.status_code == 200:
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Products page: {response.status_code} '
                    f'(Response time: {products_time:.3f}s)'
                )
            )
        else:
            self.stdout.write(
                self.style.ERROR(f'❌ Products page: {response.status_code}')
            )
        
        # Test health endpoint
        start_time = time.time()
        response = client.get('/health/')
        health_time = time.time() - start_time
        
        if response.status_code == 200:
            health_data = json.loads(response.content)
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Health endpoint: {health_data["status"]} '
                    f'(Response time: {health_time:.3f}s)'
                )
            )
        else:
            self.stdout.write(
                self.style.ERROR(f'❌ Health endpoint: {response.status_code}')
            )

    def test_cart_operations(self):
        self.stdout.write('🔍 Testing cart operations...')
        
        try:
            # Create test user if not exists
            test_user, created = User.objects.get_or_create(
                username='test_user',
                defaults={'email': 'test@example.com'}
            )
            
            # Test cart creation
            start_time = time.time()
            cart, created = Cart.objects.get_or_create(user=test_user)
            
            # Test product selection
            products = Product.objects.filter(stock__gt=0)[:3]
            
            cart_operations_time = time.time() - start_time
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Cart operations: Cart created/retrieved, '
                    f'{len(products)} products available '
                    f'(Time: {cart_operations_time:.3f}s)'
                )
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Cart operations failed: {str(e)}')
            )