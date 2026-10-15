from django.db import models, transaction
from django.conf import settings
from decimal import Decimal
from django.utils import timezone
from apps.catalog.models import Product

class Coupon(models.Model):
    """
    Coupons and promotional discounts.
    """
    DISCOUNT_TYPES = (
        ('percentage', 'Percentage Discount (%)'),
        ('flat', 'Flat Amount Discount ($)'),
    )

    code = models.CharField(max_length=30, unique=True, verbose_name="Coupon Code")
    description = models.CharField(max_length=200, blank=True, verbose_name="Description")
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPES, default='percentage')
    discount_value = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Discount Value")
    min_purchase_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), verbose_name="Minimum Order Subtotal")
    max_discount_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Maximum Discount Cap (Optional)")
    max_uses = models.PositiveIntegerField(null=True, blank=True, verbose_name="Max Redemptions Allowed")
    used_count = models.PositiveIntegerField(default=0, verbose_name="Times Used")
    valid_from = models.DateTimeField(default=timezone.now, verbose_name="Valid From")
    valid_to = models.DateTimeField(verbose_name="Valid Until")
    is_active = models.BooleanField(default=True, verbose_name="Is Active")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Coupon'
        verbose_name_plural = 'Coupons'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.code} ({self.get_discount_display()})"

    def get_discount_display(self):
        if self.discount_type == 'percentage':
            return f"{self.discount_value}% off"
        return f"${self.discount_value:.2f} off"

    def is_valid_for(self, subtotal):
        now = timezone.now()
        if not self.is_active:
            return False, "This coupon is no longer active."
        if now < self.valid_from or now > self.valid_to:
            return False, "This coupon has expired or is not yet valid."
        if self.max_uses is not None and self.used_count >= self.max_uses:
            return False, "This coupon has reached its maximum usage limit."
        if Decimal(subtotal) < self.min_purchase_amount:
            return False, f"Minimum purchase amount for this coupon is ${self.min_purchase_amount:.2f}."
        return True, "Valid coupon"

    def calculate_discount(self, subtotal):
        valid, msg = self.is_valid_for(subtotal)
        if not valid:
            return Decimal('0.00')
        subtotal = Decimal(subtotal)
        if self.discount_type == 'percentage':
            discount = (subtotal * self.discount_value) / Decimal('100.00')
            if self.max_discount_amount and discount > self.max_discount_amount:
                discount = self.max_discount_amount
        else:
            discount = min(self.discount_value, subtotal)
        return round(discount, 2)


class Order(models.Model):
    """
    Order model storing complete transaction, shipping snapshot, and payment state.
    """
    ORDER_STATUS = (
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    )

    PAYMENT_METHODS = (
        ('cod', 'Cash on Delivery (COD)'),
        ('card', 'Credit / Debit Card (Online Gateway Ready)'),
    )

    PAYMENT_STATUS = (
        ('unpaid', 'Unpaid'),
        ('paid', 'Paid'),
        ('refunded', 'Refunded'),
    )

    order_number = models.CharField(max_length=64, unique=True, verbose_name="Order Number")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
    
    # Snapshot of delivery address to ensure permanent historical accuracy
    shipping_full_name = models.CharField(max_length=150, verbose_name="Recipient Name")
    shipping_phone = models.CharField(max_length=20, verbose_name="Recipient Phone")
    shipping_address_line1 = models.CharField(max_length=255, verbose_name="Address Line 1")
    shipping_address_line2 = models.CharField(max_length=255, blank=True, verbose_name="Address Line 2")
    shipping_city = models.CharField(max_length=100, verbose_name="City")
    shipping_state = models.CharField(max_length=100, verbose_name="State")
    shipping_postal_code = models.CharField(max_length=20, verbose_name="Postal Code")
    shipping_country = models.CharField(max_length=100, default="India", verbose_name="Country")

    # Order tracking and payment
    status = models.CharField(max_length=20, choices=ORDER_STATUS, default='pending')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='cod')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='unpaid')
    transaction_id = models.CharField(max_length=100, blank=True, null=True, help_text="Gateway transaction reference")

    # Financial breakdown (Strict DecimalField)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    shipping_fee = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))

    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    coupon_code_snapshot = models.CharField(max_length=50, blank=True, null=True)

    customer_notes = models.TextField(blank=True, verbose_name="Order / Delivery Instructions")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Customer Order'
        verbose_name_plural = 'Customer Orders'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['order_number']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"Order #{self.order_number} ({self.user.username})"

    @property
    def total_items_count(self):
        return sum(item.quantity for item in self.items.all())

    @property
    def can_cancel(self):
        """
        Orders can only be cancelled while in 'pending' or 'confirmed' state.
        """
        return self.status in ['pending', 'confirmed']

    @transaction.atomic
    def cancel_order(self):
        """
        Cancel order safely and restore product inventory.
        """
        if not self.can_cancel:
            return False, "This order cannot be cancelled at this stage."
        
        self.status = 'cancelled'
        self.save(update_fields=['status', 'updated_at'])

        # Restore product stock
        for item in self.items.all():
            if item.product:
                Product.objects.filter(id=item.product.id).update(
                    stock=models.F('stock') + item.quantity
                )
        return True, "Order has been cancelled and inventory restored."

    @property
    def status_badge_class(self):
        mapping = {
            'pending': 'bg-warning text-dark',
            'confirmed': 'bg-primary',
            'shipped': 'bg-info text-dark',
            'delivered': 'bg-success',
            'cancelled': 'bg-danger',
        }
        return mapping.get(self.status, 'bg-secondary')


class OrderItem(models.Model):
    """
    Snapshots product details and prices at time of order creation.
    """
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True, related_name='order_items')
    
    # Snapshot fields
    product_name = models.CharField(max_length=220)
    product_sku = models.CharField(max_length=64, blank=True)
    product_image_url = models.CharField(max_length=500, blank=True, null=True)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = 'Order Line Item'
        verbose_name_plural = 'Order Line Items'

    def __str__(self):
        return f"{self.quantity}x {self.product_name} (${self.total_price})"

    def save(self, *args, **kwargs):
        if not self.total_price:
            self.total_price = Decimal(self.unit_price) * self.quantity
        super().save(*args, **kwargs)
