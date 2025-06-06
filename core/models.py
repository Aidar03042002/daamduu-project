from django.db import models
from django.utils.timezone import now, timedelta
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
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
    scanner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='scans')
    code = models.CharField(max_length=255)
    scanned_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.scanner.username} → {self.code} @ {self.scanned_at}"

class MenuItem(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.date})"

class Payment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    stripe_payment_intent = models.CharField(max_length=255)
    amount = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, default="pending")

    def __str__(self):
        return f"{self.user.username} - {self.amount} - {self.status}"
