from django.test import TestCase, Client
from django.urls import reverse
from decimal import Decimal
from apps.catalog.models import Category, Product, ProductReview
from apps.accounts.models import User

class CatalogTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(name='Electronics', slug='electronics')
        self.user = User.objects.create_user(username='reviewer', email='rev@example.com', password='Password@123')

        self.product1 = Product.objects.create(
            category=self.category,
            name='Noise Cancelling Headphones',
            sku='TEST-NC-01',
            price=Decimal('199.99'),
            original_price=Decimal('249.99'),
            stock=15,
            is_active=True
        )
        self.product2 = Product.objects.create(
            category=self.category,
            name='Wireless Mouse',
            sku='TEST-WM-02',
            price=Decimal('29.99'),
            stock=0,  # Out of stock
            is_active=True
        )

    def test_product_list_view(self):
        url = reverse('catalog:product_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Noise Cancelling Headphones')
        self.assertContains(response, 'Wireless Mouse')

    def test_search_filtering(self):
        url = reverse('catalog:product_list')
        response = self.client.get(url, {'q': 'Headphones'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Noise Cancelling Headphones')
        self.assertNotContains(response, 'Wireless Mouse')

    def test_stock_filtering(self):
        url = reverse('catalog:product_list')
        response = self.client.get(url, {'in_stock': '1'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Noise Cancelling Headphones')
        self.assertNotContains(response, 'Wireless Mouse')

    def test_product_detail_view(self):
        url = reverse('catalog:product_detail', kwargs={'slug': self.product1.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.product1.name)
        self.assertContains(response, '₹199.99')

    def test_add_review_updates_product_rating(self):
        self.client.login(username='reviewer', password='Password@123')
        url = reverse('catalog:add_review', kwargs={'slug': self.product1.slug})
        response = self.client.post(url, {
            'rating': '5',
            'title': 'Outstanding Sound!',
            'comment': 'Best audio gear I have ever owned.'
        })
        self.assertEqual(response.status_code, 302)
        
        self.product1.refresh_from_db()
        self.assertEqual(self.product1.rating_count, 1)
        self.assertEqual(self.product1.rating_average, Decimal('5.00'))

    def test_search_suggestions_api(self):
        url = reverse('catalog:search_suggestions_api')
        response = self.client.get(url, {'q': 'Headphones'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('results', data)
        self.assertTrue(len(data['results']) >= 1)
        self.assertEqual(data['results'][0]['name'], 'Noise Cancelling Headphones')
