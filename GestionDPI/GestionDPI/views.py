from rest_framework_simplejwt.views import TokenObtainPairView
from GestionDPI.serializers import CustomTokenObtainPairSerializer
from django.contrib.auth.models import User



class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    def post(self, request, *args, **kwargs):
      
        modified_data = request.data.copy()

        email = modified_data.get('email')
        if email:
            modified_data['username'] = User.objects.filter(email=email)[0].username
            del modified_data['email']  

        request._full_data = modified_data
        print(modified_data)
        return super().post(request, *args, **kwargs)