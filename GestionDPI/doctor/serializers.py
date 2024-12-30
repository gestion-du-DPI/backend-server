from rest_framework import serializers

from .models import Ticket, Consultation
from users.serializers import WorkerSerializer, PatientSerializer

class DynamicFieldsModelSerializer(serializers.ModelSerializer):
    """
    A ModelSerializer that takes an optional `fields` argument during initialization
    to specify which fields should be included.
    """
    def __init__(self, *args, **kwargs):
        # Extract the `fields` argument before calling the parent's __init__
        fields = kwargs.pop('fields', None)
        super().__init__(*args, **kwargs)

        if fields:
            # Drop any fields that are not specified in the `fields` argument
            allowed = set(fields)
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)

class ConsultationSerializer(DynamicFieldsModelSerializer):
    doctor= WorkerSerializer()
    patient= PatientSerializer()
    class Meta:
        model = Consultation
        fields = ["patient", "doctor", "priority", "reason", "archived", "created_at", "resume"]

class TicketSerializer(DynamicFieldsModelSerializer):
    consultation= ConsultationSerializer()
    class Meta:
        model = Ticket
        fields = ["consultation", "type", "title", "description", "priority", "status"]
        
    def create(self, validated_data):
        # Extract the nested consultation data
        consultation_data = validated_data.pop('consultation')

        # Create the Consultation object
        consultation = Consultation.objects.create(**consultation_data)

        # Create the Ticket object with the consultation
        ticket = Ticket.objects.create(consultation=consultation, **validated_data)

        return ticket

