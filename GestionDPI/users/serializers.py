from rest_framework import serializers
from rest_flex_fields import FlexFieldsModelSerializer

from .models import Worker, Patient, AppUser, User



class UserSerializer(FlexFieldsModelSerializer):
    class Meta:
        model = User
        fields = ["id", "first_name", "last_name", "email"]


class AppUserSerializer(FlexFieldsModelSerializer):

    class Meta:
        model = AppUser
        fields = [
            "id",
            "user",
            "hospital",
            "role",
            "gender",
            "phone_number",
            "address",
            "is_active",
            "created_at",
            "updated_at",
            "nss",
            "date_of_birth",
            "place_of_birth",
            "image",
        ]
        expandable_fields = {"user": UserSerializer}


class WorkerSerializer(FlexFieldsModelSerializer):

    class Meta:
        model = Worker
        fields = ["id", "user", "speciality"]
        expandable_fields = {"user": AppUserSerializer}


class PatientSerializer(FlexFieldsModelSerializer):

    consultation_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Patient
        fields = [
            "id",
            "user",
            "emergency_contact_name",
            "emergency_contact_phone",
            "medical_condition",
            "consultation_count"
        ]
        expandable_fields = {"user": AppUserSerializer}
        
    def get_consultation_count(self, obj):
        return obj.number_of_consultations()
