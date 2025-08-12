from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.utils.text import slugify
from django.conf import settings

from pathlib import Path
import os
import sys
import requests
from typing import List, Optional, Dict

from shop.models import Product


def normalize_text(text: str) -> str:
    if not text:
        return ""
    return "".join(text.split()).lower()


def overlap_score(name_a: str, name_b: str) -> int:
    tokens_a = set(name_a.split())
    tokens_b = set(name_b.split())
    return len(tokens_a & tokens_b)


def pick_best_curated_url(
    product_name: str,
    curated_map: Dict[str, List[str]],
    fallback_groups: Dict[str, List[str]],
    category_name: Optional[str] = None,
) -> Optional[str]:
    # 1) Exact match
    if product_name in curated_map and curated_map[product_name]:
        return curated_map[product_name][0]

    # 2) Best token overlap with any key
    best_key = None
    best_score = 0
    for key in curated_map.keys():
        score = overlap_score(product_name, key)
        if score > best_score and curated_map[key]:
            best_key = key
            best_score = score
    if best_key:
        return curated_map[best_key][0]

    # 3) Category-based generic pool
    if category_name:
        category_name = category_name.strip()
        if "سیروپ" in category_name and fallback_groups.get("syrup_bottles"):
            return fallback_groups["syrup_bottles"][0]
        if "پودریجات" in category_name and fallback_groups.get("instant_beverages"):
            return fallback_groups["instant_beverages"][0]
        # Coffee-related categories
        if any(tag in category_name for tag in ["قهوه", "بلند", "گلد"]) and fallback_groups.get("coffee_packages"):
            return fallback_groups["coffee_packages"][0]

    # 4) Last resort generic pool
    for group in ("coffee_packages", "instant_beverages", "syrup_bottles"):
        if fallback_groups.get(group):
            return fallback_groups[group][0]

    return None


def search_images_bing(query: str, api_key: str, count: int = 5) -> List[str]:
    try:
        endpoint = "https://api.bing.microsoft.com/v7.0/images/search"
        headers = {"Ocp-Apim-Subscription-Key": api_key}
        params = {
            "q": query,
            "count": count,
            "imageType": "Photo",
            "size": "Medium",
            "aspect": "Square",
            "color": "ColorOnly",
            "safeSearch": "Strict",
        }
        response = requests.get(endpoint, headers=headers, params=params, timeout=20)
        response.raise_for_status()
        data = response.json()
        return [img.get("contentUrl") for img in data.get("value", []) if img.get("contentUrl")]
    except Exception:
        return []


def search_images_serpapi(query: str, api_key: str, count: int = 5) -> List[str]:
    try:
        url = "https://serpapi.com/search"
        params = {
            "engine": "google_images",
            "q": query,
            "api_key": api_key,
            "num": count,
            "safe": "active",
            "ijn": "0",
        }
        response = requests.get(url, params=params, timeout=20)
        response.raise_for_status()
        data = response.json()
        urls: List[str] = []
        for img in data.get("images_results", [])[:count]:
            candidate = img.get("original") or img.get("link")
            if candidate:
                urls.append(candidate)
        return urls
    except Exception:
        return []


def download_image_to_content(url: str) -> Optional[ContentFile]:
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
            "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
        }
        resp = requests.get(url, headers=headers, timeout=30, stream=True)
        resp.raise_for_status()
        content_type = resp.headers.get("content-type", "").lower()
        if not any(t in content_type for t in ["image/", "jpeg", "jpg", "png", "gif", "webp"]):
            return None
        data = resp.content
        if not data or len(data) < 1024:
            return None
        return ContentFile(data)
    except Exception:
        return None


class Command(BaseCommand):
    help = "Find and assign images to products based on Persian titles. Uses curated Unsplash URLs first, then optional Bing/SerpApi."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=None, help="Limit number of products to process")
        parser.add_argument("--overwrite", action="store_true", help="Overwrite existing product images")
        parser.add_argument(
            "--source",
            choices=["auto", "curated", "bing", "serpapi"],
            default="auto",
            help="Image source preference",
        )
        parser.add_argument("--dry-run", action="store_true", help="Do not save images, just show actions")

    def handle(self, *args, **options):
        # Ensure project root is importable so we can import curated URLs
        project_root = str(Path(settings.BASE_DIR))
        if project_root not in sys.path:
            sys.path.insert(0, project_root)

        curated_map: Dict[str, List[str]] = {}
        fallback_groups: Dict[str, List[str]] = {}
        try:
            import image_links_finder as ilf  # type: ignore

            curated_map = getattr(ilf, "high_quality_image_urls", {}) or {}
            fallback_groups = getattr(ilf, "additional_stock_urls", {}) or {}
        except Exception:
            curated_map = {}
            fallback_groups = {}

        limit = options["limit"]
        overwrite = options["overwrite"]
        preferred_source = options["source"]
        dry_run = options["dry_run"]

        bing_key = os.getenv("BING_SEARCH_API_KEY")
        serpapi_key = os.getenv("SERPAPI_KEY")

        queryset = Product.objects.all().order_by("-created_at")
        if not overwrite:
            from django.db.models import Q
            queryset = queryset.filter(Q(image__isnull=True) | Q(image=""))

        if limit:
            queryset = queryset[:limit]

        total = queryset.count()
        if total == 0:
            self.stdout.write(self.style.WARNING("No products to process."))
            return

        self.stdout.write(f"Processing {total} products...")

        assigned = 0
        skipped = 0
        failed = 0

        for product in queryset:
            product_name = product.name.strip()
            category_name = product.category.name if product.category_id else ""

            self.stdout.write("")
            self.stdout.write(f"→ {product_name} (#{product.id})")

            if product.image and not overwrite:
                self.stdout.write("  • Image exists, skipping (use --overwrite to replace)")
                skipped += 1
                continue

            chosen_url: Optional[str] = None

            # Source selection
            if preferred_source in ("auto", "curated"):
                chosen_url = pick_best_curated_url(product_name, curated_map, fallback_groups, category_name)

            if preferred_source in ("auto", "bing") and not chosen_url and bing_key:
                query = f"{product_name} بسته بندی محصول قهوه coffee product package"
                urls = search_images_bing(query, bing_key, count=5)
                chosen_url = urls[0] if urls else None

            if preferred_source in ("auto", "serpapi") and not chosen_url and serpapi_key:
                query = f"{product_name} بسته بندی محصول coffee product package"
                urls = search_images_serpapi(query, serpapi_key, count=5)
                chosen_url = urls[0] if urls else None

            if not chosen_url:
                self.stdout.write(self.style.WARNING("  • No candidate image URL found"))
                failed += 1
                continue

            self.stdout.write(f"  • Candidate URL: {chosen_url}")

            if dry_run:
                assigned += 1
                continue

            content = download_image_to_content(chosen_url)
            if not content:
                self.stdout.write(self.style.WARNING("  • Download failed or not an image"))
                failed += 1
                continue

            # Derive filename
            base = slugify(product_name, allow_unicode=True) or f"product-{product.id}"
            filename = f"{base}-{product.id}.jpg"

            # Save to ImageField
            try:
                product.image.save(filename, content, save=True)
                assigned += 1
                self.stdout.write(self.style.SUCCESS("  ✓ Image assigned"))
            except Exception as e:
                failed += 1
                self.stdout.write(self.style.ERROR(f"  ✗ Failed to assign image: {e}"))

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(f"Done. Assigned: {assigned}, Skipped: {skipped}, Failed: {failed}"))