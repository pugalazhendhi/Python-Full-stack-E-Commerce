/**
 * ShopSphere — Core Frontend Interactions & Asynchronous Operations
 */

// Helper to get CSRF cookie in Django
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

const csrftoken = getCookie('csrftoken');

// Universal Toast Dispatcher
function showToast(message, type = 'success') {
    let container = document.getElementById('toastContainer');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toastContainer';
        container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        container.style.zIndex = '1099';
        document.body.appendChild(container);
    }

    const toastId = 'toast-' + Date.now();
    const bgClass = type === 'success' ? 'bg-success text-white' : 
                    type === 'error' || type === 'danger' ? 'bg-danger text-white' : 
                    type === 'warning' ? 'bg-warning text-dark' : 'bg-primary text-white';

    const icon = type === 'success' ? 'bi-check-circle-fill' : 
                 type === 'error' || type === 'danger' ? 'bi-exclamation-triangle-fill' : 
                 type === 'warning' ? 'bi-exclamation-circle-fill' : 'bi-info-circle-fill';

    const toastHtml = `
        <div id="${toastId}" class="toast align-items-center ${bgClass} border-0 shadow-lg" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="d-flex">
                <div class="toast-body d-flex align-items-center gap-2 py-3 px-3">
                    <i class="bi ${icon} fs-5"></i>
                    <span class="fw-semibold">${message}</span>
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        </div>
    `;

    container.insertAdjacentHTML('beforeend', toastHtml);
    const toastElem = document.getElementById(toastId);
    const bsToast = new bootstrap.Toast(toastElem, { delay: 4000 });
    bsToast.show();

    toastElem.addEventListener('hidden.bs.toast', () => {
        toastElem.remove();
    });
}

// Global DOM Content Loaded Handler
document.addEventListener('DOMContentLoaded', () => {
    // 1. Auto-show any existing Django messages passed in toast format
    const existingAlerts = document.querySelectorAll('.django-flash-message');
    existingAlerts.forEach(alert => {
        const msg = alert.getAttribute('data-message');
        const tag = alert.getAttribute('data-tag') || 'info';
        if (msg) showToast(msg, tag);
    });

    // 2. AJAX Add to Cart Buttons
    document.querySelectorAll('.btn-add-to-cart-ajax').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const productId = this.getAttribute('data-product-id');
            const qtyInput = document.querySelector(`#quantityInput_${productId}`) || document.querySelector('#productQuantityInput');
            const quantity = qtyInput ? qtyInput.value : 1;

            const originalHtml = this.innerHTML;
            this.innerHTML = '<span class="spinner-border spinner-border-sm me-1" role="status"></span> Adding...';
            this.disabled = true;

            fetch(`/cart/add/${productId}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrftoken,
                    'X-Requested-With': 'XMLHttpRequest',
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: new URLSearchParams({
                    'quantity': quantity
                })
            })
            .then(res => res.json())
            .then(data => {
                this.innerHTML = originalHtml;
                this.disabled = false;

                if (data.status === 'success' || data.status === 'warning') {
                    showToast(data.message, data.status);
                    // Update Cart badge in nav
                    const badge = document.getElementById('navbarCartCount');
                    if (badge && data.cart_count !== undefined) {
                        badge.textContent = data.cart_count;
                        badge.classList.remove('d-none');
                    }
                } else {
                    showToast(data.message || 'Could not add to cart.', 'error');
                }
            })
            .catch(err => {
                this.innerHTML = originalHtml;
                this.disabled = false;
                showToast('An error occurred. Please try again.', 'error');
            });
        });
    });

    // 3. AJAX Wishlist Toggle Buttons
    document.querySelectorAll('.btn-toggle-wishlist').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const productId = this.getAttribute('data-product-id');
            const icon = this.querySelector('i');

            fetch(`/wishlist/toggle/${productId}/`, {
                method: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'Accept': 'application/json'
                }
            })
            .then(res => {
                if (res.redirected) {
                    window.location.href = res.url;
                    return;
                }
                return res.json();
            })
            .then(data => {
                if (!data) return;
                if (data.status === 'success') {
                    showToast(data.message, data.action === 'added' ? 'success' : 'info');
                    if (data.action === 'added') {
                        this.classList.add('active');
                        if (icon) {
                            icon.classList.remove('bi-heart');
                            icon.classList.add('bi-heart-fill');
                        }
                    } else {
                        this.classList.remove('active');
                        if (icon) {
                            icon.classList.remove('bi-heart-fill');
                            icon.classList.add('bi-heart');
                        }
                    }

                    // Update Wishlist Badge
                    const wBadge = document.getElementById('navbarWishlistCount');
                    if (wBadge && data.wishlist_count !== undefined) {
                        wBadge.textContent = data.wishlist_count;
                        if (data.wishlist_count > 0) {
                            wBadge.classList.remove('d-none');
                        } else {
                            wBadge.classList.add('d-none');
                        }
                    }
                }
            })
            .catch(err => {
                showToast('Unable to update wishlist. Please make sure you are logged in.', 'error');
            });
        });
    });

    // 4. Live Search Autosuggestions with Debounce
    const searchInput = document.getElementById('navbarSearchInput');
    const searchDropdown = document.getElementById('searchSuggestionsDropdown');
    let searchTimeout = null;

    if (searchInput && searchDropdown) {
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            const val = this.value.trim();

            if (val.length < 2) {
                searchDropdown.style.display = 'none';
                searchDropdown.innerHTML = '';
                return;
            }

            searchTimeout = setTimeout(() => {
                fetch(`/api/search-suggest/?q=${encodeURIComponent(val)}`)
                    .then(res => res.json())
                    .then(data => {
                        if (data.results && data.results.length > 0) {
                            let html = '';
                            data.results.forEach(item => {
                                html += `
                                    <a href="${item.url}" class="search-suggestion-item">
                                        <img src="${item.image}" alt="${item.name}">
                                        <div class="flex-grow-1">
                                            <div class="fw-semibold text-truncate" style="max-width: 280px;">${item.name}</div>
                                            <small class="text-muted">${item.category}</small>
                                        </div>
                                        <span class="fw-bold text-primary">$${item.price}</span>
                                    </a>
                                `;
                            });
                            searchDropdown.innerHTML = html;
                            searchDropdown.style.display = 'block';
                        } else {
                            searchDropdown.innerHTML = '<div class="p-3 text-center text-muted small">No products found</div>';
                            searchDropdown.style.display = 'block';
                        }
                    })
                    .catch(() => {
                        searchDropdown.style.display = 'none';
                    });
            }, 250);
        });

        // Close dropdown when clicking outside
        document.addEventListener('click', (e) => {
            if (!searchInput.contains(e.target) && !searchDropdown.contains(e.target)) {
                searchDropdown.style.display = 'none';
            }
        });
    }

    // 5. Product Detail Image Gallery Swapper
    const mainImg = document.getElementById('mainProductImage');
    const thumbs = document.querySelectorAll('.gallery-thumbnail');
    if (mainImg && thumbs.length > 0) {
        thumbs.forEach(thumb => {
            thumb.addEventListener('click', function() {
                thumbs.forEach(t => t.classList.remove('active'));
                this.classList.add('active');
                const newSrc = this.getAttribute('data-full-src');
                if (newSrc) {
                    mainImg.style.opacity = '0.5';
                    mainImg.src = newSrc;
                    setTimeout(() => { mainImg.style.opacity = '1'; }, 100);
                }
            });
        });
    }

    // 6. Quantity Stepper (+ and - buttons)
    document.querySelectorAll('.btn-qty-minus').forEach(btn => {
        btn.addEventListener('click', function() {
            const input = this.parentElement.querySelector('input');
            if (input) {
                let current = parseInt(input.value) || 1;
                if (current > 1) {
                    input.value = current - 1;
                    input.dispatchEvent(new Event('change'));
                }
            }
        });
    });

    document.querySelectorAll('.btn-qty-plus').forEach(btn => {
        btn.addEventListener('click', function() {
            const input = this.parentElement.querySelector('input');
            if (input) {
                let current = parseInt(input.value) || 1;
                let max = parseInt(input.getAttribute('max')) || 999;
                if (current < max) {
                    input.value = current + 1;
                    input.dispatchEvent(new Event('change'));
                } else {
                    showToast(`Maximum stock limit is ${max}`, 'warning');
                }
            }
        });
    });
});
