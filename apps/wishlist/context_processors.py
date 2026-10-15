from .models import Wishlist

def wishlist_processor(request):
    """
    Exposes wishlist item count and saved product IDs to templates.
    """
    if request.user.is_authenticated:
        try:
            wishlist = Wishlist.objects.get(user=request.user)
            product_ids = set(wishlist.items.values_list('product_id', flat=True))
            return {
                'wishlist_count': len(product_ids),
                'wishlist_product_ids': product_ids
            }
        except Wishlist.DoesNotExist:
            return {
                'wishlist_count': 0,
                'wishlist_product_ids': set()
            }
    return {
        'wishlist_count': 0,
        'wishlist_product_ids': set()
    }
