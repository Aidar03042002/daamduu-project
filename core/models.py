from django.db import models
from django.utils.timezone import now, timedelta
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

class ScanLog(models.Model):
    payment = models.ForeignKey('Payment', on_delete=models.CASCADE)
    scanned_by = models.ForeignKey(User, on_delete=models.CASCADE)
    scanned_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[
        ('success', 'Success'),
        ('invalid', 'Invalid'),
        ('used', 'Already Used')
    ], default='success')

    def __str__(self):
        return f"{self.payment.transaction_id} - {self.scanned_by.username}"

class MenuItem(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='menu_items/', null=True, blank=True)
    date = models.DateField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Payment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    item = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_id = models.CharField(max_length=255, unique=True)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded')
    ])
    qr_code = models.TextField(null=True, blank=True)  # Store QR code as base64 string
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.item.name} - {self.amount}"
