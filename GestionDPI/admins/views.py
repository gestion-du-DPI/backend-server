from django.shortcuts import render
from GestionDPI.permissions import IsAdmin
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from django.http import JsonResponse 
from datetime import datetime, timedelta
from django.utils.timezone import now
from users.models import AppUser,Patient,Worker
from doctor.models import Consultation
from django.db.models.functions import TruncMonth
from django.db.models import Count
from collections import defaultdict
from calendar import month_name
from django.contrib.auth.models import User


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
class CreatePatientView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def post(self, request):
        data = request.json() 

        email = data.get('email')
        first_name = data.get('first_name')
        last_name = data.get('last_name')
        phone_number= data.get('phone_number')
        address = data.get('address')
        gender = data.get('gender')
        nss =  data.get('nss')
        date_of_birth =  data.get('date_of_birth')
        place_of_birth =  data.get('place_of_birth')
        emergency_contact_name =  data.get('emergency_contact_name')
        emergency_contact_phone =  data.get('emergency_contact_phone')
        medical_condition= data.get('medical_condition')
            
        if not all([  email,first_name,last_name,phone_number,address,gender,nss,date_of_birth,place_of_birth,emergency_contact_name,emergency_contact_phone,medical_condition]):
            return JsonResponse({'error': 'Missing required fields'}, status=400)
        try:
          username = f'{first_name}{last_name}'
          user = User.objects.create_user(username=username, password=nss, email=email)
          
          appuser = AppUser.objects.create(user=user,hospital=request.user.appuser.hospital,role='Patient',phone_number=phone_number,address=address,is_active=True)
          
          patient = Patient.objects.create(user=appuser,gender=gender,nss=nss,date_of_birth=date_of_birth,place_of_birth=place_of_birth,emergency_contact_name=emergency_contact_name,emergency_contact_phone=emergency_contact_phone,medical_condition=medical_condition)
        
        except Exception as e:
        # Catch any other exceptions
          print(f"Error: {str(e)}")
          return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return JsonResponse({'message': 'User created successfully', 'user_id': user.id}, status=201)
        return ''
      
class CreateWorkerView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def post(self, request):
        data = request.json() 
      
        email = data.get('email')
        first_name = data.get('first_name')
        last_name = data.get('last_name')
        role = data.get('role')
        phone_number= data.get('phone_number')
        address = data.get('address')
        gender = data.get('gender')
        nss =  data.get('nss')
        date_of_birth =  data.get('date_of_birth')
        place_of_birth =  data.get('place_of_birth')
        speciality = data.get('speciality')
            
        if not all([  email,first_name,last_name,role,phone_number,address,gender,nss,date_of_birth,place_of_birth,emergency_contact_name,speciality]):
            return JsonResponse({'error': 'Missing required fields'}, status=400)
        try:
          username = f'{first_name}{last_name}'
          user = User.objects.create_user(username=username, password=nss, email=email)
          
          appuser = AppUser.objects.create(user=user,hospital=request.user.appuser.hospital,role=role,phone_number=phone_number,address=address,is_active=True)
          
          Worker = Worker.objects.create(user=appuser,gender=gender,nss=nss,date_of_birth=date_of_birth,place_of_birth=place_of_birth,speciality=speciality)
        
        except Exception as e:
        # Catch any other exceptions
          print(f"Error: {str(e)}")
          return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return JsonResponse({'message': 'User created successfully', 'user_id': user.id}, status=201)
        return ''
