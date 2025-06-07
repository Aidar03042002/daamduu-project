import stripe
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils.timezone import now
from django.shortcuts import render
from .models import User, EmailVerificationCode, ScanLog, MenuItem, Payment
from .serializers import (
    EmailStartRegistrationSerializer,
    EmailVerifyCodeSerializer,
    UserListSerializer,
    ScanLogSerializer,
    MenuItemSerializer
)

stripe.api_key = settings.STRIPE_SECRET_KEY

def payment_status(request, status):
    """
    Handle all payment statuses in a single view
    status can be: success, failure, pending, refund, refund_success, refund_failure,
    refund_pending, refund_cancel, refund_cancel_success, refund_cancel_failure,
    refund_cancel_pending
    """
    status_messages = {
        'success': 'Ödemeniz başarıyla tamamlandı.',
        'failure': 'Ödeme işlemi sırasında bir hata oluştu.',
        'pending': 'Ödemeniz işleme alındı, lütfen bekleyin.',
        'refund': 'İade talebiniz alındı.',
        'refund_success': 'İade işleminiz başarıyla tamamlandı.',
        'refund_failure': 'İade işlemi sırasında bir hata oluştu.',
        'refund_pending': 'İade talebiniz işleme alındı, lütfen bekleyin.',
        'refund_cancel': 'İade talebiniz iptal edildi.',
        'refund_cancel_success': 'İade iptal işleminiz başarıyla tamamlandı.',
        'refund_cancel_failure': 'İade iptal işlemi sırasında bir hata oluştu.',
        'refund_cancel_pending': 'İade iptal talebiniz işleme alındı, lütfen bekleyin.'
    }
    
    return render(request, 'odeme.html', {
        'status': status,
        'message': status_messages.get(status, 'Bilinmeyen bir durum oluştu.')
    })

@csrf_exempt
def create_payment(request):
    if request.method == "POST":
        try:
            intent = stripe.PaymentIntent.create(
                amount=8000,
                currency='kgs',
                payment_method_types=['card'],
            )
            return JsonResponse({'clientSecret': intent.client_secret})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

    if event['type'] == 'payment_intent.succeeded':
        intent = event['data']['object']
        Payment.objects.create(
            user=None,  # Will be updated when user authentication is implemented
            stripe_payment_intent=intent['id'],
            amount=intent['amount'],
            status='succeeded'
        )
    elif event['type'] == 'payment_intent.payment_failed':
        intent = event['data']['object']
        Payment.objects.create(
            user=None,
            stripe_payment_intent=intent['id'],
            amount=intent['amount'],
            status='failed'
        )
    elif event['type'] == 'charge.refunded':
        intent = event['data']['object']
        payment = Payment.objects.get(stripe_payment_intent=intent['payment_intent'])
        payment.status = 'refunded'
        payment.save()

    return JsonResponse({'status': 'success'})

def register_page(request):
    return render(request, 'daamduu/register.html')

class EmailStartRegistrationView(APIView):
    def post(self, request):
        serializer = EmailStartRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            if not email.endswith("@manas.edu.kg"):
                return Response({"error": "Только почты manas.edu.kg разрешены"}, status=400)
            code = "123456"  # Генерация кода позже
            EmailVerificationCode.objects.create(email=email, code=code)
            return Response({"detail": "Код отправлен (симуляция)"})
        return Response(serializer.errors, status=400)

class EmailVerifyCodeView(APIView):
    def post(self, request):
        serializer = EmailVerifyCodeSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            code = serializer.validated_data['code']
            username = serializer.validated_data['username']
            password = serializer.validated_data['password']
            check = EmailVerificationCode.objects.filter(email=email, code=code).first()
            if not check or check.is_expired():
                return Response({"error": "Неверный или истекший код"}, status=400)
            user = User.objects.create_user(username=username, email=email, password=password)
            user.save()
            return Response({"detail": "Регистрация успешна"})
        return Response(serializer.errors, status=400)

# Остальные API (сканирование, меню)
class ScanAPIView(generics.CreateAPIView):
    queryset = ScanLog.objects.all()
    serializer_class = ScanLogSerializer
    permission_classes = [permissions.IsAuthenticated]

class MenuListCreateView(generics.ListCreateAPIView):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer

class MenuDeleteView(generics.DestroyAPIView):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    permission_classes = [permissions.IsAuthenticated]

class TodayMenuView(generics.ListAPIView):
    serializer_class = MenuItemSerializer
    def get_queryset(self):
        return MenuItem.objects.filter(date=now().date())
