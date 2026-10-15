from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.conf import settings
from decimal import Decimal
from .models import Cart, CartItem
from apps.catalog.models import Product

def get_or_create_cart(request):
    """
    Retrieves or creates a cart for the current authenticated user or anonymous session.
    """
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
    else:
        if not request.session.session_key:
            request.session.save()
        cart, _ = Cart.objects.get_or_create(session_key=request.session.session_key)
    return cart


def cart_detail_view(request):
    """
    Renders cart items and financial summary with real-time calculations.
    """
    cart = get_or_create_cart(request)
    cart_items = cart.items.select_related('product', 'product__category').all()

    # Re-validate stock for all items
    stock_warnings = []
    for item in cart_items:
        if not item.product.is_active or item.product.stock == 0:
            stock_warnings.append(f"'{item.product.name}' is currently out of stock.")
        elif item.quantity > item.product.stock:
            item.quantity = item.product.stock
            item.save()
            stock_warnings.append(f"Quantity for '{item.product.name}' adjusted to available stock ({item.product.stock}).")

    subtotal = cart.subtotal
    free_shipping_threshold = Decimal(str(getattr(settings, 'FREE_SHIPPING_THRESHOLD', 500.00)))
    base_shipping_fee = Decimal(str(getattr(settings, 'SHIPPING_FEE', 50.00)))

    if subtotal >= free_shipping_threshold or subtotal == Decimal('0.00'):
        shipping_fee = Decimal('0.00')
    else:
        shipping_fee = base_shipping_fee

    tax_rate = Decimal(str(getattr(settings, 'TAX_RATE', 0.05)))
    tax_amount = round(subtotal * tax_rate, 2)
    grand_total = subtotal + shipping_fee + tax_amount

    # Free shipping progress
    if free_shipping_threshold > 0:
        shipping_progress = min(100, int((subtotal / free_shipping_threshold) * 100))
        amount_needed_for_free_shipping = max(Decimal('0.00'), free_shipping_threshold - subtotal)
    else:
        shipping_progress = 100
        amount_needed_for_free_shipping = Decimal('0.00')

    context = {
        'cart': cart,
        'cart_items': cart_items,
        'subtotal': subtotal,
        'shipping_fee': shipping_fee,
        'tax_amount': tax_amount,
        'grand_total': grand_total,
        'shipping_progress': shipping_progress,
        'free_shipping_threshold': free_shipping_threshold,
        'amount_needed_for_free_shipping': amount_needed_for_free_shipping,
        'stock_warnings': stock_warnings,
    }
    return render(request, 'cart/cart_detail.html', context)


def add_to_cart_view(request, product_id):
    """
    Adds a product to cart with strict server-side stock validation.
    Supports both traditional POST/GET and AJAX requests.
    """
    product = get_object_or_404(Product, id=product_id, is_active=True)
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('format') == 'json'

    # Check stock
    if product.stock <= 0:
        if is_ajax:
            return JsonResponse({'status': 'error', 'message': f"Sorry, '{product.name}' is out of stock."}, status=400)
        messages.error(request, f"Sorry, '{product.name}' is currently out of stock.")
        return redirect(request.META.get('HTTP_REFERER', 'catalog:product_list'))

    try:
        qty = int(request.POST.get('quantity', 1) or request.GET.get('quantity', 1))
        if qty < 1:
            qty = 1
    except (ValueError, TypeError):
        qty = 1

    cart = get_or_create_cart(request)
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)

    if not created:
        new_quantity = cart_item.quantity + qty
        if new_quantity > product.stock:
            allowed_qty = product.stock
            cart_item.quantity = allowed_qty
            cart_item.save()
            msg = f"Only {product.stock} units of '{product.name}' available in stock. Quantity adjusted."
            if is_ajax:
                return JsonResponse({
                    'status': 'warning',
                    'message': msg,
                    'cart_count': cart.total_items,
                    'cart_subtotal': str(cart.subtotal)
                })
            messages.warning(request, msg)
            return redirect('cart:cart_detail')
        else:
            cart_item.quantity = new_quantity
            cart_item.save()
    else:
        if qty > product.stock:
            cart_item.quantity = product.stock
            cart_item.save()
            msg = f"Only {product.stock} units available. Added {product.stock} to your cart."
            if is_ajax:
                return JsonResponse({
                    'status': 'warning',
                    'message': msg,
                    'cart_count': cart.total_items,
                    'cart_subtotal': str(cart.subtotal)
                })
            messages.warning(request, msg)
            return redirect('cart:cart_detail')
        else:
            cart_item.quantity = qty
            cart_item.save()

    msg = f"Added {qty}x '{product.name}' to your cart!"
    if is_ajax:
        return JsonResponse({
            'status': 'success',
            'message': msg,
            'cart_count': cart.total_items,
            'cart_subtotal': str(cart.subtotal)
        })

    messages.success(request, msg)
    next_url = request.POST.get('next') or request.GET.get('next')
    if next_url:
        return redirect(next_url)
    return redirect('cart:cart_detail')


def update_cart_item_view(request, item_id):
    """
    Updates the quantity of a cart line item with server validation.
    """
    cart = get_or_create_cart(request)
    cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

    if request.method == 'POST':
        try:
            quantity = int(request.POST.get('quantity', 1))
        except (ValueError, TypeError):
            quantity = 1

        if quantity <= 0:
            cart_item.delete()
            msg = f"Removed '{cart_item.product.name}' from your cart."
            if is_ajax:
                return JsonResponse({
                    'status': 'success',
                    'removed': True,
                    'message': msg,
                    'cart_count': cart.total_items,
                    'cart_subtotal': str(cart.subtotal)
                })
            messages.info(request, msg)
            return redirect('cart:cart_detail')

        if quantity > cart_item.product.stock:
            cart_item.quantity = cart_item.product.stock
            cart_item.save()
            msg = f"Only {cart_item.product.stock} units available in stock."
            if is_ajax:
                return JsonResponse({
                    'status': 'warning',
                    'message': msg,
                    'item_quantity': cart_item.quantity,
                    'item_total': str(cart_item.total_price),
                    'cart_count': cart.total_items,
                    'cart_subtotal': str(cart.subtotal)
                })
            messages.warning(request, msg)
            return redirect('cart:cart_detail')

        cart_item.quantity = quantity
        cart_item.save()

        if is_ajax:
            return JsonResponse({
                'status': 'success',
                'message': "Cart updated",
                'item_quantity': cart_item.quantity,
                'item_total': str(cart_item.total_price),
                'cart_count': cart.total_items,
                'cart_subtotal': str(cart.subtotal)
            })

        messages.success(request, f"Updated quantity for '{cart_item.product.name}'.")

    return redirect('cart:cart_detail')


def remove_cart_item_view(request, item_id):
    """
    Removes a product from the shopping cart.
    """
    cart = get_or_create_cart(request)
    cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
    product_name = cart_item.product.name
    cart_item.delete()

    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'
    if is_ajax:
        return JsonResponse({
            'status': 'success',
            'message': f"Removed '{product_name}' from cart.",
            'cart_count': cart.total_items,
            'cart_subtotal': str(cart.subtotal)
        })

    messages.info(request, f"Removed '{product_name}' from your cart.")
    return redirect('cart:cart_detail')


def clear_cart_view(request):
    """
    Empties all items from current cart.
    """
    cart = get_or_create_cart(request)
    cart.clear()
    messages.info(request, "Your shopping cart has been cleared.")
    return redirect('cart:cart_detail')
