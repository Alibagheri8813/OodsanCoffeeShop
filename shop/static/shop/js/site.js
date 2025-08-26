// Loading Screen
document.addEventListener('DOMContentLoaded', function() {
	const loadingScreen = document.getElementById('loading-screen');
	if (loadingScreen) {
		loadingScreen.style.opacity = '0';
		setTimeout(() => {
			loadingScreen.style.display = 'none';
		}, 300);
	}
});

// Back to Top Button
(function(){
	const backToTopBtn = document.getElementById('backToTop');
	if (!backToTopBtn) return;
	window.addEventListener('scroll', function() {
		if (window.pageYOffset > 300) {
			backToTopBtn.style.display = 'block';
		} else {
			backToTopBtn.style.display = 'none';
		}
	}, { passive: true });
	backToTopBtn.addEventListener('click', function() {
		window.scrollTo({ top: 0, behavior: 'smooth' });
	});
})();

// Dropdown Toggle
window.toggleDropdown = function() {
	const dropdown = document.getElementById('profileDropdown');
	const toggle = document.querySelector('.dropdown-toggle');
	if (!dropdown || !toggle) return;
	dropdown.classList.toggle('show');
	toggle.classList.toggle('active');
};

document.addEventListener('click', function(event) {
	const dropdown = document.getElementById('profileDropdown');
	const toggle = document.querySelector('.dropdown-toggle');
	if (!dropdown || !toggle) return;
	if (!toggle.contains(event.target) && !dropdown.contains(event.target)) {
		dropdown.classList.remove('show');
		toggle.classList.remove('active');
	}
});

// Newsletter Form
(function(){
	const newsletterForm = document.getElementById('newsletterForm');
	if (!newsletterForm) return;
	newsletterForm.addEventListener('submit', function(e) {
		e.preventDefault();
		const email = this.querySelector('.newsletter-input').value;
		const consent = this.querySelector('#newsletterConsent').checked;
		if (email && consent) {
			alert('با موفقیت در خبرنامه عضو شدید!');
			this.reset();
		} else {
			alert('لطفاً ایمیل را وارد کنید و موافقت خود را اعلام کنید.');
		}
	});
})();

// Lazy Loading for Images
(function(){
	if ('IntersectionObserver' in window) {
		const imageObserver = new IntersectionObserver((entries) => {
			entries.forEach(entry => {
				if (entry.isIntersecting) {
					const img = entry.target;
					if (img.dataset && img.dataset.src) {
						img.src = img.dataset.src;
					}
					img.classList.remove('lazy');
					imageObserver.unobserve(img);
				}
			});
		});
		document.querySelectorAll('img[data-src]').forEach(img => imageObserver.observe(img));
	}
	// Ensure lazy loading and async decoding
	document.addEventListener('DOMContentLoaded', function () {
		document.querySelectorAll('img:not([loading])').forEach(function(img){ img.setAttribute('loading','lazy'); });
		document.querySelectorAll('img:not([decoding])').forEach(function(img){ img.setAttribute('decoding','async'); });
	});
})();

// Dynamic navbar offset for non-home pages
(function() {
	function applyNavbarOffset() {
		var navbar = document.querySelector('.navbar');
		var isHome = document.body.classList.contains('home-page');
		if (!isHome && navbar) {
			var height = navbar.offsetHeight || 80;
			document.documentElement.style.setProperty('--navbar-offset', height + 'px');
		} else {
			document.documentElement.style.removeProperty('--navbar-offset');
		}
	}
	document.addEventListener('DOMContentLoaded', applyNavbarOffset);
	window.addEventListener('load', applyNavbarOffset);
	window.addEventListener('resize', applyNavbarOffset);
})();

// CSRF accessor
window.getCSRFToken = function() {
	var meta = document.querySelector('meta[name="csrf-token"]');
	return (meta && meta.content) ? meta.content : '';
};

// Cart count updater (only when authenticated and element exists)
window.updateCartCount = function() {
	const el = document.getElementById('cartCount');
	if (!el) return;
	const cartCountUrlMeta = document.querySelector('meta[name="cart-count-url"]');
	const url = cartCountUrlMeta && cartCountUrlMeta.content ? cartCountUrlMeta.content : null;
	if (!url) return;
	fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' }})
		.then(function(response){ return response.json(); })
		.then(function(data){ if (typeof data.count === 'number') { el.textContent = data.count; } })
		.catch(function(){});
};

document.addEventListener('DOMContentLoaded', function(){
	if (document.body.classList.contains('authenticated')) {
		window.updateCartCount();
	}
});