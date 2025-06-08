import stripe
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils.timezone import now
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import User, EmailVerificationCode, ScanLog, MenuItem, Payment
from .serializers import (
    EmailStartRegistrationSerializer,
    EmailVerifyCodeSerializer,
    UserListSerializer,
    ScanLogSerializer,
    MenuItemSerializer
)
import qrcode
from io import BytesIO
import base64
import json
from datetime import datetime

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

@login_required
def create_payment(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            item_id = data.get('item_id')
            item_name = data.get('item_name')
            price = data.get('price')

            # Create Stripe checkout session
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': item_name,
                        },
                        'unit_amount': int(price * 100),  # Convert to cents
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url=request.build_absolute_uri(f'/payment/success?item_id={item_id}'),
                cancel_url=request.build_absolute_uri('/payment/cancel'),
                metadata={
                    'item_id': item_id,
                    'user_id': request.user.id
                }
            )

            return JsonResponse({
                'success': True,
                'session_id': session.id
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@csrf_exempt
def stripe_webhook(request):
    if request.method == 'POST':
        payload = request.body
        sig_header = request.META['HTTP_STRIPE_SIGNATURE']

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
        except ValueError as e:
            return JsonResponse({'error': 'Invalid payload'}, status=400)
        except stripe.error.SignatureVerificationError as e:
            return JsonResponse({'error': 'Invalid signature'}, status=400)

        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            
            # Create payment record
            payment = Payment.objects.create(
                user_id=session['metadata']['user_id'],
                item_id=session['metadata']['item_id'],
                amount=session['amount_total'] / 100,  # Convert from cents
                transaction_id=session['payment_intent'],
                status='paid',
                created_at=datetime.fromtimestamp(session['created'])
            )

            # Generate QR code
            qr_data = {
                'transaction_id': payment.transaction_id,
                'item_id': payment.item_id,
                'user_id': payment.user_id,
                'timestamp': payment.created_at.isoformat()
            }
            
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(json.dumps(qr_data))
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Save QR code as base64
            buffered = BytesIO()
            img.save(buffered, format="PNG")
            qr_code = base64.b64encode(buffered.getvalue()).decode()
            
            payment.qr_code = qr_code
            payment.save()

        return JsonResponse({'status': 'success'})

@login_required
def payment_status(request, status):
    if status == 'success':
        item_id = request.GET.get('item_id')
        payment = Payment.objects.filter(
            user=request.user,
            item_id=item_id,
            status='paid'
        ).latest('created_at')
        
        return JsonResponse({
            'success': True,
            'transaction_id': payment.transaction_id,
            'qr_code': payment.qr_code
        })
    elif status == 'qr':
        transaction_id = request.path.split('/')[-1]
        payment = Payment.objects.get(transaction_id=transaction_id)
        return JsonResponse({
            'success': True,
            'qr_code': payment.qr_code
        })
    
    return JsonResponse({'success': False, 'message': 'Invalid status'})

@login_required
def scan_api(request):
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'message': 'Unauthorized'}, status=403)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            qr_data = json.loads(data['qr_data'])
            
            # Verify payment
            payment = Payment.objects.get(transaction_id=qr_data['transaction_id'])
            
            if payment.status != 'paid':
                return JsonResponse({
                    'success': False,
                    'message': 'Payment not completed'
                })
            
            # Check if QR code has been used
            if ScanLog.objects.filter(payment=payment).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'QR code already used'
                })
            
            # Create scan log
            ScanLog.objects.create(
                payment=payment,
                scanned_by=request.user,
                scanned_at=datetime.now()
            )
            
            return JsonResponse({
                'success': True,
                'transaction_id': payment.transaction_id,
                'status': 'verified'
            })
            
        except Payment.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Invalid transaction'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

def register_page(request):
    return render(request, 'register.html')

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

def login_view(request):
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect('staff')
        return redirect('home')
    return render(request, 'login.html')

@login_required
def home_view(request):
    if request.user.is_staff:
        return redirect('staff')
    return render(request, 'home.html')

@login_required
def staff_view(request):
    if not request.user.is_staff:
        return redirect('home')
    return render(request, 'staff.html')

@login_required
def admin_users_view(request):
    if not request.user.is_superuser:
        return redirect('home')
    return render(request, 'admin-users.html')

def generate_qr_code(transaction_data):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(transaction_data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64 for embedding in HTML
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return img_str
