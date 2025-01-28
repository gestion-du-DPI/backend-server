import rest_framework.exceptions
import rest_framework.status
from rest_framework.response import Response
from rest_framework.decorators import APIView
from doctor.serializers import TicketSerializer, NursingObservationSerializer
from doctor.models import Ticket, NursingObservation, NursingResult
from users.serializers import *
from GestionDPI.permissions import IsLabNurse
from django.core.paginator import Paginator
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiParameter, OpenApiResponse

@extend_schema(
    summary="Retrieve Open Nursing Tickets",
    description="Get a list of open nursing tickets associated with the authenticated user's hospital.",
    responses={
        200: TicketSerializer(many=True),  # Schema for the serialized tickets
        403: OpenApiResponse(description="Permission denied"),
    },
    parameters=[
        OpenApiParameter(
            name="Authorization",
            location=OpenApiParameter.HEADER,
            description="Bearer token for authentication",
            required=True,
            type=str,
        ),
    ],
)
class GetOpenTicketsView(APIView):
    permission_classes = [IsLabNurse]

    def get(self, request):

        # Get the authenticated user from the request

        # Fetch data for the specific user (assuming a foreign key relationship to the user)
        tickets = Ticket.objects.filter(
            status="Open", type="Nursing", hospital=request.user.appuser.hospital
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
    summary="Submit Nursing Result",
    description="Submit the results for a nursing ticket, creating observations and marking the ticket as 'Closed'.",
    request={
        "application/json": OpenApiExample(
            "SubmitResultRequest",
            value={
                "ticket_id": 1,
                "title": "Observation Title",
                "notes": "Detailed notes about the observation",
            },
            description="Request body format",
        ),
    },
    responses={
        200: OpenApiResponse(description="Result submitted successfully"),
        400: OpenApiResponse(description="Bad request - missing or invalid data"),
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
    ],
)
class SubmitResult(APIView):
    permission_classes = [IsLabNurse]

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

        if NursingResult.objects.filter(ticket_id=ticket_id).exists():
            lab_result = ticket.nursingresult
        else:
            lab_result = NursingResult.objects.create(
                ticket=ticket, nurse=request.user.appuser.worker
            )

        lab_observation = NursingObservation.objects.create(
            nursingresult=lab_result, title=title, notes=notes
        )

        ticket.status = "Closed"
        ticket.save()

        return Response(status=rest_framework.status.HTTP_200_OK)

@extend_schema(
    summary="Get Nursing Observations for Ticket",
    description="Retrieve a list of nursing observations for a specific ticket ID.",
    responses={
        200: NursingObservationSerializer(many=True),  # Schema for observations
        400: OpenApiResponse(description="Missing or invalid ticket_id"),
        404: OpenApiResponse(description="Ticket or observations not found"),
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
            name="ticket_id",
            location=OpenApiParameter.PATH,
            description="ID of the ticket to retrieve observations for",
            required=True,
            type=int,
        ),
    ],
)
class GetResult(APIView):
    permission_classes = [IsLabNurse]

    def get(self, request, ticket_id):

        if ticket_id is None:
            return Response(
                "ticket_id missing", status=rest_framework.status.HTTP_400_BAD_REQUEST
            )

        try:
            ticket = Ticket.objects.get(
                id=ticket_id, hospital=request.user.appuser.hospital
            )
            nursingresult = ticket.nursingresult

        except Ticket.DoesNotExist or Ticket.MultipleObjectsReturned as e:
            return Response(
                e.__str__(), status=rest_framework.status.HTTP_404_NOT_FOUND
            )

        observation = NursingObservation.objects.filter(
            nursingresult_id=nursingresult.id
        )

        return Response(
            NursingObservationSerializer(observation, many=True).data,
            status=rest_framework.status.HTTP_200_OK,
        )

@extend_schema(
    summary="Get List of Patients",
    description="Retrieve a paginated list of patients associated with the authenticated user's hospital.",
    responses={
        200: PatientSerializer(many=True),  # Schema for the serialized patients
        400: OpenApiResponse(description="Invalid page number"),
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
            description="Page number for paginated results",
            required=False,
            type=int,
        ),
    ],
)
class GetPatientListView(APIView):
    permission_classes = [IsLabNurse]

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
    description="Retrieve detailed information about a specific patient using their NSS (National Social Security) number.",
    responses={
        200: PatientSerializer,  # Schema for the serialized patient
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
    permission_classes = [IsLabNurse]

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
    description="Retrieve a paginated list of closed nursing tickets associated with the authenticated user's hospital.",
    responses={
        200: TicketSerializer(many=True),  # Schema for the serialized tickets
        400: OpenApiResponse(description="Invalid page number"),
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
            description="Page number for paginated results",
            required=False,
            type=int,
        ),
    ],
)
class GetTicketHistoryView(APIView):
    permission_classes = [IsLabNurse]

    def get(self, request):
        # Filter tickets by the hospital of the current user
        tickets = Ticket.objects.filter(
            hospital=request.user.appuser.hospital, type="Nursing", status="Closed"
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
            fields=[
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
                "created_at",
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
    summary="Get Ticket Details by ID",
    description="Retrieve detailed information about a specific closed nursing ticket by its ID.",
    responses={
        200: TicketSerializer,  # Schema for the serialized ticket
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
            description="ID of the ticket to retrieve",
            required=True,
            type=int,
        ),
    ],
)
class GetTicketByID(APIView):
    permission_classes = [IsLabNurse]

    def get(self, request, id):

        try:
            ticket = Ticket.objects.get(
                id=id,
                hospital=request.user.appuser.hospital,
                type="Nursing",
                status="Closed",
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
