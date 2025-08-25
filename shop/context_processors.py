from urllib.parse import urlsplit, urlunsplit, parse_qsl


def seo_context(request):
    """Provide canonical URL, hreflang, and robots index flags to templates.

    - canonical strips known tracking params and normalizes URL
    - noindex for search results and non-canonical variations
    - hreflang for fa-IR (primary). Prepared structure for future locales.
    """
    try:
        full_url = request.build_absolute_uri()
        parts = urlsplit(full_url)
        # Remove common tracking params
        allowed_query_params = []
        filtered_query = "&".join(
            f"{k}={v}" for k, v in parse_qsl(parts.query) if k in allowed_query_params
        )
        canonical = urlunsplit((parts.scheme, parts.netloc, parts.path, filtered_query, ""))

        path = request.path or ""
        # Heuristic: noindex for search results and paginated duplicates unless canonicalized
        is_search = path.endswith('/search/') or 'search' in path
        is_noindex = is_search

        hreflangs = [
            {"hreflang": "fa-IR", "href": canonical},
        ]

        return {
            'canonical_url': canonical,
            'seo_noindex': is_noindex,
            'seo_hreflangs': hreflangs,
        }
    except Exception:
        return {
            'canonical_url': request.build_absolute_uri() if hasattr(request, 'build_absolute_uri') else '',
            'seo_noindex': False,
            'seo_hreflangs': [{"hreflang": "fa-IR", "href": request.build_absolute_uri() if hasattr(request, 'build_absolute_uri') else ''}],
        }

