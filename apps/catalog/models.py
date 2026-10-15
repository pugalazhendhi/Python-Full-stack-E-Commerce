from django.db import models
from django.utils.text import slugify
from django.conf import settings
from decimal import Decimal
from django.core.validators import MinValueValidator, MaxValueValidator

class Category(models.Model):
    """
    Product categories (e.g. Electronics, Fashion, Home & Kitchen, Books, Accessories).
    """
    name = models.CharField(max_length=100, unique=True, verbose_name="Category Name")
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True, verbose_name="Description")
    image = models.ImageField(upload_to='categories/', blank=True, null=True, verbose_name="Category Banner/Image")
    icon_class = models.CharField(max_length=50, default='bi-tag', help_text="Bootstrap icon class, e.g. bi-laptop, bi-bag")
    is_featured = models.BooleanField(default=False, verbose_name="Featured on Homepage")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    @property
    def product_count(self):
        return self.products.filter(is_active=True).count()


class Product(models.Model):
    """
    Product model storing pricing, stock, metadata, and status.
    """
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=220, verbose_name="Product Title")
    slug = models.SlugField(max_length=240, unique=True, blank=True)
    sku = models.CharField(max_length=64, unique=True, verbose_name="SKU / Item Code")
    short_description = models.CharField(max_length=300, blank=True, help_text="Short highlight for cards and banners")
    description = models.TextField(verbose_name="Full Description")
    specifications = models.TextField(blank=True, help_text="One specification per line (e.g. Brand: Apple | Color: Space Gray)")
    
    # Financial fields must use DecimalField
    price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        validators=[MinValueValidator(Decimal('0.01'))], 
        verbose_name="Selling Price"
    )
    original_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        blank=True, 
        null=True, 
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="Original / MRP Price (for discount display)"
    )
    
    stock = models.PositiveIntegerField(default=0, verbose_name="Available Stock")
    cover_image = models.ImageField(upload_to='products/covers/', blank=True, null=True, verbose_name="Main Product Image")
    
    # Flags for storefront merchandising
    is_active = models.BooleanField(default=True, verbose_name="Active for Sale")
    is_featured = models.BooleanField(default=False, verbose_name="Featured Product")
    is_bestseller = models.BooleanField(default=False, verbose_name="Best Seller")
    is_new_arrival = models.BooleanField(default=False, verbose_name="New Arrival")

    # Aggregated rating cache
    rating_average = models.DecimalField(max_digits=3, decimal_places=2, default=Decimal('0.00'), verbose_name="Average Rating")
    rating_count = models.PositiveIntegerField(default=0, verbose_name="Total Reviews")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Product'
        verbose_name_plural = 'Products'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['price']),
            models.Index(fields=['is_active']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.name} (${self.price})"

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    @property
    def is_in_stock(self):
        return self.stock > 0

    @property
    def discount_percentage(self):
        if self.original_price and self.original_price > self.price:
            savings = self.original_price - self.price
            return int(round((savings / self.original_price) * 100))
        return 0

    def update_rating_stats(self):
        approved_reviews = self.reviews.filter(is_approved=True)
        count = approved_reviews.count()
        if count > 0:
            avg = approved_reviews.aggregate(models.Avg('rating'))['rating__avg'] or 0.0
            self.rating_average = round(Decimal(avg), 2)
            self.rating_count = count
        else:
            self.rating_average = Decimal('0.00')
            self.rating_count = 0
        self.save(update_fields=['rating_average', 'rating_count'])


class ProductImage(models.Model):
    """
    Multiple product gallery images.
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='gallery_images')
    image = models.ImageField(upload_to='products/gallery/', verbose_name="Gallery Image")
    alt_text = models.CharField(max_length=200, blank=True)
    display_order = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Product Gallery Image'
        verbose_name_plural = 'Product Gallery Images'
        ordering = ['display_order', 'id']

    def __str__(self):
        return f"Image for {self.product.name}"


class ProductReview(models.Model):
    """
    Customer reviews and star ratings.
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="Rating (1-5 Stars)"
    )
    title = models.CharField(max_length=120, verbose_name="Review Headline")
    comment = models.TextField(verbose_name="Review Comment")
    is_approved = models.BooleanField(default=True, verbose_name="Approved for Display")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Product Review'
        verbose_name_plural = 'Product Reviews'
        ordering = ['-created_at']
        unique_together = ('product', 'user')

    def __str__(self):
        return f"{self.user.username} - {self.product.name} ({self.rating}★)"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.product.update_rating_stats()

    def delete(self, *args, **kwargs):
        product = self.product
        super().delete(*args, **kwargs)
        product.update_rating_stats()
