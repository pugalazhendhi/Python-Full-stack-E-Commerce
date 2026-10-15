from django.test import TestCase, Client
from django.urls import reverse
from apps.accounts.models import User, Address

class AccountsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='Password@123',
            first_name='Test',
            last_name='User'
        )

    def test_user_registration_success(self):
        url = reverse('accounts:register')
        response = self.client.post(url, {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'first_name': 'New',
            'last_name': 'Person',
            'phone_number': '1234567890',
            'password': 'StrongPassword@123',
            'confirm_password': 'StrongPassword@123',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_registration_duplicate_email(self):
        url = reverse('accounts:register')
        response = self.client.post(url, {
            'username': 'anotheruser',
            'email': 'testuser@example.com',  # Existing email
            'password': 'StrongPassword@123',
            'confirm_password': 'StrongPassword@123',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='anotheruser').exists())

    def test_registration_password_mismatch(self):
        url = reverse('accounts:register')
        response = self.client.post(url, {
            'username': 'anotheruser',
            'email': 'unique@example.com',
            'password': 'PasswordOne123',
            'confirm_password': 'PasswordTwo123',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='anotheruser').exists())

    def test_user_login_and_logout(self):
        login_url = reverse('accounts:login')
        response = self.client.post(login_url, {
            'username': 'testuser',
            'password': 'Password@123',
        })
        self.assertEqual(response.status_code, 302)

        logout_url = reverse('accounts:logout')
        response = self.client.get(logout_url)
        self.assertEqual(response.status_code, 302)

    def test_address_management_and_default_toggle(self):
        self.client.login(username='testuser', password='Password@123')
        
        # Add Address 1 (should become default automatically)
        addr1 = Address.objects.create(
            user=self.user,
            full_name="Test User",
            phone_number="555-1234",
            address_line1="123 Main St",
            city="Metropolis",
            state="NY",
            postal_code="10001",
            is_default=True
        )
        self.assertTrue(addr1.is_default)

        # Add Address 2 set as default
        addr2 = Address.objects.create(
            user=self.user,
            full_name="Test User Work",
            phone_number="555-5678",
            address_line1="456 Market St",
            city="Metropolis",
            state="NY",
            postal_code="10002",
            is_default=True
        )
        # Check that addr1 is no longer default
        addr1.refresh_from_db()
        self.assertFalse(addr1.is_default)
        self.assertTrue(addr2.is_default)
