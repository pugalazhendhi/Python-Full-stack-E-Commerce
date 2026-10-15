from django.test import TestCase, Client
from django.urls import reverse
from decimal import Decimal
from apps.catalog.models import Category, Product
from apps.cart.models import Cart, CartItem
from apps.accounts.models import User

class CartTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(name='Tech', slug='tech')
        self.user = User.objects.create_user(username='cartuser', email='cart@example.com', password='Password@123')

        self.in_stock_product = Product.objects.create(
            category=self.category,
            name='Mechanical Keyboard',
            sku='KB-001',
            price=Decimal('100.00'),
            stock=5,
            is_active=True
        )
        self.out_of_stock_product = Product.objects.create(
            category=self.category,
            name='Vintage Keycaps',
            sku='KC-002',
            price=Decimal('40.00'),
            stock=0,
            is_active=True
        )

    def test_add_to_cart_success(self):
        self.client.login(username='cartuser', password='Password@123')
        url = reverse('cart:add_to_cart', kwargs={'product_id': self.in_stock_product.id})
        response = self.client.post(url, {'quantity': 2})
        self.assertEqual(response.status_code, 302)

        cart = Cart.objects.get(user=self.user)
        self.assertEqual(cart.total_items, 2)
        self.assertEqual(cart.subtotal, Decimal('200.00'))

    def test_add_out_of_stock_rejected(self):
        self.client.login(username='cartuser', password='Password@123')
        url = reverse('cart:add_to_cart', kwargs={'product_id': self.out_of_stock_product.id})
        response = self.client.post(url, {'quantity': 1})
        self.assertEqual(response.status_code, 302)

        cart = Cart.objects.filter(user=self.user).first()
        if cart:
            self.assertEqual(cart.total_items, 0)

    def test_add_exceeding_stock_capped_at_available(self):
        self.client.login(username='cartuser', password='Password@123')
        url = reverse('cart:add_to_cart', kwargs={'product_id': self.in_stock_product.id})
        # Try to order 10 when stock is only 5
        response = self.client.post(url, {'quantity': 10})
        self.assertEqual(response.status_code, 302)

        cart = Cart.objects.get(user=self.user)
        item = cart.items.get(product=self.in_stock_product)
        self.assertEqual(item.quantity, 5)

    def test_update_cart_item_quantity(self):
        self.client.login(username='cartuser', password='Password@123')
        cart = Cart.objects.create(user=self.user)
        item = CartItem.objects.create(cart=cart, product=self.in_stock_product, quantity=1)

        url = reverse('cart:update_cart_item', kwargs={'item_id': item.id})
        response = self.client.post(url, {'quantity': 3})
        self.assertEqual(response.status_code, 302)

        item.refresh_from_db()
        self.assertEqual(item.quantity, 3)
        self.assertEqual(item.total_price, Decimal('300.00'))

    def test_remove_cart_item(self):
        self.client.login(username='cartuser', password='Password@123')
        cart = Cart.objects.create(user=self.user)
        item = CartItem.objects.create(cart=cart, product=self.in_stock_product, quantity=1)

        url = reverse('cart:remove_cart_item', kwargs={'item_id': item.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(cart.items.count(), 0)

    def test_ajax_add_to_cart(self):
        url = reverse('cart:add_to_cart', kwargs={'product_id': self.in_stock_product.id})
        response = self.client.post(url, {'quantity': 1}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['cart_count'], 1)
