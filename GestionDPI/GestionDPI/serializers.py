from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        
        app_user = getattr(user, 'appuser', None)
        token['user_id'] = user.id
        token['role'] = app_user.role if app_user else None

        return token