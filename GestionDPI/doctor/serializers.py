from rest_framework import serializers
from .models import *
from users.serializers import WorkerSerializer, PatientSerializer
from rest_flex_fields import FlexFieldsModelSerializer


class ConsultationSerializer(FlexFieldsModelSerializer):

    class Meta:
        model = Consultation
        fields = [
            "id",
            "priority",
            "reason",
            "archived",
            "created_at",
            "resume",
            "patient",
            "doctor",
        ]
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
            "consultation",
        ]
        expandable_fields = {"consultation": ConsultationSerializer}


class LabObservationSerializer(FlexFieldsModelSerializer):
    class Meta:
        model = LabObservation
        fields = [
            "id",
            "title",
            "notes"
        ]

class LabImageSerializer(FlexFieldsModelSerializer):
    class Meta:
        model = LabImage
        fields = [
            "id",
            "image"
        ]

class RadioObservationSerializer(FlexFieldsModelSerializer):
    class Meta:
        model = RadioObservation
        fields = [
            "id",
            "title",
            "notes"
        ]

class RadioImageSerializer(FlexFieldsModelSerializer):
    class Meta:
        model = RadioImage
        fields = [
            "id",
            "image"
        ]
