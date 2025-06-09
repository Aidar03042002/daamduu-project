from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from ..models import User, EmailVerificationCode, MenuItem, Payment, ScanLog

class UserModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@manas.edu.kg',
            password='testpass123'
        )

    def test_user_creation(self):
        self.assertEqual(self.user.username, 'testuser')
        self.assertEqual(self.user.email, 'test@manas.edu.kg')
        self.assertTrue(self.user.check_password('testpass123'))
        self.assertEqual(self.user.role, 'USER')

    def test_user_str(self):
        self.assertEqual(str(self.user), 'testuser (USER)')

class EmailVerificationCodeTest(TestCase):
    def setUp(self):
        self.verification = EmailVerificationCode.objects.create(
            email='test@manas.edu.kg',
            code='123456'
        )

    def test_verification_creation(self):
        self.assertEqual(self.verification.email, 'test@manas.edu.kg')
        self.assertEqual(self.verification.code, '123456')
        self.assertFalse(self.verification.is_verified)
        self.assertIsNotNone(self.verification.verification_token)

    def test_verification_expiration(self):
        # Set expiration to past
        self.verification.expires_at = timezone.now() - timedelta(hours=1)
        self.verification.save()
        self.assertTrue(self.verification.is_expired())

        # Set expiration to future
        self.verification.expires_at = timezone.now() + timedelta(hours=1)
        self.verification.save()
        self.assertFalse(self.verification.is_expired())

class MenuItemTest(TestCase):
    def setUp(self):
        self.menu_item = MenuItem.objects.create(
            title='Test Item',
            description='Test Description',
            date=timezone.now().date()
        )

    def test_menu_item_creation(self):
        self.assertEqual(self.menu_item.title, 'Test Item')
        self.assertEqual(self.menu_item.description, 'Test Description')
        self.assertEqual(self.menu_item.date, timezone.now().date())

class PaymentTest(TestCase):
    def setUp(self):
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
        self.payment = Payment.objects.create(
            stripe_payment_intent='pi_test123',
            amount=1000,
            user=self.user,
            item=self.menu_item,
            transaction_id='tx_test123'
        )

    def test_payment_creation(self):
        self.assertEqual(self.payment.amount, 1000)
        self.assertEqual(self.payment.status, 'pending')
        self.assertEqual(self.payment.user, self.user)
        self.assertEqual(self.payment.item, self.menu_item)

    def test_payment_expiration(self):
        # Set expiration to past
        self.payment.expires_at = timezone.now() - timedelta(hours=1)
        self.payment.save()
        self.assertTrue(self.payment.is_expired())

        # Set expiration to future
        self.payment.expires_at = timezone.now() + timedelta(hours=1)
        self.payment.save()
        self.assertFalse(self.payment.is_expired())

class ScanLogTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@manas.edu.kg',
            password='testpass123'
        )
        self.scan_log = ScanLog.objects.create(
            code='test_code',
            scanner=self.user
        )

    def test_scan_log_creation(self):
        self.assertEqual(self.scan_log.code, 'test_code')
        self.assertEqual(self.scan_log.scanner, self.user)
        self.assertIsNotNone(self.scan_log.scanned_at) 