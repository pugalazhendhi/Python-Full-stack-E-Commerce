from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.edit_profile_view, name='edit_profile'),
    path('password-change/', views.change_password_view, name='change_password'),
    path('addresses/', views.address_list_view, name='address_list'),
    path('addresses/add/', views.add_address_view, name='add_address'),
    path('addresses/<int:pk>/edit/', views.edit_address_view, name='edit_address'),
    path('addresses/<int:pk>/delete/', views.delete_address_view, name='delete_address'),
    path('addresses/<int:pk>/default/', views.set_default_address_view, name='set_default_address'),
]
