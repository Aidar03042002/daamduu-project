from django.db import models
from django.utils.timezone import now
from datetime import timedelta
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

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
    email = models.EmailField()
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        return now() > self.created_at + timedelta(minutes=10)

    def __str__(self):
        return f"{self.email} - {self.code}"

class MenuItem(models.Model):
    name = models.CharField(max_length=200, default="Default Name")
    description = models.TextField(default="Описание временно отсутствует")
    price = models.DecimalField(max_digits=10, decimal_places=2, default=80)
    image = models.ImageField(upload_to='menu_items/', null=True, blank=True)
    date = models.DateField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Payment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    item = models.ForeignKey(MenuItem, on_delete=models.CASCADE, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    transaction_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded')
    ], default='pending')
    qr_code = models.TextField(null=True, blank=True)  # Store QR code as base64 string
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username if self.user else 'Unknown User'} - {self.item.name if self.item else 'No Item'} - {self.amount}"

class ScanLog(models.Model):
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, null=True, blank=True)
    scanned_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    scanned_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[
        ('success', 'Success'),
        ('invalid', 'Invalid'),
        ('used', 'Already Used')
    ], default='success')

    def __str__(self):
        return f"{self.payment.transaction_id if self.payment else 'No Tx'} - {self.scanned_by.username if self.scanned_by else 'Unknown'}"
