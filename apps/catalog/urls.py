from django.urls import path
from . import views

app_name = 'catalog'

urlpatterns = [
    path('', views.home_view, name='home'),
    path('products/', views.product_list_view, name='product_list'),
    path('products/category/<slug:category_slug>/', views.product_list_view, name='product_list_by_category'),
    path('products/<slug:slug>/', views.product_detail_view, name='product_detail'),
    path('products/<slug:slug>/review/', views.add_review_view, name='add_review'),
    path('api/search-suggest/', views.search_suggestions_api, name='search_suggestions_api'),
]
