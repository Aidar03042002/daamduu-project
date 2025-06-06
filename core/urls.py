from django.urls import path, include
from django.views.generic import TemplateView
from . import views

urlpatterns = [
    path("create-payment/", views.create_payment, name="create-payment"),
    path("stripe/webhook/", views.stripe_webhook, name="stripe-webhook"),
    path("start-registration/", views.EmailStartRegistrationView.as_view(), name="start-registration"),
    path("verify-code/", views.EmailVerifyCodeView.as_view(), name="verify-code"),
    path("menu/", views.MenuListCreateView.as_view(), name="menu-list-create"),
    path("menu/<int:pk>/", views.MenuDeleteView.as_view(), name="menu-delete"),
    path("menu/today/", views.TodayMenuView.as_view(), name="menu-today"),
    path("scan/", views.ScanAPIView.as_view(), name="scan-api"),
    path("oauth/", include("social_django.urls", namespace="social")),
    path("login/", TemplateView.as_view(template_name="login.html"), name="login"),
]
