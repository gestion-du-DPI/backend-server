from django.shortcuts import render
from GestionDPI.permissions import IsAdmin
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from django.http import JsonResponse 
from datetime import datetime, timedelta
from django.utils.timezone import now
from users.models import AppUser
from doctor.models import Consultation
from django.db.models.functions import TruncMonth
from django.db.models import Count
from collections import defaultdict
from calendar import month_name



class AdminOnlyView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        user = request.user
        
       
        
        
        admin_info = {
          'name': f"{user.first_name} {user.last_name}",
          'hospital': user.appuser.hospital.name,
          'address': user.appuser.address,
          'phone_number':user.appuser.phone_number,
          'email':user.email
        }
        
        three_months_ago = now() - timedelta(days=90)
        role_counts = {
        'patients': AppUser.objects.filter(role='Patient', created_at__gte=three_months_ago).count(),
        'doctors': AppUser.objects.filter(role='Doctor', created_at__gte=three_months_ago).count(),
        'nurses': AppUser.objects.filter(role='Nurse', created_at__gte=three_months_ago).count(),
        'radiologists': AppUser.objects.filter(role='Radiologist', created_at__gte=three_months_ago).count(),
        'lab_technicians': AppUser.objects.filter(role='LabTechnician', created_at__gte=three_months_ago).count(),
        'consultations': Consultation.objects.filter( created_at__gte=three_months_ago).count(),
        }

        recent_patients = AppUser.objects.filter(role='Patient').order_by('-created_at')[:5]
       
       
        current_month = now()
        six_months_ago = current_month - timedelta(days=6 * 30)
        
        patient_stats = (
            AppUser.objects.filter(role='Patient', created_at__gte=six_months_ago)
            .annotate(month=TruncMonth('created_at'))
            .values('month')
            .annotate(count=Count('id'))
            .order_by('month')
        )

        consultation_stats = (
            Consultation.objects.filter(created_at__gte=six_months_ago)
            .annotate(month=TruncMonth('created_at'))
            .values('month')
            .annotate(count=Count('id'))
            .order_by('month')
        )

        stats = {
          month_name[(six_months_ago + timedelta(days=30 * i)).month]:{ 
          'patiens':  next((entry['count'] for entry in patient_stats), 0),
          'consultations': next((entry['count'] for entry in patient_stats), 0)
          }
          for i in range(6)
          
        }
        top_doctors = (
          Consultation.objects.values('doctor') 
          .annotate(consultation_count=Count('id'))  
          .order_by('-consultation_count') 
          [:9] 
        )
        data = {
          'admin_info':admin_info,
          'role_counts':role_counts,
          'top_staff':list(top_doctors),
          'stats':stats,
          'recent_patients':list(recent_patients)
        }
       
        return JsonResponse(data)
