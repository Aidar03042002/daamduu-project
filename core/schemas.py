from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status

# Common response schemas
error_response = openapi.Response(
    description="Error response",
    schema=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'error': openapi.Schema(type=openapi.TYPE_STRING),
        }
    )
)

success_response = openapi.Response(
    description="Success response",
    schema=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'detail': openapi.Schema(type=openapi.TYPE_STRING),
        }
    )
)

# Menu schemas
menu_item_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'id': openapi.Schema(type=openapi.TYPE_INTEGER),
        'title': openapi.Schema(type=openapi.TYPE_STRING),
        'description': openapi.Schema(type=openapi.TYPE_STRING),
        'date': openapi.Schema(type=openapi.TYPE_STRING, format='date'),
        'created_at': openapi.Schema(type=openapi.TYPE_STRING, format='date-time'),
    }
)

# Payment schemas
payment_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'item_id': openapi.Schema(type=openapi.TYPE_INTEGER),
        'item_name': openapi.Schema(type=openapi.TYPE_STRING),
        'price': openapi.Schema(type=openapi.TYPE_NUMBER),
    }
)

payment_response_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN),
        'session_id': openapi.Schema(type=openapi.TYPE_STRING),
    }
)

# Email verification schemas
email_verification_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'email': openapi.Schema(type=openapi.TYPE_STRING, format='email'),
    }
)

verification_code_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'email': openapi.Schema(type=openapi.TYPE_STRING, format='email'),
        'code': openapi.Schema(type=openapi.TYPE_STRING),
        'username': openapi.Schema(type=openapi.TYPE_STRING),
        'password': openapi.Schema(type=openapi.TYPE_STRING),
        'password2': openapi.Schema(type=openapi.TYPE_STRING),
    }
)

# Scan schemas
scan_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'code': openapi.Schema(type=openapi.TYPE_STRING),
    }
)

scan_response_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN),
        'message': openapi.Schema(type=openapi.TYPE_STRING),
    }
) 