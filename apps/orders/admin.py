from django.contrib import admin
from django.utils.html import format_html
from .models import Order, OrderItem, Coupon

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ('product_name', 'product_sku', 'unit_price', 'quantity', 'total_price')
    readonly_fields = ('product_name', 'product_sku', 'unit_price', 'quantity', 'total_price')
    can_delete = False

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'order_number', 'user', 'shipping_full_name', 'status_badge', 
        'payment_method', 'payment_status', 'total_amount', 'created_at'
    )
    list_filter = ('status', 'payment_method', 'payment_status', 'created_at')
    search_fields = ('order_number', 'user__username', 'user__email', 'shipping_full_name', 'shipping_phone')
    readonly_fields = (
        'order_number', 'user', 'subtotal', 'shipping_fee', 'tax_amount', 
        'discount_amount', 'total_amount', 'coupon', 'coupon_code_snapshot', 
        'created_at', 'updated_at'
    )
    inlines = [OrderItemInline]
    actions = ['mark_confirmed', 'mark_shipped', 'mark_delivered', 'mark_cancelled']

    fieldsets = (
        ('Order Identifiers', {
            'fields': ('order_number', 'user', 'created_at', 'updated_at')
        }),
        ('Status & Payment', {
            'fields': ('status', 'payment_method', 'payment_status', 'transaction_id')
        }),
        ('Shipping Snapshot', {
            'fields': (
                'shipping_full_name', 'shipping_phone', 'shipping_address_line1', 
                'shipping_address_line2', 'shipping_city', 'shipping_state', 
                'shipping_postal_code', 'shipping_country'
            )
        }),
        ('Financial Summary', {
            'fields': (
                'subtotal', 'shipping_fee', 'tax_amount', 'discount_amount', 
                'total_amount', 'coupon', 'coupon_code_snapshot'
            )
        }),
        ('Customer Instructions', {
            'fields': ('customer_notes',)
        }),
    )

    def status_badge(self, obj):
        colors = {
            'pending': '#f59e0b',
            'confirmed': '#3b82f6',
            'shipped': '#06b6d4',
            'delivered': '#10b981',
            'cancelled': '#ef4444',
        }
        color = colors.get(obj.status, '#64748b')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 9999px; font-size: 11px; font-weight: 600; text-transform: uppercase;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def mark_confirmed(self, request, queryset):
        queryset.filter(status='pending').update(status='confirmed')
    mark_confirmed.short_description = "Mark selected orders as Confirmed"

    def mark_shipped(self, request, queryset):
        queryset.filter(status='confirmed').update(status='shipped')
    mark_shipped.short_description = "Mark selected orders as Shipped"

    def mark_delivered(self, request, queryset):
        queryset.filter(status='shipped').update(status='delivered', payment_status='paid')
    mark_delivered.short_description = "Mark selected orders as Delivered"

    def mark_cancelled(self, request, queryset):
        count = 0
        for order in queryset:
            success, _ = order.cancel_order()
            if success:
                count += 1
        self.message_user(request, f"{count} orders were successfully cancelled and their inventory restored.")
    mark_cancelled.short_description = "Cancel selected orders (Restore Stock)"


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_type', 'discount_value', 'min_purchase_amount', 'used_count', 'max_uses', 'valid_to', 'is_active')
    list_filter = ('discount_type', 'is_active', 'valid_from', 'valid_to')
    search_fields = ('code', 'description')
    list_editable = ('is_active',)
