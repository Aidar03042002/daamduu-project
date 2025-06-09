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
from django.contrib.auth import login, logout
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
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from rest_framework.pagination import PageNumberPagination
import secrets
import string
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.contrib.auth.password_validation import validate_password
from .schemas import (
    error_response, success_response, menu_item_schema,
    payment_schema, payment_response_schema,
    email_verification_schema, verification_code_schema,
    scan_schema, scan_response_schema
)
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

stripe.api_key = settings.STRIPE_SECRET_KEY

def payment_status(request, status):
    """
    Handle all payment statuses in a single view
    status can be: success, failure, pending, refund, refund_success, refund_failure,
    refund_pending, refund_cancel, refund_cancel_success, refund_cancel_failure,
    refund_cancel_pending
    """
    if status == 'success':
        item_id = request.GET.get('item_id')
        try:
            payment = Payment.objects.filter(
                user=request.user,
                item_id=item_id,
                status='paid'
            ).latest('created_at')
            
            if payment.is_expired():
                return JsonResponse({
                    'success': False,
                    'message': 'Payment has expired'
                }, status=400)
            
            return JsonResponse({
                'success': True,
                'transaction_id': payment.transaction_id,
                'qr_code': payment.qr_code
            })
        except Payment.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Payment not found'
            })
    elif status == 'qr':
        transaction_id = request.path.split('/')[-1]
        try:
            payment = Payment.objects.get(transaction_id=transaction_id)
            if payment.is_expired():
                return JsonResponse({
                    'success': False,
                    'message': 'Payment has expired'
                }, status=400)
            return JsonResponse({
                'success': True,
                'qr_code': payment.qr_code
            })
        except Payment.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Invalid transaction'
            })
    
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

@swagger_auto_schema(
    method='post',
    request_body=payment_schema,
    responses={
        200: payment_response_schema,
        400: error_response
    },
    operation_description="Create a new payment"
)
@login_required
def create_payment(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=405)
        
    try:
        data = json.loads(request.body)
        
        # Validate required fields
        required_fields = ['item_id', 'item_name', 'price']
        if not all(field in data for field in required_fields):
            return JsonResponse({
                'success': False,
                'message': 'Missing required fields'
            }, status=400)
            
        # Validate price
        try:
            price = float(data['price'])
            if price <= 0:
                raise ValueError("Price must be positive")
        except (ValueError, TypeError):
            return JsonResponse({
                'success': False,
                'message': 'Invalid price value'
            }, status=400)
            
        # Validate item exists
        try:
            item = MenuItem.objects.get(id=data['item_id'])
        except MenuItem.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Item not found'
            }, status=404)

        # Create Stripe checkout session
        try:
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': data['item_name'],
                        },
                        'unit_amount': int(price * 100),  # Convert to cents
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url=request.build_absolute_uri(f'/payment/success?item_id={data["item_id"]}'),
                cancel_url=request.build_absolute_uri('/payment/cancel'),
                metadata={
                    'item_id': data['item_id'],
                    'user_id': request.user.id
                }
            )

            return JsonResponse({
                'success': True,
                'session_id': session.id
            })
        except stripe.error.StripeError as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=400)
            
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)

@csrf_exempt
def stripe_webhook(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
        
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    if not sig_header:
        return JsonResponse({'error': 'No signature header'}, status=400)

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        return JsonResponse({'error': 'Invalid payload'}, status=400)
    except stripe.error.SignatureVerificationError as e:
        return JsonResponse({'error': 'Invalid signature'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

    try:
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            
            # Validate required metadata
            if not all(key in session['metadata'] for key in ['user_id', 'item_id']):
                return JsonResponse({'error': 'Missing required metadata'}, status=400)
            
            # Create payment record
            payment = Payment.objects.create(
                user_id=session['metadata']['user_id'],
                item_id=session['metadata']['item_id'],
                amount=session['amount_total'] / 100,  # Convert from cents
                transaction_id=session['payment_intent'],
                status='paid',
                created_at=datetime.fromtimestamp(session['created'])
            )

            # Generate QR code in a background task
            cache_key = f'qr_generation_{payment.id}'
            if not cache.get(cache_key):
                try:
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
                    
                    # Set cache to prevent duplicate generation
                    cache.set(cache_key, True, timeout=3600)  # Cache for 1 hour
                except Exception as e:
                    # Log the error but don't fail the webhook
                    print(f"Error generating QR code: {str(e)}")
                    # You might want to add proper logging here

        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

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
    @swagger_auto_schema(
        request_body=email_verification_schema,
        responses={
            200: success_response,
            400: error_response
        },
        operation_description="Start email registration process"
    )
    def post(self, request):
        serializer = EmailStartRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            if not email.endswith("@manas.edu.kg"):
                return Response({"error": "Только почты manas.edu.kg разрешены"}, status=400)
                
            # Generate a secure random code
            code = ''.join(secrets.choice(string.digits) for _ in range(6))
            
            # Delete any existing codes for this email
            EmailVerificationCode.objects.filter(email=email).delete()
            
            # Create new verification code
            verification = EmailVerificationCode.objects.create(
                email=email,
                code=code
            )
            
            # Send verification email
            subject = 'Подтверждение регистрации'
            verification_link = request.build_absolute_uri(
                f'/verify-email/{verification.verification_token}/'
            )
            message = render_to_string('email_verification.html', {
                'code': code,
                'verification_link': verification_link,
            })
            
            if settings.DEBUG:
                print(f"Verification code: {code}")
                print(f"Verification link: {verification_link}")
            else:
                send_mail(
                    subject,
                    message,
                    settings.EMAIL_HOST_USER,
                    [email],
                    fail_silently=False,
                )
                
            return Response({"detail": "Код подтверждения отправлен на вашу почту"})
        return Response(serializer.errors, status=400)

class EmailVerifyCodeView(APIView):
    @swagger_auto_schema(
        request_body=verification_code_schema,
        responses={
            200: success_response,
            400: error_response
        },
        operation_description="Verify email code and complete registration"
    )
    def post(self, request):
        serializer = EmailVerifyCodeSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            code = serializer.validated_data['code']
            username = serializer.validated_data['username']
            password = serializer.validated_data['password']
            
            verification = EmailVerificationCode.objects.filter(
                email=email,
                code=code,
                is_verified=False
            ).first()
            
            if not verification:
                return Response({"error": "Неверный код подтверждения"}, status=400)
                
            if verification.is_expired():
                return Response({"error": "Срок действия кода истек"}, status=400)
                
            # Create user
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password
            )
            
            # Mark verification as complete
            verification.is_verified = True
            verification.save()
            
            return Response({"detail": "Регистрация успешно завершена"})
        return Response(serializer.errors, status=400)

def verify_email(request, token):
    try:
        verification = EmailVerificationCode.objects.get(
            verification_token=token,
            is_verified=False
        )
        
        if verification.is_expired():
            return JsonResponse({
                "error": "Срок действия ссылки истек"
            }, status=400)
            
        verification.is_verified = True
        verification.save()
        
        return JsonResponse({
            "detail": "Email успешно подтвержден"
        })
    except EmailVerificationCode.DoesNotExist:
        return JsonResponse({
            "error": "Недействительная ссылка подтверждения"
        }, status=400)

# Остальные API (сканирование, меню)
class ScanAPIView(generics.CreateAPIView):
    queryset = ScanLog.objects.all()
    serializer_class = ScanLogSerializer
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        request_body=scan_schema,
        responses={
            201: scan_response_schema,
            400: error_response
        },
        operation_description="Scan a QR code"
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

class MenuListCreateView(generics.ListCreateAPIView):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    pagination_class = PageNumberPagination
    
    @swagger_auto_schema(
        responses={
            200: openapi.Response(
                description="List of menu items",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'count': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'next': openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
                        'previous': openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
                        'results': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=menu_item_schema
                        )
                    }
                )
            )
        },
        operation_description="Get list of menu items"
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        request_body=menu_item_schema,
        responses={
            201: menu_item_schema,
            400: error_response
        },
        operation_description="Create a new menu item"
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

class MenuDeleteView(generics.DestroyAPIView):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        responses={
            204: "No content",
            404: error_response
        },
        operation_description="Delete a menu item"
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)

class TodayMenuView(generics.ListAPIView):
    serializer_class = MenuItemSerializer
    def get_queryset(self):
        return MenuItem.objects.filter(date=now().date())

def login_view(request):
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect('staff')
        return redirect('home')
        
    # Rate limiting
    ip = request.META.get('REMOTE_ADDR')
    cache_key = f'login_attempts_{ip}'
    attempts = cache.get(cache_key, 0)
    
    if attempts >= 5:  # 5 attempts allowed
        raise PermissionDenied('Too many login attempts. Please try again later.')
        
    if request.method == 'POST':
        cache.set(cache_key, attempts + 1, 300)  # 5 minutes timeout
        
    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    return redirect('index')

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

def password_reset_request(request):
    if request.method == "POST":
        email = request.POST.get("email")
        if not email.endswith("@manas.edu.kg"):
            return JsonResponse({"error": "Только почты manas.edu.kg разрешены"}, status=400)
            
        try:
            user = User.objects.get(email=email)
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            
            # Create reset link
            reset_link = request.build_absolute_uri(
                f'/reset-password-confirm/{uid}/{token}/'
            )
            
            # Send email
            subject = 'Сброс пароля'
            message = render_to_string('password_reset_email.html', {
                'user': user,
                'reset_link': reset_link,
            })
            
            if settings.DEBUG:
                print(f"Reset link: {reset_link}")  # For development
            else:
                send_mail(
                    subject,
                    message,
                    settings.EMAIL_HOST_USER,
                    [email],
                    fail_silently=False,
                )
                
            return JsonResponse({"detail": "Инструкции по сбросу пароля отправлены на вашу почту"})
        except User.DoesNotExist:
            # Don't reveal that the user doesn't exist
            return JsonResponse({"detail": "Инструкции по сбросу пароля отправлены на вашу почту"})
            
    return render(request, 'reset-password.html')

def password_reset_confirm(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
        
    if user is not None and default_token_generator.check_token(user, token):
        if request.method == "POST":
            password = request.POST.get("password")
            password2 = request.POST.get("password2")
            
            if password != password2:
                return JsonResponse({"error": "Пароли не совпадают"}, status=400)
                
            # Validate password
            try:
                validate_password(password, user)
            except ValidationError as e:
                return JsonResponse({"error": e.messages}, status=400)
                
            user.set_password(password)
            user.save()
            return JsonResponse({"detail": "Пароль успешно изменен"})
            
        return render(request, 'reset-password-confirm.html')
    else:
        return JsonResponse({"error": "Недействительная ссылка для сброса пароля"}, status=400)
