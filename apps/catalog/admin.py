from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Product, ProductImage, ProductReview

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ('image', 'alt_text', 'display_order')

class ProductReviewInline(admin.TabularInline):
    model = ProductReview
    extra = 0
    readonly_fields = ('user', 'rating', 'title', 'comment', 'created_at')
    can_delete = True

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'icon_class', 'is_featured', 'product_count_display', 'created_at')
    list_filter = ('is_featured', 'created_at')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}

    def product_count_display(self, obj):
        return obj.product_count
    product_count_display.short_description = 'Active Products'

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'thumbnail', 'name', 'category', 'price', 'original_price', 
        'stock', 'is_active', 'is_featured', 'is_bestseller', 'rating_average', 'created_at'
    )
    list_editable = ('price', 'stock', 'is_active', 'is_featured', 'is_bestseller')
    list_filter = ('category', 'is_active', 'is_featured', 'is_bestseller', 'is_new_arrival', 'created_at')
    search_fields = ('name', 'sku', 'description', 'category__name')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductImageInline, ProductReviewInline]
    readonly_fields = ('rating_average', 'rating_count', 'created_at', 'updated_at')

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'sku', 'category', 'short_description', 'description', 'specifications')
        }),
        ('Pricing & Stock', {
            'fields': ('price', 'original_price', 'stock')
        }),
        ('Media', {
            'fields': ('cover_image',)
        }),
        ('Merchandising Flags', {
            'fields': ('is_active', 'is_featured', 'is_bestseller', 'is_new_arrival')
        }),
        ('Review Statistics', {
            'fields': ('rating_average', 'rating_count', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def thumbnail(self, obj):
        if obj.cover_image:
            return format_html('<img src="{}" style="width: 45px; height: 45px; object-fit: cover; border-radius: 4px;" />', obj.cover_image.url)
        return format_html('<div style="width: 45px; height: 45px; background: #e2e8f0; border-radius: 4px; display: flex; align-items: center; justify-content: center; font-size: 10px; color: #64748b;">No Img</div>')
    thumbnail.short_description = 'Image'

@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'title', 'is_approved', 'created_at')
    list_filter = ('rating', 'is_approved', 'created_at')
    search_fields = ('product__name', 'user__username', 'user__email', 'title', 'comment')
    list_editable = ('is_approved',)
    actions = ['approve_reviews']

    def approve_reviews(self, request, queryset):
        queryset.update(is_approved=True)
        for review in queryset:
            review.product.update_rating_stats()
    approve_reviews.short_description = "Approve selected reviews"
