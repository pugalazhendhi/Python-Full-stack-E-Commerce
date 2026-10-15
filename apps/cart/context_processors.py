from .models import Cart

def cart_processor(request):
    """
    Exposes total cart item count and cart subtotal globally to all templates.
    Handles both logged-in users and guest sessions.
    """
    cart = None
    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user).first()
    else:
        if request.session.session_key:
            cart = Cart.objects.filter(session_key=request.session.session_key).first()

    if cart:
        return {
            'cart_count': cart.total_items,
            'cart_subtotal': cart.subtotal,
            'active_cart': cart,
        }
    return {
        'cart_count': 0,
        'cart_subtotal': 0,
        'active_cart': None,
    }
