import rest_framework.exceptions
import rest_framework.status
from rest_framework.response import Response
from rest_framework.decorators import APIView
from doctor.serializers import (
    TicketSerializer,
    RadioImageSerializer,
    RadioObservationSerializer,
)
from doctor.models import Ticket, RadioResult, RadioObservation, RadioImage
from users.serializers import *
from GestionDPI.permissions import IsRadiologist
import cloudinary
from django.core.paginator import Paginator
from django.http import JsonResponse 


class GetOpenTicketsView(APIView):
    permission_classes = [IsRadiologist]

    def get(self, request):

        # Fetch data for the specific user (assuming a foreign key relationship to the user)
        tickets = Ticket.objects.filter(
            status="Open", type="Radio", hospital=request.user.appuser.hospital
        )

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
            e["ticket_id"] = e.pop("id")
        # Return the serialized data as a JSON response
        return Response(serializer.data)


class SubmitResult(APIView):
    permission_classes = [IsRadiologist]

    def post(self, request):

        data = request.data

        try:
            ticket_id = data["ticket_id"]
            title = data["title"]
            notes = data.get("notes")
        except KeyError as e:
            return Response(
                f"missing key: {e.__str__()}",
                status=rest_framework.status.HTTP_400_BAD_REQUEST,
            )

        try:
            ticket = Ticket.objects.get(
                id=ticket_id, hospital=request.user.appuser.hospital
            )
        except Ticket.DoesNotExist or Ticket.MultipleObjectsReturned as e:
            return Response(
                e.__str__(), status=rest_framework.status.HTTP_404_NOT_FOUND
            )

        if RadioResult.objects.filter(ticket_id=ticket_id).exists():
            radio_result = ticket.radioresult
        else:
            radio_result = RadioResult.objects.create(
                ticket=ticket, radiotechnician=request.user.appuser.worker
            )

        radio_observation = RadioObservation.objects.create(
            radioresult=radio_result, title=title, notes=notes
        )

        ticket.status = "Closed"

        return Response(status=rest_framework.status.HTTP_200_OK)


class AddImage(APIView):
    permission_classes = [IsRadiologist]

    def post(self, request):

        data = request.data

        try:
            ticket_id = data["ticket_id"]
            uploaded_image = request.FILES["image"]
        except KeyError as e:
            return Response(
                f"missing key: {e.__str__()}",
                status=rest_framework.status.HTTP_400_BAD_REQUEST,
            )

        try:
            ticket = Ticket.objects.get(
                id=ticket_id, hospital=request.user.appuser.hospital
            )
        except Ticket.DoesNotExist or Ticket.MultipleObjectsReturned as e:
            return Response(
                e.__str__(), status=rest_framework.status.HTTP_404_NOT_FOUND
            )

        if RadioResult.objects.filter(ticket_id=ticket_id).exists():
            radio_result = ticket.radioresult
        else:
            radio_result = RadioResult.objects.create(
                ticket=ticket, radiotechnician=request.user.appuser.worker
            )

        radio_image = RadioImage.objects.create(
            radioresult=radio_result, image=uploaded_image
        )

        return Response(
            {
                "id": radio_image.id,
                "message": "Image uploaded successfully",
                "image_url": radio_image.image.url,
            },
            status=rest_framework.status.HTTP_201_CREATED,
        )


class DelImage(APIView):
    permission_classes = [IsRadiologist]

    def delete(self, request, id):

        if id is None:
            return Response(
                "ticket_id missing", status=rest_framework.status.HTTP_400_BAD_REQUEST
            )

        try:
            radio_image = RadioImage.objects.get(
                id=id, radioresult__radiotechnician=request.user.appuser.worker
            )
        except RadioImage.DoesNotExist:
            return Response(
                {"message": "Image not found or not authorized to delete"},
                status=rest_framework.status.HTTP_404_NOT_FOUND,
            )

        cloudinary.uploader.destroy(radio_image.image.public_id, invalidate=True)
        radio_image.delete()  # Deletes the database entry

        return Response(
            {"message": "Image deleted successfully"},
            status=rest_framework.status.HTTP_200_OK,
        )


class GetResult(APIView):
    permission_classes = [IsRadiologist]

    def get(self, request, ticket_id):

        if ticket_id is None:
            return Response(
                "ticket_id missing", status=rest_framework.status.HTTP_400_BAD_REQUEST
            )

        try:
            ticket = Ticket.objects.get(
                id=ticket_id, hospital=request.user.appuser.hospital
            )
            radioresult = ticket.radioresult

        except Ticket.DoesNotExist or Ticket.MultipleObjectsReturned as e:
            return Response(
                e.__str__(), status=rest_framework.status.HTTP_404_NOT_FOUND
            )

        images = RadioImage.objects.filter(radioresult_id=radioresult.id)
        observation = RadioObservation.objects.filter(radioresult_id=radioresult.id)

        images_ser_data = []
        observation_ser_data = []

        if images.exists():
            images_ser = RadioImageSerializer(images, many=True)
            images_ser_data = images_ser.data
        if observation.exists():
            observation_ser = RadioObservationSerializer(observation, many=True)
            observation_ser_data = observation_ser.data

        return Response(
            [images_ser_data, observation_ser_data],
            status=rest_framework.status.HTTP_200_OK,
        )


class GetPatientListView(APIView):
    permission_classes = [IsRadiologist]

    def get(self, request):
        # Filter patients by the hospital of the current user
        patients = Patient.objects.filter(
            user__hospital=request.user.appuser.hospital
        ).order_by("user__user__last_name")

        # Initialize paginator with 10 patients per page
        paginator = Paginator(patients, per_page=10)

        # Get the 'page' parameter from query params
        page = request.query_params.get(
            "page", 1
        )  # Default to page 1 if 'page' is not provided

        try:
            page_obj = paginator.get_page(page)
        except Exception as e:
            return Response(
                {"error": f"Invalid page: {e.__str__()}"},
                status=rest_framework.status.HTTP_400_BAD_REQUEST,
            )

        # Extract the list of patients from page_obj
        patients_list = list(page_obj)  # Convert the page_obj to a list of patients

        # Serialize the list of patients
        patient_ser = PatientSerializer(
            patients_list,
            omit=[
                "medical_condition",
                "user.created_at",
                "user.updated_at",
                "user.place_of_birth",
                "user.hospital",
                "user.role",
                "user.is_active",
            ],
            expand=["user.user"],
            many=True,
        )

        return Response(
            {
                "count": paginator.count,
                "num_pages": paginator.num_pages,
                "current_page": page_obj.number,
                "results": patient_ser.data,
            },
            status=rest_framework.status.HTTP_200_OK,
        )


class GetPatientByNSS(APIView):
    permission_classes = [IsRadiologist]

    def get(self, request, nss):

        try:
            patient = Patient.objects.get(user__nss=nss)
        except Patient.DoesNotExist as e:
            return Response(
                e.__str__(), status=rest_framework.status.HTTP_404_NOT_FOUND
            )

        patient_ser = PatientSerializer(
            patient,
            omit=[
                "user.created_at",
                "user.updated_at",
                "user.hospital",
                "user.role",
                "user.is_active",
            ],
            expand=["user.user"],
        )

        return Response(
            patient_ser.data,
            status=rest_framework.status.HTTP_200_OK,
        )


class GetTicketHistoryView(APIView):
    permission_classes = [IsRadiologist]

    def get(self, request):
        # Filter tickets by the hospital of the current user
        tickets = Ticket.objects.filter(
            hospital=request.user.appuser.hospital, type="Radio", status= 'Closed'
        ).order_by("id")

        # Initialize paginator with 10 patients per page
        paginator = Paginator(tickets, per_page=10)

        # Get the 'page' parameter from query params
        page = request.query_params.get(
            "page", 1
        )  # Default to page 1 if 'page' is not provided

        try:
            page_obj = paginator.get_page(page)
        except Exception as e:
            return Response(
                {"error": f"Invalid page: {e.__str__()}"},
                status=rest_framework.status.HTTP_400_BAD_REQUEST,
            )

        # Extract the list of patients from page_obj
        tickets_list = list(page_obj)  # Convert the page_obj to a list of patients

        # Serialize the list of patients
        ticket_ser = TicketSerializer(
            tickets_list,
            fields= [
                "id",
                "title",
                "priority",
                "worker",
                "consultation.doctor",
                "consultation.doctor.id",
                "consultation.doctor.user.id",
                "consultation.doctor.user.user",
                "consultation.patient",
                "consultation.patient.id",
                "consultation.patient.user.id",
                "consultation.patient.user.user",
                "consultation.id",
                "created_at"
            ],
            expand=["consultation.doctor.user.user", "consultation.patient.user.user"],
            many=True,
        )

        return Response(
            {
                "count": paginator.count,
                "num_pages": paginator.num_pages,
                "current_page": page_obj.number,
                "results": ticket_ser.data,
            },
            status=rest_framework.status.HTTP_200_OK,
        )


class GetTicketByID(APIView):
    permission_classes = [IsRadiologist]

    def get(self, request, id):

        try:
            ticket = Ticket.objects.get(
                id=id, hospital=request.user.appuser.hospital, type="Radio", status= 'Closed'
            )
        except Ticket.DoesNotExist as e:
            return Response(
                e.__str__(), status=rest_framework.status.HTTP_404_NOT_FOUND
            )

        ticket_ser = TicketSerializer(
            ticket,
            omit=[
                "type",
                "consultation.archived",
                "consultation.reason",
                "consultation.patient.consultation_count",
                "consultation.patient.medical_condition",
                "consultation.patient.user.image",
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
                "consultation.doctor.user.image",
            ],
            expand=["consultation.doctor.user.user", "consultation.patient.user.user"],
        )

        return Response(
            ticket_ser.data,
            status=rest_framework.status.HTTP_200_OK,
        )
        
class getUserView(APIView):
    permission_classes = [IsRadiologist]

    def get(self, request):
        app_user=request.user.appuser
        def dispatch(self, request, *args, **kwargs):
            return super().dispatch(request, *args, **kwargs)
        data={
          "first_name":app_user.user.first_name,
          "last_name": app_user.user.last_name,
          "gender" : app_user.gender,
          "nss" :app_user.nss,
          "address" : app_user.address,
          "phone_number" :app_user.phone_number,
          "profile_image":app_user.image.url

        }
        return JsonResponse(data)
    
class ModifyMyUser(APIView):
    permission_classes = [IsRadiologist]

   
    def patch(self, request, format=None):
       
        app_user = AppUser.objects.get(pk=request.user.appuser.id)  
        first_name=request.data.get('first_name')
        last_name=request.data.get('last_name')
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
        return JsonResponse({'message': 'Radiologist modified successfully', 'user_id': app_user.id}, status=201)
      
