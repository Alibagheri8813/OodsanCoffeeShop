from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import Product, Category

class ProductSitemap(Sitemap):
    changefreq = 'daily'
    priority = 0.8

    def items(self):
        return Product.objects.filter(stock__gt=0).only('id', 'slug', 'updated_at')

    def lastmod(self, obj: Product):
        return obj.updated_at

    def location(self, obj: Product):
        try:
            return obj.get_absolute_url()
        except Exception:
            return reverse('product_detail', args=[obj.id])

class CategorySitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.5

    def items(self):
        return Category.objects.only('id', 'slug')

    def location(self, obj: Category):
        try:
            return obj.get_absolute_url()
        except Exception:
            return reverse('category_detail', args=[obj.id])