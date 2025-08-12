from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.core.files import File
from decimal import Decimal
from pathlib import Path
import io

from shop.models import Category, Product


class Command(BaseCommand):
    help = "Reset and seed categories and products based on predefined catalog rules"

    def add_arguments(self, parser):
        parser.add_argument('--no-input', action='store_true', help='Run non-interactively')

    def handle(self, *args, **options):
        base_dir = Path(__file__).resolve().parents[3]
        media_dir = base_dir / 'media'
        local_cats_dir = base_dir / 'categories'
        media_dir.mkdir(parents=True, exist_ok=True)

        self.stdout.write(self.style.WARNING('Deleting existing products and categories...'))
        Product.objects.all().delete()
        Category.objects.all().delete()

        # Create categories
        category_names = [
            'قهوه تک دان',
            'قهوه گلد',
            'پودریجات',
            'قهوه های ترکیب شده(بلند)',
            'سیروپ ها',
        ]

        # Assign local images to categories if available
        local_cat_images = list(sorted(local_cats_dir.glob('coffee_*.jpg')))
        created_categories = {}
        for idx, name in enumerate(category_names):
            cat = Category.objects.create(name=name, description='')
            # Attach image from local pool if exists
            if local_cat_images:
                img_path = local_cat_images[idx % len(local_cat_images)]
                try:
                    with open(img_path, 'rb') as f:
                        cat.image.save(img_path.name, File(f), save=True)
                except Exception:
                    pass
            created_categories[name] = cat
            self.stdout.write(self.style.SUCCESS(f"Created category: {name}"))

        # Utility: configure per-category rules
        def set_product_options(product: Product, category_name: str):
            # Defaults
            default_grinds = ['whole_bean', 'coarse', 'medium_coarse', 'medium', 'medium_fine', 'fine']
            default_weights = ['250g', '500g', '1kg']

            if category_name == 'قهوه گلد':
                product.available_grinds = []
                product.available_weights = ['100g', '250g', '500g']
                product.weight_multipliers = {
                    '100g': 1.0,
                    '250g': 2.5,
                    '500g': 5.0,
                }
            elif category_name == 'پودریجات':
                product.available_grinds = []
                product.available_weights = ['250g', '500g']
                product.weight_multipliers = {
                    '250g': 1.0,
                    '500g': 2.0,
                }
            elif category_name == 'سیروپ ها':
                product.available_grinds = []
                product.available_weights = []
                product.weight_multipliers = {}
            else:
                # تک دان + بلند
                product.available_grinds = default_grinds
                product.available_weights = default_weights
                product.weight_multipliers = {}

        # Seed products per category
        def create_product(name: str, price_int: int, category_name: str, stock: int = 100, featured: bool = False, description: str = ''):
            product = Product(
                name=name,
                description=description or 'محصول ثبت شده به صورت خودکار',
                price=Decimal(price_int),
                category=created_categories[category_name],
                stock=stock,
                featured=featured,
            )
            set_product_options(product, category_name)
            product.save()
            self.stdout.write(self.style.SUCCESS(f"Added product: {name} ({category_name})"))

        # قهوه تک دان
        single_origin = [
            ('عربیکا کلمبیا', 385000),
            ('عربیکا اتیوپی', 299000),
            ('عربیکا کنیا', 357000),
            ('عربیکا برزیل', 282000),
            ('ربستا اندونزی', 385000),
            ('ربستا اوگاندا', 299000),
        ]
        for name, price in single_origin:
            create_product(name, price, 'قهوه تک دان')

        # قهوه گلد
        gold = [
            ('گلد اکوادور', 264000),
            ('گلد هند', 210000),
            ('گلد برزیل', 210000),
        ]
        for name, price in gold:
            create_product(name, price, 'قهوه گلد')

        # پودریجات
        powders = [
            ('کاپوچینو', 155000),
            ('هات چاکلت', 155000),
            ('ماسالا', 155000),
            ('کافی میت', 87000),
        ]
        for name, price in powders:
            create_product(name, price, 'پودریجات')

        # قهوه های ترکیب شده(بلند)
        blends = [
            ('فول کافئین', 287000),
            ('70*30 پایه ربستا', 299000),
            ('50*50', 327000),
            ('100 عربیکا', 390000),
        ]
        for name, price in blends:
            create_product(name, price, 'قهوه های ترکیب شده(بلند)')

        # سیروپ ها
        syrups = [
            'سیروپ کارامل',
            'سیروپ ایریش',
            'سیروپ نارگیل',
            'سیروپ سیب',
            'سیروپ بلوبری',
            'سیروپ لیمو',
            'سیروپ موهیتو',
            'سیروپ زعفران',
            'سیروپ آناناس',
        ]
        for name in syrups:
            create_product(name, 477000, 'سیروپ ها')

        self.stdout.write(self.style.SUCCESS('Catalog seeding complete.'))