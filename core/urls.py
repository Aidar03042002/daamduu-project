from django.urls import path, include
from django.views.generic import TemplateView
from . import views

urlpatterns = [
    path('', TemplateView.as_view(template_name="index.html"), name='index'),  # Root now serves index.html
    path("register/", views.register_page, name="register"),
    path("create-payment/", views.create_payment, name="create-payment"),
    path("stripe/webhook/", views.stripe_webhook, name="stripe-webhook"),
    path("payment/<str:status>/", views.payment_status, name="payment-status"),
    path("start-registration/", views.EmailStartRegistrationView.as_view(), name="start-registration"),
    path("verify-code/", views.EmailVerifyCodeView.as_view(), name="verify-code"),
    path("menu/", views.MenuListCreateView.as_view(), name="menu-list-create"),
    path("menu/<int:pk>/", views.MenuDeleteView.as_view(), name="menu-delete"),
    path("menu/today/", views.TodayMenuView.as_view(), name="menu-today"),
    path("scan/", views.ScanAPIView.as_view(), name="scan-api"),
    path("oauth/", include("social_django.urls", namespace="social")),
    path("login/", views.login_view, name="login"),  # Changed to use view function for auth check
    path("home/", views.home_view, name="home"),  # Changed to use view function for auth check
    path("about/", TemplateView.as_view(template_name="hakkimizda.html"), name="about"),
    path("team/", TemplateView.as_view(template_name="takim.html"), name="team"),
    path("reset-password/", TemplateView.as_view(template_name="reset-password.html"), name="reset-password"),
    path("admin-login/", TemplateView.as_view(template_name="admin-login.html"), name="admin-login"),
    path("reset-password-admin/", TemplateView.as_view(template_name="reset-password-admin.html"),
         name="reset-password-admin"),
    path("admin-panel/", TemplateView.as_view(template_name="admin.html"), name="admin-panel"),
    path("admin-menu/", TemplateView.as_view(template_name="admin-menu.html"), name="admin-menu"),
    path("admin-qr/", TemplateView.as_view(template_name="admin-qr-tarayici.html"), name="admin-qr"),
    path("bugun-menu/", TemplateView.as_view(template_name="bugun-menu.html"), name="bugun-menu"),
    path("haftalik-menu/", TemplateView.as_view(template_name="haftalik-menu.html"), name="haftalik-menu"),
    path("staff/", views.staff_view, name="staff"),  # New staff page
    path("admin-users/", views.admin_users_view, name="admin-users"),  # New admin users page
]
