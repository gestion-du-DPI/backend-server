from rest_framework import serializers

from .models import Worker, Patient, AppUser


class DynamicFieldsModelSerializer(serializers.ModelSerializer):
    """
    A ModelSerializer that takes an optional `fields` argument during initialization
    to specify which fields should be included.
    """

    def __init__(self, *args, **kwargs):
        # Extract the `fields` argument before calling the parent's __init__
        fields = kwargs.pop("fields", None)
        super().__init__(*args, **kwargs)

        if fields:
            # Drop any fields that are not specified in the `fields` argument
            allowed = set(fields)
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)


class AppUserSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = AppUser
        fields = [
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


class WorkerSerializer(DynamicFieldsModelSerializer):

    class Meta:
        model = Worker
        fields = ["speciality"]


class PatientSerializer(DynamicFieldsModelSerializer):

    class Meta:
        model = Patient
        fields = [
            "emergency_contact_name",
            "emergency_contact_phone",
            "medical_condition",
        ]
