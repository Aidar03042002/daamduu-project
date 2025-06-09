from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from ..models import User, EmailVerificationCode, MenuItem, Payment
import json

class AuthenticationTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@manas.edu.kg',
            password='testpass123'
        )

    def test_login(self):
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 302)  # Redirect after successful login

    def test_logout(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('logout'))
        self.assertEqual(response.status_code, 302)  # Redirect after logout

class EmailVerificationTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_email_registration(self):
        response = self.client.post(reverse('start-registration'), {
            'email': 'test@manas.edu.kg'
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(EmailVerificationCode.objects.filter(email='test@manas.edu.kg').exists())

    def test_email_verification(self):
        # Create verification code
        verification = EmailVerificationCode.objects.create(
            email='test@manas.edu.kg',
            code='123456'
        )
        
        # Verify code
        response = self.client.post(reverse('verify-code'), {
            'email': 'test@manas.edu.kg',
            'code': '123456',
            'username': 'testuser',
            'password': 'testpass123',
            'password2': 'testpass123'
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(User.objects.filter(username='testuser').exists())

class PaymentTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@manas.edu.kg',
            password='testpass123'
        )
        self.menu_item = MenuItem.objects.create(
            title='Test Item',
            description='Test Description',
            date=timezone.now().date()
        )
        self.client.login(username='testuser', password='testpass123')

    def test_create_payment(self):
        response = self.client.post(reverse('create-payment'), json.dumps({
            'item_id': self.menu_item.id,
            'item_name': 'Test Item',
            'price': 10.00
        }), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue('session_id' in data)

    def test_payment_status(self):
        payment = Payment.objects.create(
            stripe_payment_intent='pi_test123',
            amount=1000,
            user=self.user,
            item=self.menu_item,
            transaction_id='tx_test123',
            status='paid'
        )
        response = self.client.get(
            reverse('payment-status', args=['success']),
            {'item_id': self.menu_item.id}
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])

class MenuTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@manas.edu.kg',
            password='testpass123',
            is_staff=True
        )
        self.client.login(username='testuser', password='testpass123')

    def test_menu_list(self):
        response = self.client.get(reverse('menu-list-create'))
        self.assertEqual(response.status_code, 200)

    def test_menu_create(self):
        response = self.client.post(reverse('menu-list-create'), {
            'title': 'Test Item',
            'description': 'Test Description',
            'date': timezone.now().date()
        })
        self.assertEqual(response.status_code, 201)
        self.assertTrue(MenuItem.objects.filter(title='Test Item').exists())

    def test_menu_delete(self):
        menu_item = MenuItem.objects.create(
            title='Test Item',
            description='Test Description',
            date=timezone.now().date()
        )
        response = self.client.delete(reverse('menu-delete', args=[menu_item.id]))
        self.assertEqual(response.status_code, 204)
        self.assertFalse(MenuItem.objects.filter(id=menu_item.id).exists()) 