from django.conf import settings


class SecurityHeadersMiddleware:
	"""Add strong security headers, including CSP, for production.
	Adjusts headers conservatively to avoid breaking existing inline styles/JSON-LD.
	"""
	def __init__(self, get_response):
		self.get_response = get_response

	def __call__(self, request):
		response = self.get_response(request)

		# Content Security Policy
		# Allow self and required CDNs used in templates; permit inline styles and JSON-LD.
		csp_directives = {
			"default-src": "'self'",
			"base-uri": "'self'",
			"frame-ancestors": "'none'",
			"img-src": "'self' data: blob:",
			"font-src": "'self' https://fonts.gstatic.com data:",
			"style-src": "'self' 'unsafe-inline' https://fonts.googleapis.com https://cdnjs.cloudflare.com",
			"script-src": "'self' 'unsafe-inline' https://cdnjs.cloudflare.com",
			"connect-src": "'self'",
		}
		csp = "; ".join(f"{k} {v}" for k, v in csp_directives.items())
		response.headers.setdefault("Content-Security-Policy", csp)

		# Additional security headers
		response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
		response.headers.setdefault("Permissions-Policy", "geolocation=(), microphone=(), camera=()")
		response.headers.setdefault("Cross-Origin-Opener-Policy", "same-origin")
		response.headers.setdefault("Cross-Origin-Resource-Policy", "same-origin")
		# X-Content-Type-Options and X-Frame-Options are already handled via settings/SecurityMiddleware,
		# but we set nosniff explicitly for safety.
		response.headers.setdefault("X-Content-Type-Options", "nosniff")

		# HSTS is handled by SecurityMiddleware when not DEBUG, so we do not duplicate here.

		return response