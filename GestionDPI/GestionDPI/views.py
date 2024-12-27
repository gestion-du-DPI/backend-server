from rest_framework_simplejwt.views import TokenObtainPairView
from GestionDPI.serializers import CustomTokenObtainPairSerializer
from GestionDPI.permissions import IsAdmin
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

class AdminOnlyView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        # Only accessible by Admin users
        return Response({"message": "Welcome Admin!"})