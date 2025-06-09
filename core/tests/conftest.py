import pytest
from django.conf import settings

def pytest_configure():
    settings.DEBUG = False
    settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
    settings.STRIPE_PUBLIC_KEY = 'pk_test_dummy'
    settings.STRIPE_SECRET_KEY = 'sk_test_dummy'
    settings.STRIPE_WEBHOOK_SECRET = 'whsec_dummy' 