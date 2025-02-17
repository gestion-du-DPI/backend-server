from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import serializers
from rest_framework.parsers import JSONParser
from rest_framework.exceptions import NotFound
from django.db import transaction
from django.http import JsonResponse
from users.models import Patient
from doctor.models import Consultation,Prescription,LabImage,LabObservation,LabResult,RadioResult,RadioImage,RadioObservation,NursingObservation,NursingResult,Ticket
from GestionDPI.permissions import IsPatient
from doctor.models import  LabResult, RadioResult, NursingResult
from django.contrib.auth.password_validation import validate_password
from rest_framework.exceptions import ValidationError
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiParameter, OpenApiResponse,OpenApiTypes

class PatientDashboardView(APIView):
    permission_classes = [IsAuthenticated,IsPatient]
    @extend_schema(
        responses={
            200: OpenApiResponse(
                description="Returns patient information and list of consultations",
                examples=[
                    {
                        "patient_info": {
                            "name": "John Doe",
                            "hospital": "General Hospital",
                            "gender": "Male",
                            "nss": "123456789",
                            "date_of_birth": "1990-01-01",
                            "place_of_birth": "City A",
                            "address": "123 Street",
                            "phone_number": "+1234567890",
                            "emergency_contact_name": "Jane Doe",
                            "emergency_contact_phone": "+0987654321",
                            "medical_condition": "Hypertension"
                        },
                        "consultations": [
                            {
                                "consultation_id": 1,
                                "archived": False,
                                "date": "2024-01-01",
                                "doctor_name": "Dr. Smith",
                                "lasted_for": "-----",
                                "sgph": "Pending",
                                "reason": "Fever",
                                "priority": "High"
                            }
                        ]
                    }
                ]
            )
        },
        description="Retrieve the patient's profile and their consultations.",
        tags=["Patient Dashboard"]
    )
    def get(self, request):
        user = request.user
        
        # Get patient
        try:
            patient = Patient.objects.get(user=user.appuser)
        except Patient.DoesNotExist:
            raise NotFound(detail="Patient not found.")

        #patient info
        patient_info = {
            'name': f"{user.first_name} {user.last_name}",
            'hospital':patient.user.hospital.name,
            'gender': patient.user.gender,
            'nss': patient.user.nss,
            'date_of_birth': patient.user.date_of_birth,
            'place_of_birth': patient.user.place_of_birth,
            'address': patient.user.address,
            'phone_number': patient.user.phone_number,
            'emergency_contact_name': patient.emergency_contact_name,
            'emergency_contact_phone': patient.emergency_contact_phone,
            'medical_condition': patient.medical_condition
        }

        #consultations related to the patient
        consultations = Consultation.objects.filter(patient=patient)
        print(consultations)
        consultations_list = []
        for consultation in consultations:
            doctor= Worker.objects.get(id=consultation.doctor)
            
            last_prescription = Prescription.objects.filter(consultation=consultation).order_by('-id').first()
            if not last_prescription: sgph="-----"
            else : sgph = last_prescription.status
            
            if(consultation.archived):
                lasted_for=(consultation.archived_at-consultation.created_at).days
            else : lasted_for="-----"
            
            consultations_list.append({
                "consultation_id":consultation.id,
                "archived":consultation.archived,
                "date":consultation.created_at,
                "doctor_name":doctor.name,
                "lasted_for":lasted_for,
                "sgph":sgph,
                "reason":consultation.reason,
                "priority":consultation.priority
                
                
            })
        print(consultations_list)
        return JsonResponse({'patient_info': patient_info, 'consultations': consultations_list}, status=200)


class ConsultationDetailView(APIView):
    permission_classes = [IsAuthenticated,IsPatient]
    
    def get(self, request, consultation_id):
        user = request.user

        # Get patient and consultation
        try:
            patient = Patient.objects.get(user=user.appuser)
            consultation = Consultation.objects.get(id=consultation_id, patient=patient)
        except (Patient.DoesNotExist, Consultation.DoesNotExist):
            raise NotFound(detail="Consultation not found or unauthorized access.")

        patient_info = {
            'name': f"{user.first_name} {user.last_name}",
            'gender': patient.user.gender,
            'nss': patient.user.nss,
            'date_of_birth': patient.user.date_of_birth,
            'place_of_birth': patient.user.place_of_birth,
            'address': patient.user.address,
            'phone_number': patient.user.phone_number,
            'emergency_contact_name': patient.emergency_contact_name,
            'emergency_contact_phone': patient.emergency_contact_phone,
            
        }
        # Prepare consultation details
        consultation_details = {
            'id': consultation.id,
            'created_at': consultation.created_at,
            'doctor': f"{consultation.doctor.user.user.first_name} {consultation.doctor.user.user.last_name}",
            'priority': consultation.priority,
            'reason': consultation.reason,
            'resume': consultation.resume,
            'archived' : consultation.archived
        }
        results_serialized = []

        # Lab Results
        lab_results = LabResult.objects.filter(ticket__consultation=consultation)
        for result in lab_results:
             ticket = Ticket.objects.get(pk=result.ticket)
             for image in result.labimage_set.all():
                
                results_serialized.append({
                    'type': 'Lab_image',
                    'title':ticket.title,
                    'made_by':f"{result.labtechnician.user.user.first_name} {result.labtechnician.user.user.last_name}",
                    'profile_image':result.labtechnician.user.image.url,
                    'created_at':result.created_at,
                    'attachment_id': image.image.url ,
                   
                })
             for obs in result.labobservation_set.all():    
                 results_serialized.append({
                    'type': 'lab_observation',
                    'title':ticket.title,
                    'made_by':f"{result.labtechnician.user.user.first_name} {result.labtechnician.user.user.last_name}",
                    'profile_image':result.labtechnician.user.image.url,
                    'created_at':result.created_at,
                    'attachment_id':obs.id
                   
                })


        # Radio Results
        radio_results = RadioResult.objects.filter(ticket__consultation=consultation)
        for result in radio_results:
             ticket = Ticket.objects.get(pk=result.ticket)
             for image in result.radioimage_set.all():
                
                results_serialized.append({
                    'type': 'Radio_image',
                    'title':ticket.title,
                    'made_by': f"{result.radiologist.user.user.first_name} {result.radiologist.user.user.last_name}",
                    'profile_image':result.radiologist.user.image.url,
                    'created_at':result.created_at,
                    'attachment_id': image.image.url ,
                   
                })
             for obs in result.radioobservation_set.all():    
                 results_serialized.append({
                    'type': 'Radio_observation',
                    'title':ticket.title,
                    'made_by': f"{result.radiologist.user.user.first_name} {result.radiologist.user.user.last_name}",
                    'profile_image':result.radiologist.user.image.url,
                    'created_at':result.created_at,
                    'attachment_id':obs.id
                   
                })


        # Nursing Results
        nursing_results = NursingResult.objects.filter(ticket__consultation=consultation)
        for result in nursing_results:
             ticket = Ticket.objects.get(pk=result.ticket)
             for obs in result.nursingobservation_set.all():    
                 results_serialized.append({
                    'type': 'Nursing_observation',
                    'title':ticket.title,
                    'made_by': f"{result.nurse.user.user.first_name} {result.nurse.user.user.last_name}",
                    'profile_image':result.nurse.user.image.url,
                    'created_at':result.created_at,
                    'attachment_id':obs.id ,
                })
        prescriptions = Prescription.objects.filter(consultation=consultation)
        for prescription in prescriptions:
                 consultation=Consultation.objects.get(pk=prescription.consultation)
                 doctor=Worker.objects.get(pk=consultation.doctor)
                 results_serialized.append({
                    'type': 'prescription',
                    'title': f'Doctor Prescription',
                    'made_by': f"{doctor.user.user.first_name} {doctor.user.user.last_name}",
                    'profile_image':doctor.user.image.url,
                    'created_at':prescription.created_at,
                    'attachment_id':prescription.id,
                    
                })


        return JsonResponse({'patient':patient_info,'consultation': consultation_details, 'results': results_serialized}, status=200)




@extend_schema(
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "first_name": {"type": "string"},
                    "last_name": {"type": "string"},
                    "gender": {"type": "string"},
                    "nss": {"type": "string"},
                    "address": {"type": "string"},
                    "phone_number": {"type": "string"},
                    "password": {"type": "string", "format": "password"},
                    "email": {"type": "string", "format": "email"}
                }
            },
            "multipart/form-data": {
                "type": "object",
                "properties": {
                    "image": {"type": "string", "format": "binary"}
                }
            }
        },
        responses={
            201: OpenApiResponse(
                description="User details successfully modified.",
                examples={"message": "User modified successfully", "user_id": 1}
            ),
            400: OpenApiResponse(description="Invalid input."),
        },
        description="Modify details of the authenticated user.",
        tags=["User Management"]
    )
class ModifyMyUser(APIView):
    permission_classes = [IsAuthenticated, IsPatient]

    
    def patch(self, request, format=None):
       
        app_user = AppUser.objects.get(pk=request.user.appuser.id)  
        first_name=request.data.get('first_name')
        last_name=request.data.get('last_name')
        gender = request.data.get('gender')
        nss =request.data.get('nss')
        address = request.data.get('address')
        phone_number = request.data.get('phone_number')
        password = request.data.get('password')
        email = request.data.get('email')
        file = request.FILES.get('image')  
        
        if file:
            app_user.image = file  
        if first_name:
            app_user.user.first_name = first_name
        if last_name:
            app_user.user.last_name = last_name
        if gender:
            app_user.gender = gender
        if nss:
            app_user.nss = nss
        if address:
            app_user.address = address
        if phone_number:
            app_user.phone_number = phone_number
        if password:
            app_user.user.set_password(password) 
        if email:
            app_user.user.email = email
    
        
        app_user.user.save()
        app_user.save()
        print(app_user.image.url)
        return JsonResponse({'message': 'Doctor modified successfully', 'user_id': app_user.id}, status=201)
              
