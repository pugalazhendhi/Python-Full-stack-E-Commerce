import uuid
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction, models
from django.utils import timezone
from django.conf import settings
from django.http import JsonResponse
from .models import Order, OrderItem, Coupon
from apps.cart.models import Cart, CartItem
from apps.accounts.models import Address
from apps.catalog.models import Product

def generate_order_number():
    date_str = timezone.now().strftime('%Y%m%d')
    random_str = uuid.uuid4().hex[:6].upper()
    return f"ORD-{date_str}-{random_str}"


@login_required
def checkout_view(request):
    """
    Checkout page showing saved addresses, order items, coupon application,
    shipping calculations, and payment method selection.
    """
    cart = Cart.objects.filter(user=request.user).first()
    if not cart or cart.items.count() == 0:
        messages.warning(request, "Your shopping cart is empty. Add some products before checking out.")
        return redirect('cart:cart_detail')

    cart_items = cart.items.select_related('product').all()

    # Verify inventory availability before proceeding
    for item in cart_items:
        if not item.product.is_active or item.product.stock < item.quantity:
            messages.error(
                request, 
                f"Item '{item.product.name}' only has {item.product.stock} units available. Please adjust your cart."
            )
            return redirect('cart:cart_detail')

    subtotal = cart.subtotal
    free_shipping_threshold = Decimal(str(getattr(settings, 'FREE_SHIPPING_THRESHOLD', 999.00)))
    base_shipping_fee = Decimal(str(getattr(settings, 'SHIPPING_FEE', 49.00)))

    if subtotal >= free_shipping_threshold or subtotal == Decimal('0.00'):
        shipping_fee = Decimal('0.00')
    else:
        shipping_fee = base_shipping_fee

    tax_rate = Decimal(str(getattr(settings, 'TAX_RATE', 0.05)))
    tax_amount = round(subtotal * tax_rate, 2)

    # Check for coupon code in session
    applied_coupon_code = request.session.get('applied_coupon_code')
    coupon = None
    discount_amount = Decimal('0.00')

    if applied_coupon_code:
        coupon = Coupon.objects.filter(code__iexact=applied_coupon_code, is_active=True).first()
        if coupon:
            is_valid, msg = coupon.is_valid_for(subtotal)
            if is_valid:
                discount_amount = coupon.calculate_discount(subtotal)
            else:
                del request.session['applied_coupon_code']
                messages.warning(request, f"Coupon '{applied_coupon_code}' removed: {msg}")
                coupon = None
        else:
            del request.session['applied_coupon_code']

    grand_total = max(Decimal('0.00'), subtotal + shipping_fee + tax_amount - discount_amount)
    addresses = request.user.addresses.all()
    default_address = addresses.filter(is_default=True).first() or addresses.first()

    # Dynamic GPay UPI Deep Link & QR Code
    from urllib.parse import quote
    merchant_vpa = "shopsphere@okaxis"
    merchant_name = quote("ShopSphere Store")
    upi_intent_url = f"upi://pay?pa={merchant_vpa}&pn={merchant_name}&am={grand_total:.2f}&cu=INR&tn=ShopSphere_Order"
    upi_qr_code_url = f"https://api.qrserver.com/v1/create-qr-code/?size=260x260&margin=8&data={quote(upi_intent_url)}"

    context = {
        'cart': cart,
        'cart_items': cart_items,
        'addresses': addresses,
        'default_address': default_address,
        'subtotal': subtotal,
        'shipping_fee': shipping_fee,
        'tax_amount': tax_amount,
        'discount_amount': discount_amount,
        'grand_total': grand_total,
        'coupon': coupon,
        'upi_vpa': merchant_vpa,
        'upi_qr_code_url': upi_qr_code_url,
        'upi_intent_url': upi_intent_url,
    }
    return render(request, 'orders/checkout.html', context)


@login_required
def apply_coupon_view(request):
    """
    Validates and applies a coupon code stored in session.
    """
    if request.method == 'POST':
        code = request.POST.get('coupon_code', '').strip().upper()
        cart = Cart.objects.filter(user=request.user).first()
        if not cart or cart.items.count() == 0:
            messages.error(request, "Your cart is empty.")
            return redirect('cart:cart_detail')

        if not code:
            if 'applied_coupon_code' in request.session:
                del request.session['applied_coupon_code']
                messages.info(request, "Coupon removed.")
            return redirect('orders:checkout')

        coupon = Coupon.objects.filter(code__iexact=code).first()
        if not coupon:
            messages.error(request, f"Coupon code '{code}' is invalid.")
            return redirect('orders:checkout')

        is_valid, error_msg = coupon.is_valid_for(cart.subtotal)
        if not is_valid:
            messages.error(request, error_msg)
            return redirect('orders:checkout')

        request.session['applied_coupon_code'] = coupon.code
        messages.success(request, f"Coupon '{coupon.code}' applied successfully! Saved {coupon.get_discount_display()}.")

    return redirect('orders:checkout')


@login_required
def place_order_view(request):
    """
    Processes checkout and creates an Order with atomic database transaction.
    """
    if request.method != 'POST':
        return redirect('orders:checkout')

    cart = Cart.objects.filter(user=request.user).first()
    if not cart or cart.items.count() == 0:
        messages.error(request, "Your cart is empty. Cannot place order.")
        return redirect('cart:cart_detail')

    cart_items = list(cart.items.select_related('product').all())

    # Address determination
    address_id = request.POST.get('address_id')
    if address_id:
        address = get_object_or_404(Address, id=address_id, user=request.user)
        full_name = address.full_name
        phone = address.phone_number
        line1 = address.address_line1
        line2 = address.address_line2
        city = address.city
        state = address.state
        postal_code = address.postal_code
        country = address.country
    else:
        # User entered address fields directly
        full_name = request.POST.get('full_name', '').strip()
        phone = request.POST.get('phone_number', '').strip()
        line1 = request.POST.get('address_line1', '').strip()
        line2 = request.POST.get('address_line2', '').strip()
        city = request.POST.get('city', '').strip()
        state = request.POST.get('state', '').strip()
        postal_code = request.POST.get('postal_code', '').strip()
        country = request.POST.get('country', 'India').strip()

        if not all([full_name, phone, line1, city, state, postal_code]):
            messages.error(request, "Please fill in all required shipping address fields.")
            return redirect('orders:checkout')

        # Optionally save this address if requested
        if request.POST.get('save_address'):
            Address.objects.create(
                user=request.user,
                full_name=full_name,
                phone_number=phone,
                address_line1=line1,
                address_line2=line2,
                city=city,
                state=state,
                postal_code=postal_code,
                country=country,
                is_default=(request.user.addresses.count() == 0)
            )

    customer_notes = request.POST.get('customer_notes', '').strip()
    payment_method = request.POST.get('payment_method', 'cod')

    try:
        with transaction.atomic():
            # 1. Strict Stock Re-check and deduction
            for item in cart_items:
                # Lock row for update
                prod = Product.objects.select_for_update().get(id=item.product.id)
                if not prod.is_active:
                    raise ValueError(f"Product '{prod.name}' is no longer active.")
                if prod.stock < item.quantity:
                    raise ValueError(f"Insufficient stock for '{prod.name}'. Only {prod.stock} available.")
                
                # Deduct inventory
                prod.stock -= item.quantity
                prod.save(update_fields=['stock'])

            # 2. Strict Server-side Pricing calculations
            subtotal = cart.subtotal
            free_shipping_threshold = Decimal(str(getattr(settings, 'FREE_SHIPPING_THRESHOLD', 999.00)))
            base_shipping_fee = Decimal(str(getattr(settings, 'SHIPPING_FEE', 49.00)))

            if subtotal >= free_shipping_threshold or subtotal == Decimal('0.00'):
                shipping_fee = Decimal('0.00')
            else:
                shipping_fee = base_shipping_fee

            tax_rate = Decimal(str(getattr(settings, 'TAX_RATE', 0.05)))
            tax_amount = round(subtotal * tax_rate, 2)

            # Coupon calculation
            discount_amount = Decimal('0.00')
            coupon = None
            applied_code = request.session.get('applied_coupon_code')
            if applied_code:
                coupon = Coupon.objects.select_for_update().filter(code__iexact=applied_code, is_active=True).first()
                if coupon:
                    is_valid, _ = coupon.is_valid_for(subtotal)
                    if is_valid:
                        discount_amount = coupon.calculate_discount(subtotal)
                        coupon.used_count += 1
                        coupon.save(update_fields=['used_count'])
                    else:
                        coupon = None

            grand_total = max(Decimal('0.00'), subtotal + shipping_fee + tax_amount - discount_amount)

            # Payment status determination
            transaction_id = request.POST.get('transaction_id', '').strip()
            payment_status = 'unpaid'
            if payment_method == 'gpay':
                payment_status = 'pending_verification' if transaction_id else 'unpaid'

            # 3. Create Order
            order = Order.objects.create(
                order_number=generate_order_number(),
                user=request.user,
                shipping_full_name=full_name,
                shipping_phone=phone,
                shipping_address_line1=line1,
                shipping_address_line2=line2,
                shipping_city=city,
                shipping_state=state,
                shipping_postal_code=postal_code,
                shipping_country=country,
                status='pending',
                payment_method=payment_method,
                payment_status=payment_status,
                transaction_id=transaction_id if transaction_id else None,
                subtotal=subtotal,
                shipping_fee=shipping_fee,
                tax_amount=tax_amount,
                discount_amount=discount_amount,
                total_amount=grand_total,
                coupon=coupon,
                coupon_code_snapshot=coupon.code if coupon else None,
                customer_notes=customer_notes,
            )

            # 4. Create OrderItems snapshot
            for item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    product_name=item.product.name,
                    product_sku=item.product.sku,
                    product_image_url=item.product.cover_image.url if item.product.cover_image else None,
                    unit_price=item.product.price,
                    quantity=item.quantity,
                    total_price=item.total_price,
                )

            # 5. Clear Cart and Coupon Session
            cart.clear()
            if 'applied_coupon_code' in request.session:
                del request.session['applied_coupon_code']

            messages.success(request, f"Order #{order.order_number} has been placed successfully!")
            return redirect('orders:order_confirmation', order_number=order.order_number)

    except ValueError as e:
        messages.error(request, str(e))
        return redirect('cart:cart_detail')
    except Exception as e:
        messages.error(request, f"An unexpected error occurred while placing your order: {str(e)}")
        return redirect('orders:checkout')


@login_required
def order_confirmation_view(request, order_number):
    """
    Displays order confirmation and receipt directly after checkout.
    """
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    return render(request, 'orders/order_confirmation.html', {'order': order})


@login_required
def order_history_view(request):
    """
    Lists all previous orders placed by the current user.
    """
    orders = Order.objects.filter(user=request.user).prefetch_related('items').order_by('-created_at')
    return render(request, 'orders/order_history.html', {'orders': orders})


@login_required
def order_detail_view(request, order_number):
    """
    Full order invoice and status details for a customer.
    """
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    return render(request, 'orders/order_detail.html', {'order': order})


@login_required
def cancel_order_view(request, order_number):
    """
    Allows a customer to cancel their order if it is in pending or confirmed state.
    Restores inventory automatically.
    """
    order = get_object_or_404(Order, order_number=order_number, user=request.user)

    if request.method == 'POST':
        success, message = order.cancel_order()
        if success:
            messages.success(request, message)
        else:
            messages.error(request, message)
        return redirect('orders:order_detail', order_number=order.order_number)

    return render(request, 'orders/confirm_cancel_order.html', {'order': order})
