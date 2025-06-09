from django.db import models
from django.utils.timezone import now
from datetime import timedelta
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.conf import settings
import secrets

class User(AbstractUser):
    is_staff = models.BooleanField(default=False)
    is_student = models.BooleanField(default=True)

    class Role(models.TextChoices):
        USER = "USER", "Студент"
        ADMIN = "ADMIN", "Администратор"
        STAFF = "STAFF", "Контролёр"

    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.USER
    )

    def __str__(self):
        return f"{self.username} ({self.role})"

class EmailVerificationCode(models.Model):
    email = models.EmailField(db_index=True)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    is_verified = models.BooleanField(default=False)
    verification_token = models.CharField(max_length=100, unique=True, null=True)
    expires_at = models.DateTimeField()

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(hours=24)
        if not self.verification_token:
            self.verification_token = secrets.token_urlsafe(32)
        super().save(*args, **kwargs)

    def is_expired(self):
        return timezone.now() > self.expires_at

    def __str__(self):
        return f"{self.email} - {self.code}"

    class Meta:
        indexes = [
            models.Index(fields=['email', 'code']),
            models.Index(fields=['verification_token']),
        ]

class MenuItem(models.Model):
    name = models.CharField(max_length=200, default="Default Name")
    description = models.TextField(default="Описание временно отсутствует")
    price = models.DecimalField(max_digits=10, decimal_places=2, default=80)
    image = models.ImageField(upload_to='menu_items/', null=True, blank=True)
    date = models.DateField(default=timezone.now, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.date}"

    class Meta:
        indexes = [
            models.Index(fields=['date', 'created_at']),
        ]

class Payment(models.Model):
    stripe_payment_intent = models.CharField(max_length=255)
    amount = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    expires_at = models.DateTimeField(db_index=True)
    status = models.CharField(default='pending', max_length=50, db_index=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    item = models.ForeignKey('MenuItem', on_delete=models.CASCADE, null=True)
    transaction_id = models.CharField(max_length=255, unique=True, db_index=True)
    qr_code = models.TextField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(hours=24)
        super().save(*args, **kwargs)

    def is_expired(self):
        return timezone.now() > self.expires_at

    def __str__(self):
        return f"Payment {self.transaction_id} - {self.status}"

    class Meta:
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['created_at', 'status']),
        ]

class ScanLog(models.Model):
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, null=True, blank=True)
    scanned_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    scanned_at = models.DateTimeField(auto_now_add=True, db_index=True)
    status = models.CharField(max_length=20, choices=[
        ('success', 'Success'),
        ('invalid', 'Invalid'),
        ('used', 'Already Used')
    ], default='success')

    def __str__(self):
        return f"{self.payment.transaction_id if self.payment else 'No Tx'} - {self.scanned_by.username if self.scanned_by else 'Unknown'}"

    class Meta:
        indexes = [
            models.Index(fields=['scanner', 'scanned_at']),
        ]
