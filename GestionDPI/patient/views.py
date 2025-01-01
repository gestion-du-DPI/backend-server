from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import serializers
from rest_framework.parsers import JSONParser
from rest_framework.exceptions import NotFound
from django.db import transaction
from django.http import JsonResponse
from users.models import Patient
from doctor.models import Consultation
from GestionDPI.permissions import IsPatient
from doctor.models import  LabResult, RadioResult, NursingResult
from django.contrib.auth.password_validation import validate_password
from rest_framework.exceptions import ValidationError


class PatientDashboardView(APIView):
    permission_classes = [IsAuthenticated,IsPatient]

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
        consultations_serialized = [
            {
                'id': consultation.id,
                'created_at': consultation.created_at,
                'doctor': f"{consultation.doctor.user.user.first_name} {consultation.doctor.user.user.last_name}",
                'priority': consultation.priority,
                'reason': consultation.reason,
                'resume': consultation.resume,
                'archived': consultation.archived
            }
            for consultation in consultations
        ]
        print(consultations_serialized)
        return JsonResponse({'patient_info': patient_info, 'consultations': consultations_serialized}, status=200)


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
            results_serialized.append({
                'type': 'Lab',
                'lab_technician': f"{result.labtechnician.user.user.first_name} {result.labtechnician.user.user.last_name}",
                'images': [image.image.url for image in result.labimage_set.all()],
                'observations': [
                    {'title': obs.title, 'notes': obs.notes} for obs in result.labobservation_set.all()
                ],
            })

        # Radio Results
        radio_results = RadioResult.objects.filter(ticket__consultation=consultation)
        for result in radio_results:
            results_serialized.append({
                'type': 'Radio',
                'radiologist': f"{result.radiologist.user.user.first_name} {result.radiologist.user.user.last_name}",
                'images': [image.image.url for image in result.radioimage_set.all()],
                'observations': [
                    {'title': obs.title, 'notes': obs.notes} for obs in result.radioobservation_set.all()
                ],
            })

        # Nursing Results
        nursing_results = NursingResult.objects.filter(ticket__consultation=consultation)
        for result in nursing_results:
            results_serialized.append({
                'type': 'Nursing',
                'nurse': f"{result.nurse.user.user.first_name} {result.nurse.user.user.last_name}",
                'observations': [
                    {'title': obs.title, 'notes': obs.notes} for obs in result.nursingobservation_set.all()
                ],
            })

        return JsonResponse({'patient':patient_info,'consultation': consultation_details, 'results': results_serialized}, status=200)





class EditPatientProfileView(APIView):
    """
    View to edit the profile information of a patient.
    """
    permission_classes = [IsAuthenticated, IsPatient]
    parser_classes = [JSONParser]  # Ensures JSON input

    def patch(self, request):
        user = request.user

        # Fetch the patient object
        try:
            patient = Patient.objects.get(user=user.appuser)
        except Patient.DoesNotExist:
            raise NotFound(detail="Patient not found.")

        # Allowed fields for editing (grouped by model)
        editable_fields = {
            'user': ['first_name', 'last_name', 'email', 'password'],
            'appuser': ['gender', 'date_of_birth', 'place_of_birth', 'address', 'phone_number'],
            'patient': ['emergency_contact_name', 'emergency_contact_phone']
        }

        errors = {}
        # Update fields
        with transaction.atomic():
            for model_name, fields in editable_fields.items():
                model_instance = user if model_name == 'user' else patient.user if model_name == 'appuser' else patient
                for field in fields:
                    if field in request.data:
                        value = request.data[field]
                        try:
                            # Specific validation for certain fields
                            if field == 'date_of_birth':
                                value = serializers.DateField().to_internal_value(value)
                            if field == 'password':
                                validate_password(value)  # Validate password strength
                                model_instance.set_password(value)  # Hash and set the password
                            elif field == 'email':
                                if user.__class__.objects.filter(email=value).exclude(id=user.id).exists():
                                    raise ValidationError("Email address is already in use.")
                                setattr(model_instance, field, value)
                            else:
                                setattr(model_instance, field, value)
                        except Exception as e:
                            errors[field] = str(e)
                
                # Save the instance
                model_instance.save()

        if errors:
            return JsonResponse({'message': 'Some fields could not be updated.', 'errors': errors}, status=400)

        return JsonResponse({"message": "Profile updated successfully."}, status=200)