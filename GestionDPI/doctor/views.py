
from GestionDPI.permissions import IsDoctor
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from django.http import JsonResponse 
from datetime import datetime, timedelta
from django.utils.timezone import now
from users.models import AppUser,Patient,Worker
from doctor.models import Consultation,Ticket
from django.db.models.functions import TruncMonth
from django.db.models import Count
from calendar import month_name
from django.contrib.auth.models import User
from rest_framework import status



class DoctorOnlyView(APIView):
    permission_classes = [IsAuthenticated, IsDoctor]

    def get(self, request):
        user = request.user
  
        doctor_info = {
          'id':user.appuser.id,
          'name': f"{user.first_name} {user.last_name}",
          'hospital': user.appuser.hospital.name,
          'address': user.appuser.address,
          'phone_number':user.appuser.phone_number,
          'email':user.email
        }
        
        current_doctor = request.user.appuser.worker

     
        recent_consultations = Consultation.objects.filter(doctor=current_doctor).order_by('-created_at')[:5]

     
        recent_patients = AppUser.objects.filter(
            role='Patient', 
            id__in=[consultation.patient.user.id for consultation in recent_consultations]
        )
        print(recent_consultations.count())
        recent_patients_serialized = [
          {
              'user_id':patient.id,
              'name': f"{patient.user.first_name} {patient.user.last_name}",
              'created_at': patient.created_at,
              'nss':patient.nss,
              'email': patient.user.email,
              'address': patient.address,
              'phone_number': patient.phone_number,
              'emergency_contact_name':patient.patient.emergency_contact_name,
              'emergency_contact_phone':patient.patient.emergency_contact_phone
          }
          for patient in recent_patients
        ]
       
        current_month = now()
        six_months_ago = current_month - timedelta(days=6 * 30)
        
        consultation_stats = (
            Consultation.objects.filter(created_at__gte=six_months_ago,doctor=current_doctor)
            .annotate(month=TruncMonth('created_at'))
            .values('month')
            .annotate(count=Count('id'))
            .order_by('month')
        )
        
        patient_stats = (
            AppUser.objects.filter(role='Patient', created_at__gte=six_months_ago,hospital=request.user.appuser.hospital)
            .annotate(month=TruncMonth('created_at'))
            .values('month')
            .annotate(count=Count('id'))
            .order_by('month')
        )

       
        stats_list =[]
        for i in range(6):
          stats_list.append({
            month_name[(six_months_ago + timedelta(days=30 * i)).month]: {
                'patients': next(
                    (entry['count'] for entry in patient_stats if entry['month'].month == (six_months_ago + timedelta(days=31 * i)).month),
                    0
                ),
                'consultations': next(
                    (entry['count'] for entry in consultation_stats if entry['month'].month == (six_months_ago + timedelta(days=31 * i)).month),
                    0
                ),
            }
            
          })
        recent_consultations_ids= [consultation.id for consultation in recent_consultations]
        top_tickets =  Ticket.objects.filter(consultation__in=recent_consultations_ids).order_by('-created_at')[:8]
        top_tickets_serialized= [] 
        for ticket in top_tickets:
          patient=AppUser.objects.get(id=ticket.consultation.patient.user.id)
          
          top_tickets_serialized.append(
              {
                  'ticket_id':ticket.id, 
                  'type': ticket.type,
                  'title': ticket.title,
                  'status':ticket.status,
                  'priority':ticket.priority,
                  'patient_id':patient.id,
                  'patient_name':f"{patient.user.first_name} {patient.user.last_name}"
              })
              
          
       
        
        data = {
          'doctor_info':doctor_info,
          'stats':stats_list,
          'recent_patients':recent_patients_serialized,
          'requested_tests':top_tickets_serialized
        }
       
        return JsonResponse(data)
  
class GetPatientView(APIView):
    permission_classes = [IsAuthenticated, IsDoctor]

    def get(self, request):
        nss = request.data.get('nss')
        patient =Patient.objects.get(nss=nss).appuser
        consultation_count = patient.consultations.count()
        data ={
              'user_id':patient.id,
              'name': f"{patient.user.first_name} {patient.user.last_name}",
              'created_at': patient.created_at,
              'nss':patient.nss,
              'email': patient.user.email,
              'address': patient.address,
              'phone_number': patient.phone_number,
              'emergency_contact_name':patient.patient.emergency_contact_name,
              'emergency_contact_phone':patient.patient.emergency_contact_phone,
              'medical_condition':patient.patient.medical_condition,
              'consultation_count':consultation_count
          }
        return JsonResponse(data)
class CreateConultationView(APIView):
    permission_classes = [IsAuthenticated, IsDoctor]

    def post(self, request):
        doctor_id = request.user.appuser.id
        patient_id = request.data.get('patient_id')
        priority = request.data.get('priority')
        reason=request.data.get('reason')
        if not all([ patient_id,priority,reason]):
            return JsonResponse({'error': 'Missing required fields'}, status=400)
        try:
           consultation =Consultation.objects.create(patient=patient_id,doctor=doctor_id,priority=priority,reason=reason,archived=False)
           JsonResponse({'message': 'Consutation created successfully', 'consultation_id': consultation.id}, status=201)
        except:
          return Response("creation failed")
        
      
class getConultationView(APIView):
    permission_classes = [IsAuthenticated, IsDoctor]

    def get(self, request):
        doctor_id = request.user.appuser.id
        consultation = Consultation.objects.get(id=request.data.get('consultation_id'))
        patient= Patient.objects.get(id=consultation.patient).appuser
        data ={
              'user_id':patient.id,
              'consultation_id':consultation.id,
              'name': f"{patient.user.first_name} {patient.user.last_name}",
              'date_of_birth': patient.date_of_birth,
              'nss':patient.nss,
              'email': patient.user.email,
              'phone_number': patient.phone_number,
              'emergency_contact_name':patient.patient.emergency_contact_name,
              'emergency_contact_phone':patient.patient.emergency_contact_phone,
              'resume':consultation.resume
          }
        return JsonResponse(data)
      
class CreateTicketView(APIView):
    permission_classes = [IsAuthenticated, IsDoctor]

    def post(self, request):
        doctor_id = request.user.appuser.id
        consultation_id = request.data.get('consultation_id')
        priority = request.data.get('priority')
        type = request.data.get("type")
        title = request.data.get("title")
        description = request.data.get("description")
        if not all([ consultation_id,priority,type,title,description]):
            return JsonResponse({'error': 'Missing required fields'}, status=400)
        try:
           ticket =Ticket.objects.create(consultation=consultation_id,priority=priority,status=status,type=type,title=title,description=description,hospital=AppUser.hospital)
           JsonResponse({'message': 'Ticket created successfully', 'ticket_id': ticket.id}, status=201)
        except:
          return Response("creation failed")
        
class ModifyUser(APIView):
    permission_classes = [IsAuthenticated, IsDoctor]

   
    def patch(self, request, pk, format=None):
        try:
            app_user = AppUser.objects.get(pk=pk)  
        except AppUser.DoesNotExist:
            raise NotFound(detail="AppUser not found.")
        first_name=request.data.get('first_name')
        last_name=request.data.get('last_name')
        hospital_name = request.data.get('hospital_name')
        gender = request.data.get('gender')
        nss =request.data.get('nss')
        address = request.data.get('address')
        phone_number = request.data.get('phone_number')
        password = request.data.get('password')
        email = request.data.get('email')
        image = request.data.get('image')

        if first_name:
            app_user.user.first_name = first_name
        if last_name:
            app_user.user.last_name = last_name
        if hospital_name:
            app_user.hospital.name = hospital_name
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
        if image:
            app_user.image = image
        app_user.user.save()
        app_user.save()
        return JsonResponse({'message': 'User modified successfully', 'user_id': app_user.id}, status=201)

class getUserView(APIView):
    permission_classes = [IsAuthenticated, IsDoctor]

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

        }
        return JsonResponse(data)
        