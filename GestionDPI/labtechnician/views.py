from doctor.serializers import TicketSerializer, ConsultationSerializer
from doctor.models import Ticket, LabResult, Consultation
from rest_framework.response import Response
from rest_framework.decorators import APIView
import rest_framework.status
from GestionDPI.permissions import IsLabTechnician

class DashboardView(APIView):
    def get(self, request):
        permission_classes=[IsLabTechnician]
        # Get the authenticated user from the request

        # Fetch data for the specific user (assuming a foreign key relationship to the user)
        tickets = Ticket.objects.filter(status='Open')

        # Serialize the queryset
        serializer = TicketSerializer(instance=tickets, fields=['consultation', 'title', 'description'], many=True)
        
        # Return the serialized data as a JSON response
        return Response(serializer.data)
    
    def post(self, request):
        permission_classes=[IsLabTechnician]

        data = request.data

        consultation = data.get('consultation')
        type_ = data.get('type')
        title = data.get('title')
        description = data.get('description')
        priority = data.get('priority')
        status = data.get('status')
        
        ticket_serializer= TicketSerializer(data= data)
        consultation_serializer = ConsultationSerializer(data= consultation)
        
        if consultation_serializer.is_valid():
            patient = data.get('patient')
            doctor = data.get('doctor')
            priority = data.get('priority')
            reason = data.get('reason')
            archived = data.get('archived')
            consultation = Consultation.objects.create(patient=patient, doctor=doctor, priority=priority, reason=reason, archived=archived)
            #consultation = consultation_serializer.create(consultation)
        else:
            return Response(consultation_serializer.errors, rest_framework.status.HTTP_400_BAD_REQUEST)
            
        if ticket_serializer.is_valid():
            ticket = Ticket.objects.create(consultation= consultation, type= type_, title=title, description=description, priority = priority, status= status)
            return Response(ticket.data)
        else:
            return Response(ticket_serializer.errors, rest_framework.status.HTTP_400_BAD_REQUEST)
        
        