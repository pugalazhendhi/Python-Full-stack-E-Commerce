from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.forms import PasswordChangeForm
from .forms import UserRegistrationForm, UserLoginForm, UserProfileUpdateForm, AddressForm
from .models import Address
from apps.cart.models import Cart, CartItem

def register_view(request):
    if request.user.is_authenticated:
        return redirect('catalog:home')

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f"Welcome to ShopSphere, {user.first_name or user.username}! Your account has been created successfully.")
            login(request, user)
            # Merge any anonymous cart items
            merge_guest_cart(request, user)
            return redirect('catalog:home')
        else:
            messages.error(request, "Please correct the errors in the registration form.")
    else:
        form = UserRegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('catalog:home')

    next_url = request.GET.get('next', 'catalog:home')

    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.first_name or user.username}!")
            # Merge guest cart
            merge_guest_cart(request, user)
            return redirect(next_url if next_url and next_url.startswith('/') else 'catalog:home')
        else:
            messages.error(request, "Invalid username or password. Please try again.")
    else:
        form = UserLoginForm()

    return render(request, 'accounts/login.html', {'form': form, 'next': next_url})


def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out safely.")
    return redirect('catalog:home')


@login_required
def profile_view(request):
    recent_orders = request.user.orders.all()[:5]
    addresses = request.user.addresses.all()
    return render(request, 'accounts/profile.html', {
        'recent_orders': recent_orders,
        'addresses': addresses,
    })


@login_required
def edit_profile_view(request):
    if request.method == 'POST':
        form = UserProfileUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile information has been updated successfully.")
            return redirect('accounts:profile')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = UserProfileUpdateForm(instance=request.user)

    return render(request, 'accounts/edit_profile.html', {'form': form})


@login_required
def change_password_view(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Your password was successfully updated!")
            return redirect('accounts:profile')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = PasswordChangeForm(request.user)

    return render(request, 'accounts/change_password.html', {'form': form})


@login_required
def address_list_view(request):
    addresses = request.user.addresses.all()
    return render(request, 'accounts/addresses.html', {'addresses': addresses})


@login_required
def add_address_view(request):
    next_url = request.GET.get('next')
    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            # If user has no existing addresses, make this default
            if not request.user.addresses.exists():
                address.is_default = True
            address.save()
            messages.success(request, "New address added successfully.")
            if next_url:
                return redirect(next_url)
            return redirect('accounts:address_list')
        else:
            messages.error(request, "Please correct the errors in the address form.")
    else:
        form = AddressForm()

    return render(request, 'accounts/address_form.html', {'form': form, 'title': 'Add New Address'})


@login_required
def edit_address_view(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)
    if request.method == 'POST':
        form = AddressForm(request.POST, instance=address)
        if form.is_valid():
            form.save()
            messages.success(request, "Address updated successfully.")
            return redirect('accounts:address_list')
        else:
            messages.error(request, "Please correct the errors in the address form.")
    else:
        form = AddressForm(instance=address)

    return render(request, 'accounts/address_form.html', {'form': form, 'title': 'Edit Address'})


@login_required
def delete_address_view(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)
    if request.method == 'POST':
        was_default = address.is_default
        address.delete()
        if was_default:
            next_addr = request.user.addresses.first()
            if next_addr:
                next_addr.is_default = True
                next_addr.save()
        messages.success(request, "Address removed successfully.")
        return redirect('accounts:address_list')

    return render(request, 'accounts/confirm_delete_address.html', {'address': address})


@login_required
def set_default_address_view(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)
    address.is_default = True
    address.save()
    messages.success(request, f"'{address.address_line1}' is now your default shipping address.")
    next_url = request.GET.get('next', 'accounts:address_list')
    return redirect(next_url)


def merge_guest_cart(request, user):
    """
    Transfers items from an anonymous session cart to the logged-in user cart.
    """
    session_key = request.session.session_key
    if not session_key:
        return

    guest_cart = Cart.objects.filter(session_key=session_key).first()
    if not guest_cart:
        return

    user_cart, _ = Cart.objects.get_or_create(user=user)

    for item in guest_cart.items.all():
        existing_item = user_cart.items.filter(product=item.product).first()
        if existing_item:
            # Respect product stock limit
            new_qty = min(existing_item.quantity + item.quantity, item.product.stock)
            existing_item.quantity = new_qty
            existing_item.save()
        else:
            item.cart = user_cart
            # Don't exceed stock
            if item.quantity > item.product.stock:
                item.quantity = max(1, item.product.stock)
            item.save()

    # Clear guest cart
    guest_cart.delete()
