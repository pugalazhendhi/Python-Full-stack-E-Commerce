from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from decimal import Decimal
from apps.catalog.models import Category, Product
from apps.cart.models import Cart, CartItem
from apps.orders.models import Order, OrderItem, Coupon
from apps.accounts.models import User, Address

class OrdersTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(username='buyer1', email='buyer1@example.com', password='Password@123')
        self.user2 = User.objects.create_user(username='buyer2', email='buyer2@example.com', password='Password@123')

        self.category = Category.objects.create(name='Home', slug='home')
        self.product = Product.objects.create(
            category=self.category,
            name='Coffee Brewer',
            sku='CB-101',
            price=Decimal('100.00'),
            stock=10,
            is_active=True
        )

        self.address = Address.objects.create(
            user=self.user1,
            full_name="Buyer One",
            phone_number="555-1111",
            address_line1="100 Main St",
            city="Seattle",
            state="WA",
            postal_code="98101",
            country="United States",
            is_default=True
        )

        self.coupon = Coupon.objects.create(
            code='SAVE10',
            discount_type='percentage',
            discount_value=Decimal('10.00'),
            min_purchase_amount=Decimal('50.00'),
            valid_to=timezone.now() + timezone.timedelta(days=30),
            is_active=True
        )

    def test_coupon_calculation(self):
        # Valid subtotal
        valid, _ = self.coupon.is_valid_for(Decimal('100.00'))
        self.assertTrue(valid)
        self.assertEqual(self.coupon.calculate_discount(Decimal('100.00')), Decimal('10.00'))

        # Subtotal below threshold
        valid, msg = self.coupon.is_valid_for(Decimal('30.00'))
        self.assertFalse(valid)

    def test_checkout_requires_login(self):
        url = reverse('orders:checkout')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('accounts:login'), response.url)

    def test_place_order_atomic_inventory_deduction(self):
        self.client.login(username='buyer1', password='Password@123')
        
        # Add product to cart
        cart = Cart.objects.create(user=self.user1)
        CartItem.objects.create(cart=cart, product=self.product, quantity=2)

        url = reverse('orders:place_order')
        response = self.client.post(url, {
            'address_id': self.address.id,
            'payment_method': 'cod',
            'customer_notes': 'Handle with care'
        })
        self.assertEqual(response.status_code, 302)

        # Verify Order created
        order = Order.objects.filter(user=self.user1).first()
        self.assertIsNotNone(order)
        self.assertEqual(order.items.count(), 1)
        self.assertEqual(order.status, 'pending')

        # Verify Snapshot integrity
        item_snap = order.items.first()
        self.assertEqual(item_snap.product_name, 'Coffee Brewer')
        self.assertEqual(item_snap.quantity, 2)
        self.assertEqual(item_snap.unit_price, Decimal('100.00'))
        self.assertEqual(item_snap.total_price, Decimal('200.00'))

        # Verify stock was deducted: 10 - 2 = 8
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 8)

        # Verify cart was cleared
        self.assertEqual(cart.items.count(), 0)

    def test_order_cancellation_restores_inventory(self):
        self.client.login(username='buyer1', password='Password@123')
        
        # Create order directly
        order = Order.objects.create(
            order_number='ORD-TEST-001',
            user=self.user1,
            shipping_full_name="Buyer One",
            shipping_phone="555-1111",
            shipping_address_line1="100 Main St",
            shipping_city="Seattle",
            shipping_state="WA",
            shipping_postal_code="98101",
            subtotal=Decimal('100.00'),
            total_amount=Decimal('100.00'),
            status='pending'
        )
        OrderItem.objects.create(
            order=order,
            product=self.product,
            product_name=self.product.name,
            unit_price=self.product.price,
            quantity=3,
            total_price=Decimal('300.00')
        )
        self.product.stock = 7
        self.product.save()

        # Cancel order
        success, _ = order.cancel_order()
        self.assertTrue(success)
        self.assertEqual(order.status, 'cancelled')

        # Stock should be restored: 7 + 3 = 10
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 10)

    def test_order_ownership_security(self):
        # Create order for user1
        order = Order.objects.create(
            order_number='ORD-PRIVATE-99',
            user=self.user1,
            shipping_full_name="Buyer One",
            shipping_phone="555-1111",
            shipping_address_line1="100 Main St",
            shipping_city="Seattle",
            shipping_state="WA",
            shipping_postal_code="98101",
            subtotal=Decimal('100.00'),
            total_amount=Decimal('100.00'),
            status='pending'
        )

        # Log in as user2
        self.client.login(username='buyer2', password='Password@123')
        url = reverse('orders:order_detail', kwargs={'order_number': order.order_number})
        response = self.client.get(url)
        # Should return 404 (user2 is not allowed to view user1's order)
        self.assertEqual(response.status_code, 404)
