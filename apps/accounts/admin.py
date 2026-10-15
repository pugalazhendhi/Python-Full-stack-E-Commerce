from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, UserProfile, Address

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile Details'

class AddressInline(admin.TabularInline):
    model = Address
    extra = 0
    fields = ('full_name', 'phone_number', 'city', 'state', 'postal_code', 'is_default')

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline, AddressInline)
    list_display = ('username', 'email', 'first_name', 'last_name', 'phone_number', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')
    search_fields = ('username', 'first_name', 'last_name', 'email', 'phone_number')
    ordering = ('-date_joined',)

    fieldsets = BaseUserAdmin.fieldsets + (
        ('Extra Info', {'fields': ('phone_number', 'is_verified')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Extra Info', {'fields': ('email', 'phone_number')}),
    )

@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'user', 'phone_number', 'city', 'state', 'postal_code', 'is_default', 'created_at')
    list_filter = ('address_type', 'is_default', 'state', 'created_at')
    search_fields = ('full_name', 'user__username', 'user__email', 'address_line1', 'city', 'postal_code')
