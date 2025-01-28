from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiResponse
from rest_framework_simplejwt.views import TokenObtainPairView
from GestionDPI.serializers import CustomTokenObtainPairSerializer
from django.contrib.auth.models import User
from rest_framework.response import Response

@extend_schema(
    tags=['Authentication'],
    description='Obtain JWT token pair by providing either username/password or email/password.',
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'email': {'type': 'string', 'format': 'email'},
                'password': {'type': 'string', 'format': 'password'},
            },
        }
    },
    responses={
        200: {
            'description': 'Successfully authenticated',
            'type': 'object',
            'properties': {
                'access': {'type': 'string', 'description': 'JWT access token'},
                'refresh': {'type': 'string', 'description': 'JWT refresh token'},
            }
        },
        400: OpenApiResponse(description='Invalid credentials')
    },
    examples=[
        OpenApiExample(
            'Email Login Example',
            value={
                'email': 'user@example.com',
                'password': 'userpassword'
            },
            request_only=True,
        ),
        OpenApiExample(
            'Successful Response',
            value={
                'access': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...',
                'refresh': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...'
            },
            response_only=True,
        )
    ]
)
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    def post(self, request, *args, **kwargs):
        modified_data = request.data.copy()

        email = modified_data.get('email')
        if email:
            try:
                modified_data['username'] = User.objects.filter(email=email)[0].username
                del modified_data['email']  
            except:
                return Response("non valid criedentials")
        request._full_data = modified_data
        print(modified_data)
        return super().post(request, *args, **kwargs)