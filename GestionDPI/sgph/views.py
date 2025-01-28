from django.shortcuts import render
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiParameter, OpenApiResponse,OpenApiTypes
@extend_schema(
    request={
        "application/json": {
            "type": "object",
            "properties": {
                "prescription_id": {"type": "integer"},
                "status": {"type": "string"},
            },
            "required": ["prescription_id", "status"],
        }
    },
    responses={201: {"type": "string", "example": "Prescription status modified successfully"}},
    description="Modify the status of a prescription",
)
class SetPrescriptionView(APIView):
    permission_classes = []

    def post(self, request):
        prescription_id = request.data.get('prescription_id')
        status = request.data.get('status')
        
        if not all([ consultation_id,status]):
            return JsonResponse({'error': 'Missing required fields'}, status=400)
       
        try:
           prescription = Prescription.objects.get(id=prescription_id)
           prescription.status=status
           prescription.save()
           JsonResponse({'message': 'prescription status modified successfully', 'prescription_id': prescription.id}, status=201)
        except:
          return Response("modyfing state failed")     

@extend_schema(
    responses={
        200: {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "hospital_name": {"type": "string"},
                    "doctor_name": {"type": "string"},
                    "speciality": {"type": "string"},
                    "patient_name": {"type": "string"},
                    "age": {"type": "integer"},
                    "gender": {"type": "string"},
                    "date": {"type": "string", "format": "date"},
                    "medications": {"type": "string"},
                    "notes": {"type": "string"},
                },
            },
        }
    },
    description="Retrieve a list of prescriptions with detailed information",
)
class GetPrescriptionsView(APIView):
    permission_classes = [IsAuthenticated, IsDoctor]

    def get(self, request):
        prescriptions = Prescription.objects
        prescriptions_serialized =[]
        for prescription in prescriptions:
            
            consultation = Consultation.objects.get(id=prescription.consultation)
            patient = Patient.objects.get(id=consultation.patient)
            doctor = Worker.objects.get(id=consultation.doctor)
            
            today = date.today()
            age = today.year - patient.user.date_of_birth.year
            prescription_details = PrescriptionDetail.objects.filter(prescription=prescription)
            details_string = "\n".join(
                f"- {detail.medicine.name} {detail.dosage} {detail.frequency} for {detail.duration} {detail.instructions}"
                for detail in prescription_details
           )
            prescriptions_serialized.append({
                "hospital_name":patient.user.hospital.name,
                "doctor_name":f"{doctor.user.user.first_name} {doctor.user.user.last_name}",
                "speciality":doctor.speciality,
                "patient_name":f"{patient.user.user.first_name} {patient.user.user.last_name}",
                "age":age,
                "gender":patient.user.gender,
                "date":prescription.created_at,
                "medications":details_string,
                "notes":prescription.notes
            })
       
        
        JsonResponse(prescriptions_serialized, status=200)
          