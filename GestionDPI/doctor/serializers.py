from rest_framework import serializers
from .models import Ticket, Consultation
from users.serializers import WorkerSerializer, PatientSerializer
from rest_flex_fields import FlexFieldsModelSerializer


class ConsultationSerializer(FlexFieldsModelSerializer):

    class Meta:
        model = Consultation
        fields = ["id", "priority", "reason", "archived", "created_at", "resume","patient","doctor"]
        expandable_fields = {"patient": PatientSerializer, "doctor": WorkerSerializer}


class TicketSerializer(FlexFieldsModelSerializer):
    class Meta:
        model = Ticket
        fields = [
            "id",
            "type",
            "title",
            "description",
            "priority",
            "status",
            "created_at",
            "consultation"
        ]
        expandable_fields = {"consultation": ConsultationSerializer}
