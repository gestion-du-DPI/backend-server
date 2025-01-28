import rest_framework.exceptions
import rest_framework.status
from rest_framework.response import Response
from rest_framework.decorators import APIView
from doctor.serializers import (
    TicketSerializer,
    LabImageSerializer,
    LabObservationSerializer,
)
from doctor.models import Ticket, LabResult, LabObservation, LabImage
from users.serializers import *
from GestionDPI.permissions import IsLabTechnician
import cloudinary
from django.core.paginator import Paginator
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiParameter, OpenApiResponse

@extend_schema(
        summary="Get Open Lab Tickets",
        description="Retrieve a list of open lab tickets for the authenticated user based on their hospital.",
        responses={
            200: TicketSerializer(many=True),  # Output schema
        },
        parameters=[
            OpenApiParameter(
                name="Authorization",
                location=OpenApiParameter.HEADER,
                description="Bearer token for authentication",
                required=True,
                type=str,
            )
        ],
)
class GetOpenTicketsView(APIView):
    permission_classes = [IsLabTechnician]

    def get(self, request):

        # Get the authenticated user from the request

        # Fetch data for the specific user (assuming a foreign key relationship to the user)
        tickets = Ticket.objects.filter(
            status="Open", type="Lab", hospital=request.user.appuser.hospital
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

@extend_schema(
    summary="Submit Lab Result",
    description="Submit a lab result for a specific ticket and mark it as closed.",
    request={
        "application/json": OpenApiExample(
            name="Submit Result Example",
            value={
                "ticket_id": 123,
                "title": "Hemoglobin Analysis",
                "notes": "Patient shows elevated levels of hemoglobin.",
            },
        ),
    },
    responses={
        200: OpenApiResponse(description="Lab result submitted successfully."),
        400: OpenApiResponse(description="Bad request or missing parameters."),
        404: OpenApiResponse(description="Ticket not found."),
    },
)
class SubmitResult(APIView):
    permission_classes = [IsLabTechnician]

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

        if LabResult.objects.filter(ticket_id=ticket_id).exists():
            lab_result = ticket.labresult
        else:
            lab_result = LabResult.objects.create(
                ticket=ticket, labtechnician=request.user.appuser.worker
            )

        lab_observation = LabObservation.objects.create(
            labresult=lab_result, title=title, notes=notes
        )

        ticket.status = "Closed"
        ticket.save()

        return Response(status=rest_framework.status.HTTP_200_OK)

@extend_schema(
    summary="Add Image to Lab Result",
    description="Upload an image associated with a lab result for a ticket.",
    request={
        "multipart/form-data": OpenApiExample(
            name="Image Upload Example",
            value={
                "ticket_id": 123,
                "image": "File object for the image.",
            },
        ),
    },
    responses={
        201: OpenApiResponse(
            description="Image uploaded successfully.",
            examples={
                "example": {
                    "id": 1,
                    "message": "Image uploaded successfully",
                    "image_url": "https://example.com/image.jpg",
                }
            },
        ),
        400: OpenApiResponse(description="Bad request or missing parameters."),
        404: OpenApiResponse(description="Ticket not found."),
    },
)
class AddImage(APIView):
    permission_classes = [IsLabTechnician]

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

        if LabResult.objects.filter(ticket_id=ticket_id).exists():
            lab_result = ticket.labresult
        else:
            lab_result = LabResult.objects.create(
                ticket=ticket, labtechnician=request.user.appuser.worker
            )

        lab_image = LabImage.objects.create(labresult=lab_result, image=uploaded_image)

        return Response(
            {
                "id": lab_image.id,
                "message": "Image uploaded successfully",
                "image_url": lab_image.image.url,
            },
            status=rest_framework.status.HTTP_201_CREATED,
        )


class DelImage(APIView):
    permission_classes = [IsLabTechnician]

    def delete(self, request, id):

        if id is None:
            return Response(
                "ticket_id missing", status=rest_framework.status.HTTP_400_BAD_REQUEST
            )

        try:
            lab_image = LabImage.objects.get(
                id=id, labresult__labtechnician=request.user.appuser.worker
            )
        except LabImage.DoesNotExist:
            return Response(
                {"message": "Image not found or not authorized to delete"},
                status=rest_framework.status.HTTP_404_NOT_FOUND,
            )

        cloudinary.uploader.destroy(lab_image.image.public_id, invalidate=True)
        lab_image.delete()  # Deletes the database entry

        return Response(
            {"message": "Image deleted successfully"},
            status=rest_framework.status.HTTP_200_OK,
        )

@extend_schema(
    summary="Get Lab Result",
    description="Retrieve all observations and images associated with a lab result for a ticket.",
    parameters=[
        OpenApiParameter(
            name="ticket_id",
            location=OpenApiParameter.PATH,
            description="ID of the ticket to fetch results for.",
            required=True,
            type=int,
        ),
    ],
    responses={
        200: OpenApiResponse(
            description="Success",
            examples={
                "example": [
                    {"images": [{"id": 1, "image_url": "https://example.com/img.jpg"}]},
                    {"observations": [{"title": "Blood Test", "notes": "Normal levels"}]},
                ]
            },
        ),
        404: OpenApiResponse(description="Ticket not found."),
    },
)
class GetResult(APIView):
    permission_classes = [IsLabTechnician]

    def get(self, request, ticket_id):

        if ticket_id is None:
            return Response(
                "ticket_id missing", status=rest_framework.status.HTTP_400_BAD_REQUEST
            )

        try:
            ticket = Ticket.objects.get(
                id=ticket_id, hospital=request.user.appuser.hospital
            )
            labresult = ticket.labresult

        except Ticket.DoesNotExist or Ticket.MultipleObjectsReturned as e:
            return Response(
                e.__str__(), status=rest_framework.status.HTTP_404_NOT_FOUND
            )

        images = LabImage.objects.filter(labresult_id=labresult.id)
        observation = LabObservation.objects.filter(labresult_id=labresult.id)

        images_ser_data = []
        observation_ser_data = []

        if images.exists():
            images_ser = LabImageSerializer(images, many=True)
            images_ser_data = images_ser.data
        if observation.exists():
            observation_ser = LabObservationSerializer(observation, many=True)
            observation_ser_data = observation_ser.data

        return Response(
            [images_ser_data, observation_ser_data],
            status=rest_framework.status.HTTP_200_OK,
        )

@extend_schema(
    summary="List Patients",
    description="Retrieve a paginated list of patients for the current user's hospital.",
    parameters=[
        OpenApiParameter(
            name="page",
            location=OpenApiParameter.QUERY,
            description="Page number for pagination.",
            required=False,
            type=int,
        ),
    ],
    responses={
        200: OpenApiResponse(
            description="List of patients.",
            examples={
                "example": {
                    "count": 50,
                    "num_pages": 5,
                    "current_page": 1,
                    "results": [
                        {"id": 1, "name": "John Doe", "user_id": 5},
                        {"id": 2, "name": "Jane Doe", "user_id": 6},
                    ],
                }
            },
        ),
        400: OpenApiResponse(description="Invalid page or request."),
    },
)
class GetPatientListView(APIView):
    permission_classes = [IsLabTechnician]

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

@extend_schema(
    summary="Get Patient by NSS",
    description="Retrieve detailed information about a patient by their NSS (National Social Security) number.",
    responses={
        200: PatientSerializer,  # Output schema
        404: OpenApiResponse(description="Patient not found"),
    },
    parameters=[
        OpenApiParameter(
            name="Authorization",
            location=OpenApiParameter.HEADER,
            description="Bearer token for authentication",
            required=True,
            type=str,
        ),
        OpenApiParameter(
            name="nss",
            location=OpenApiParameter.PATH,
            description="National Social Security number of the patient",
            required=True,
            type=str,
        ),
    ],
)
class GetPatientByNSS(APIView):
    permission_classes = [IsLabTechnician]

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

@extend_schema(
    summary="Get Ticket History",
    description="Retrieve a paginated list of closed lab tickets for the authenticated user's hospital.",
    responses={
        200: TicketSerializer(many=True),  # Output schema
        400: OpenApiResponse(description="Invalid page parameter"),
    },
    parameters=[
        OpenApiParameter(
            name="Authorization",
            location=OpenApiParameter.HEADER,
            description="Bearer token for authentication",
            required=True,
            type=str,
        ),
        OpenApiParameter(
            name="page",
            location=OpenApiParameter.QUERY,
            description="Page number for paginated results (default is 1)",
            required=False,
            type=int,
        ),
    ],
)
class GetTicketHistoryView(APIView):
    permission_classes = [IsLabTechnician]

    def get(self, request):
        # Filter tickets by the hospital of the current user
        tickets = Ticket.objects.filter(
            hospital=request.user.appuser.hospital, type="Lab", status= 'Closed'
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

@extend_schema(
    summary="Get Ticket by ID",
    description="Retrieve detailed information about a specific closed lab ticket by its ID.",
    responses={
        200: TicketSerializer,  # Output schema
        404: OpenApiResponse(description="Ticket not found"),
    },
    parameters=[
        OpenApiParameter(
            name="Authorization",
            location=OpenApiParameter.HEADER,
            description="Bearer token for authentication",
            required=True,
            type=str,
        ),
        OpenApiParameter(
            name="id",
            location=OpenApiParameter.PATH,
            description="ID of the ticket",
            required=True,
            type=int,
        ),
    ],
)
class GetTicketByID(APIView):
    permission_classes = [IsLabTechnician]

    def get(self, request, id):

        try:
            ticket = Ticket.objects.get(
                id=id, hospital=request.user.appuser.hospital, type="Lab", status= 'Closed'
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
