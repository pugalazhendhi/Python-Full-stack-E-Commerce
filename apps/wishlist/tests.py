from django.test import TestCase, Client
from django.urls import reverse
from decimal import Decimal
from apps.catalog.models import Category, Product
from apps.wishlist.models import Wishlist, WishlistItem
from apps.cart.models import Cart
from apps.accounts.models import User

class WishlistTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='wishuser', email='wish@example.com', password='Password@123')
        self.category = Category.objects.create(name='Fashion', slug='fashion')
        self.product = Product.objects.create(
            category=self.category,
            name='Silk Scarf',
            sku='FA-SC-01',
            price=Decimal('50.00'),
            stock=10,
            is_active=True
        )

    def test_toggle_wishlist(self):
        self.client.login(username='wishuser', password='Password@123')
        url = reverse('wishlist:toggle_wishlist', kwargs={'product_id': self.product.id})
        
        # 1. Add to wishlist
        response = self.client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['action'], 'added')
        self.assertEqual(data['wishlist_count'], 1)

        # 2. Toggle again to remove
        response = self.client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['action'], 'removed')
        self.assertEqual(data['wishlist_count'], 0)

    def test_move_wishlist_to_cart(self):
        self.client.login(username='wishuser', password='Password@123')
        wishlist = Wishlist.objects.create(user=self.user)
        WishlistItem.objects.create(wishlist=wishlist, product=self.product)

        url = reverse('wishlist:move_to_cart', kwargs={'product_id': self.product.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

        # Wishlist should now be empty
        self.assertEqual(wishlist.items.count(), 0)

        # Cart should now contain product
        cart = Cart.objects.get(user=self.user)
        self.assertEqual(cart.items.filter(product=self.product).count(), 1)
