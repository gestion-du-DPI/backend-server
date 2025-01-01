from rest_framework_simplejwt.views import TokenObtainPairView
from GestionDPI.serializers import CustomTokenObtainPairSerializer
from django.contrib.auth.models import User
from rest_framework.response import Response


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    def post(self, request, *args, **kwargs):
      
        modified_data = request.data.copy()

        email = modified_data.get('email')
        if email:
            try:
                modified_data['username'] = User.objects.filter(email=email)[0].username
                del modified_data['email']  
            except :
                return Response("non valid criedentials")
        request._full_data = modified_data
        print(modified_data)
        return super().post(request, *args, **kwargs)