import rest_framework.exceptions
from doctor.serializers import TicketSerializer
from doctor.models import Ticket, LabResult, LabObservation, LabImage
from users.serializers import *
from rest_framework.response import Response
from rest_framework.decorators import APIView
import rest_framework.status
from GestionDPI.permissions import IsLabTechnician
from django.core.files.storage import FileSystemStorage


class GetAllLabTicketsView(APIView):
    permission_classes = [IsLabTechnician]
    def get(self, request):
        
        # Get the authenticated user from the request

        # Fetch data for the specific user (assuming a foreign key relationship to the user)
        tickets = Ticket.objects.filter(status="Open", type="Lab", consultation__doctor__user__hospital= request.user.appuser.hospital)

        # Serialize the queryset
        serializer = TicketSerializer(
            tickets,
            omit=[
                "status",
                "type",
                "created_at",
                "consultation.archived",
                "consultation.reason",
                "consultation.patient.medical_condition",
                "consultation.patient.user.created_at",
                "consultation.patient.user.updated_at",
                "consultation.patient.user.place_of_birth",
                "consultation.patient.user.hospital",
                "consultation.patient.user.address",
                "consultation.patient.user.role",
                "consultation.patient.user.is_active",
                "consultation.doctor.user.role",
                "consultation.doctor.user.gender",
                "consultation.doctor.user.phone_number",
                "consultation.doctor.user.nss",
                "consultation.doctor.user.date_of_birth",
                "consultation.doctor.user.gender",
                "consultation.doctor.user.created_at",
                "consultation.doctor.user.updated_at",
                "consultation.doctor.user.place_of_birth",
                "consultation.doctor.user.hospital",
                "consultation.doctor.user.address",
                "consultation.doctor.user.is_active",
            ],
            expand=["consultation.doctor.user.user", "consultation.patient.user.user"],
            many=True,
        )

        for e in serializer.data:
            e['ticket_id']=e.pop('id')
        # Return the serialized data as a JSON response
        return Response(serializer.data)

class SetObservation(APIView):
    permission_classes = [IsLabTechnician]
    def post(self, request):
        
        
        data= request.data
        
        try:
            ticket_id= data['ticket_id']
            title= data['title']
            notes= data.get('notes')
            
        except Exception as e:
            return Response(f"missing key: {e.__str__()}", status= rest_framework.status.HTTP_400_BAD_REQUEST)
        
        ticket=Ticket.objects.get(id=ticket_id)
        lab_result, _ = LabResult.objects.get_or_create(ticket= ticket, labtechnician= request.user.appuser.worker)
        lab_observation = LabObservation.objects.create(labresult= lab_result, title= title, notes= notes)
        
        return Response(status= rest_framework.status.HTTP_200_OK)

class SetImage(APIView):
    permission_classes = [IsLabTechnician]
    def post(self, request):
        
        data= request.data
        
        try:
            ticket_id= data['ticket_id']
            uploaded_image = request.FILES['image']
        except Exception as e :
            return Response(f'missing key: {e.__str__()}', status= rest_framework.status.HTTP_400_BAD_REQUEST)
        
        ticket=Ticket.objects.get(id=ticket_id)
        if LabResult.objects.filter(ticket_id=ticket_id).exists():
            lab_result=ticket.labresult
        else :
            lab_result=LabResult.objects.create(ticket= ticket, labtechnician= request.user.appuser.worker)
            
        lab_image = LabImage.objects.create(labresult=lab_result, image=uploaded_image)
    
        return Response({
            'message': 'Image uploaded successfully',
            'image_url': lab_image.image.url
        }, status=rest_framework.status.HTTP_201_CREATED)