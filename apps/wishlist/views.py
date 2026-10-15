from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import Wishlist, WishlistItem
from apps.catalog.models import Product
from apps.cart.models import Cart, CartItem

@login_required
def wishlist_view(request):
    """
    Renders customer's saved wishlist products.
    """
    wishlist, _ = Wishlist.objects.get_or_create(user=request.user)
    items = wishlist.items.select_related('product', 'product__category').all()
    return render(request, 'wishlist/wishlist_detail.html', {'wishlist': wishlist, 'items': items})


@login_required
def toggle_wishlist_view(request, product_id):
    """
    Toggles a product in/out of the user's wishlist.
    Supports AJAX for instant heart icon response.
    """
    product = get_object_or_404(Product, id=product_id, is_active=True)
    wishlist, _ = Wishlist.objects.get_or_create(user=request.user)

    item = WishlistItem.objects.filter(wishlist=wishlist, product=product).first()
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('format') == 'json'

    if item:
        item.delete()
        action = 'removed'
        msg = f"Removed '{product.name}' from your wishlist."
    else:
        WishlistItem.objects.create(wishlist=wishlist, product=product)
        action = 'added'
        msg = f"Saved '{product.name}' to your wishlist!"

    current_count = wishlist.items.count()

    if is_ajax:
        return JsonResponse({
            'status': 'success',
            'action': action,
            'message': msg,
            'wishlist_count': current_count,
            'product_id': product.id,
        })

    if action == 'added':
        messages.success(request, msg)
    else:
        messages.info(request, msg)

    return redirect(request.META.get('HTTP_REFERER', 'wishlist:wishlist_detail'))


@login_required
def move_to_cart_view(request, product_id):
    """
    Transfers a saved wishlist product into the shopping cart.
    """
    product = get_object_or_404(Product, id=product_id, is_active=True)
    wishlist, _ = Wishlist.objects.get_or_create(user=request.user)

    if product.stock <= 0:
        messages.error(request, f"Sorry, '{product.name}' is currently out of stock.")
        return redirect('wishlist:wishlist_detail')

    cart, _ = Cart.objects.get_or_create(user=request.user)
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)

    if not created:
        if cart_item.quantity < product.stock:
            cart_item.quantity += 1
            cart_item.save()
    else:
        cart_item.quantity = 1
        cart_item.save()

    # Remove from wishlist
    WishlistItem.objects.filter(wishlist=wishlist, product=product).delete()

    messages.success(request, f"Moved '{product.name}' from your wishlist to shopping cart!")
    return redirect('cart:cart_detail')
