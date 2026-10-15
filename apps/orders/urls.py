from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('checkout/', views.checkout_view, name='checkout'),
    path('checkout/place-order/', views.place_order_view, name='place_order'),
    path('checkout/apply-coupon/', views.apply_coupon_view, name='apply_coupon'),
    path('confirmation/<str:order_number>/', views.order_confirmation_view, name='order_confirmation'),
    path('history/', views.order_history_view, name='order_history'),
    path('detail/<str:order_number>/', views.order_detail_view, name='order_detail'),
    path('cancel/<str:order_number>/', views.cancel_order_view, name='cancel_order'),
]
