from django.urls import path
from . import views

app_name = 'wishlist'

urlpatterns = [
    path('', views.wishlist_view, name='wishlist_detail'),
    path('toggle/<int:product_id>/', views.toggle_wishlist_view, name='toggle_wishlist'),
    path('move-to-cart/<int:product_id>/', views.move_to_cart_view, name='move_to_cart'),
]
