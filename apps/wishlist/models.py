from django.db import models
from django.conf import settings
from apps.catalog.models import Product

class Wishlist(models.Model):
    """
    User's saved wishlist of products.
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wishlist')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Wishlist'
        verbose_name_plural = 'Wishlists'

    def __str__(self):
        return f"Wishlist of {self.user.username}"

    @property
    def total_items(self):
        return self.items.count()


class WishlistItem(models.Model):
    """
    Item saved in a user's wishlist.
    """
    wishlist = models.ForeignKey(Wishlist, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='wishlist_items')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Wishlist Item'
        verbose_name_plural = 'Wishlist Items'
        unique_together = ('wishlist', 'product')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.wishlist.user.username} saved {self.product.name}"
