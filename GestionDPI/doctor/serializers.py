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

class LabResultSerializer(FlexFieldsModelSerializer):
    class Meta:
        model = LabResult
        fields= [
            "id",
            "labtechnician"
        ]
        expandable_fields= {"labtechnician": WorkerSerializer}
        
class RadioResultSerializer(FlexFieldsModelSerializer):
    class Meta:
        model = RadioResult
        fields= [
            "id",
            "labtechnician"
        ]
        expandable_fields= {"labtechnician": WorkerSerializer}
        
class TicketSerializer(FlexFieldsModelSerializer):
    
    worker= serializers.SerializerMethodField()
    
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
            "worker"
        ]
        expandable_fields = {"consultation": ConsultationSerializer, "labresult": LabResultSerializer}
        
    def get_worker(self, obj):
        if obj.status == 'Closed':
            if obj.type== 'Lab' and hasattr(obj, 'labresult') and obj.labresult is not None:
                return WorkerSerializer(obj.labresult.labtechnician, fields=['id', 'user.id', 'user.user', 'user.role'], expand= ['user.user']).data
            elif obj.type== 'Radio' and hasattr(obj, 'radioresult') and obj.radioresult is not None:
                return WorkerSerializer(obj.radioresult.radiologist, fields=['id', 'user.id', 'user.user', 'user.role'], expand= ['user.user']).data
            elif obj.type== 'Nursing' and hasattr(obj, 'nursingresult') and obj.nursingresult is not None:
                return WorkerSerializer(obj.nursingresult.nurse, fields=['id', 'user.id', 'user.user', 'user.role'], expand= ['user.user']).data
        return None



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
        
class NursingObservationSerializer(FlexFieldsModelSerializer):
    class Meta:
        model = RadioObservation
        fields = [
            "id",
            "title",
            "notes"
        ]
        
