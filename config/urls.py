"""
ShopSphere URL Configuration
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.catalog.urls', namespace='catalog')),
    path('accounts/', include('apps.accounts.urls', namespace='accounts')),
    path('cart/', include('apps.cart.urls', namespace='cart')),
    path('orders/', include('apps.orders.urls', namespace='orders')),
    path('wishlist/', include('apps.wishlist.urls', namespace='wishlist')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])

# Customize Admin Site Headers
admin.site.site_header = "ShopSphere Admin Portal"
admin.site.site_title = "ShopSphere Administration"
admin.site.index_title = "Store Management & Operations"
