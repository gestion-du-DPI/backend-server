
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

       

        stats = {
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
          for i in range(6)
         }
        recent_consultations_ids= [consultation.id for consultation in recent_consultations]
        top_tickets =  Ticket.objects.filter(consultation__in=recent_consultations_ids).order_by('-created_at')[:8] 
       
        top_tickets_serialized = [
            {
                'ticket_id':ticket.id, 
                'type': ticket.type,
                'title': ticket.title,
                'status':ticket.status
            }
            for ticket in top_tickets
        ]
       
        
        data = {
          'doctor_info':doctor_info,
          'stats':stats,
          'recent_patients':recent_patients_serialized,
          'requested_tests':top_tickets_serialized
        }
       
        return JsonResponse(data)
    