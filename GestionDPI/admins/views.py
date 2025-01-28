from GestionDPI.permissions import IsAdmin
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import NotFound
from rest_framework.views import APIView
from rest_framework.response import Response
from django.http import JsonResponse 
from datetime import datetime, timedelta
from django.utils.timezone import now
from users.models import AppUser,Patient,Worker,Hospital
from doctor.models import Consultation
from django.db.models.functions import TruncMonth
from django.db.models import Count
from collections import defaultdict
from calendar import month_name
from django.contrib.auth.models import User
from rest_framework import status
import qrcode
from django.http import HttpResponse
import io
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiParameter, OpenApiResponse

@extend_schema(
    tags=['Admin Dashboard'],
    description='Get admin dashboard data including counts, statistics, and recent activity',
    responses={
        200: {
            'type': 'object',
            'properties': {
                'admin_info': {
                    'type': 'object',
                    'properties': {
                        'id': {'type': 'integer'},
                        'name': {'type': 'string'},
                        'hospital': {'type': 'string'},
                        'address': {'type': 'string'},
                        'phone_number': {'type': 'string'},
                        'email': {'type': 'string'},
                        'profile_image': {'type': 'string'},
                        'workers_count': {'type': 'integer'},
                        'patients_count': {'type': 'integer'}
                    }
                },
                'role_counts': {'type': 'object'},
                'top_staff': {'type': 'array'},
                'stats': {'type': 'array'},
                'recent_patients': {'type': 'array'}
            }
        }
    }
)
class AdminOnlyView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        user = request.user
        
       
        workerroles=['Doctor','Radiologist','Labtechnician','Nurse']
        workercount=AppUser.objects.filter(role__in=workerroles,hospital= user.appuser.hospital.id).count()
        patientcount=AppUser.objects.filter(role='Patient',hospital= user.appuser.hospital.id).count()
        admin_info = {
          'id':user.appuser.id,
          'name': f"{user.first_name} {user.last_name}",
          'hospital': user.appuser.hospital.name,
          'address': user.appuser.address,
          'phone_number':user.appuser.phone_number,
          'email':user.email,
          'profile_image':user.appuser.image.url,
          'workers_count':workercount,
          'patients_count':patientcount
        }
        
        three_months_ago = now() - timedelta(days=90)
        role_counts = {
          'patients': AppUser.objects.filter(role='Patient', created_at__gte=three_months_ago,hospital=request.user.appuser.hospital).count(),
          'doctors': AppUser.objects.filter(role='Doctor', created_at__gte=three_months_ago,hospital=request.user.appuser.hospital).count(),
          'nurses': AppUser.objects.filter(role='Nurse', created_at__gte=three_months_ago,hospital=request.user.appuser.hospital).count(),
          'radiologists': AppUser.objects.filter(role='Radiologist', created_at__gte=three_months_ago,hospital=request.user.appuser.hospital).count(),
          'lab_technicians': AppUser.objects.filter(role='LabTechnician', created_at__gte=three_months_ago,hospital=request.user.appuser.hospital).count(),
          'consultations': Consultation.objects.filter( created_at__gte=three_months_ago).count(),
        }

        recent_patients = AppUser.objects.filter(role='Patient',hospital=request.user.appuser.hospital).order_by('-created_at')[:5]
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
              'emergency_contact_phone':patient.patient.emergency_contact_phone,
              'profile_image':patient.image.url
          }
          for patient in recent_patients
        ]
       
        current_month = now()
        six_months_ago = current_month - timedelta(days=6 * 30)
        
        patient_stats = (
            AppUser.objects.filter(role='Patient', created_at__gte=six_months_ago,hospital=request.user.appuser.hospital)
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

        top_doctors = (
          Consultation.objects.filter().values('doctor') 
          .annotate(consultation_count=Count('id'))  
          .order_by('-consultation_count') 
          [:9] 
        )
        doctor_ids = [entry['doctor'] for entry in top_doctors]
        doctors = Worker.objects.filter(id__in=doctor_ids)
       
        top_doctors_serialized = [
            {
                'user_id':doctor.user.id, 
                'name': f"{doctor.user.user.first_name} {doctor.user.user.last_name}",
                'role': f"Doctor@{doctor.speciality}",
                'profile_image':doctor.user.image.url
            }
            for doctor in doctors
        ]
       
        
        data = {
          'admin_info':admin_info,
          'role_counts':role_counts,
          'top_staff':top_doctors_serialized,
          'stats':stats_list,
          'recent_patients':recent_patients_serialized
        }
       
        return JsonResponse(data)
    
@extend_schema(
    tags=['Patient Management'],
    description='Create a new patient account',
    request={
        'multipart/form-data': {
            'type': 'object',
            'properties': {
                'email': {'type': 'string', 'format': 'email'},
                'first_name': {'type': 'string'},
                'last_name': {'type': 'string'},
                'phone_number': {'type': 'string'},
                'address': {'type': 'string'},
                'gender': {'type': 'string', 'enum': ['Male', 'Female']},
                'nss': {'type': 'string'},
                'date_of_birth': {'type': 'string', 'format': 'date'},
                'place_of_birth': {'type': 'string'},
                'emergency_contact_name': {'type': 'string'},
                'emergency_contact_phone': {'type': 'string'},
                'medical_condition': {'type': 'string'}
            },
            'required': [
                'email', 'first_name', 'last_name', 'phone_number', 'address',
                'gender', 'nss', 'date_of_birth', 'place_of_birth',
                'emergency_contact_name', 'emergency_contact_phone', 'medical_condition'
            ]
        }
    },
    responses={
        201: OpenApiResponse(
            description='Patient created successfully',
            response={
                'type': 'object',
                'properties': {
                    'message': {'type': 'string'},
                    'user_id': {'type': 'integer'}
                }
            }
        ),
        400: OpenApiResponse(description='Invalid input or user already exists')
    }
)
class CreatePatientView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def post(self, request):
        data = request.data

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
          username = f'{first_name}_{last_name}'
          user = User.objects.create_user(username=username, password=nss, email=email,first_name=first_name,last_name=last_name)
          
          appuser = AppUser.objects.create(user=user,hospital=request.user.appuser.hospital,role='Patient',phone_number=phone_number,address=address,is_active=True,gender=gender,nss=nss,date_of_birth=date_of_birth,place_of_birth=place_of_birth)
          
          patient = Patient.objects.create(user=appuser,emergency_contact_name=emergency_contact_name,emergency_contact_phone=emergency_contact_phone,medical_condition=medical_condition)
        
        except Exception as e:
          if user:
                user.delete()
          return Response({"error": "user already exist"}, status=status.HTTP_400_BAD_REQUEST)
        return JsonResponse({'message': 'User created successfully', 'user_id': appuser.id}, status=201)
       
 
@extend_schema(
    tags=['Worker Management'],
    description='Create a new worker account (doctor, nurse, etc.)',
    request={
        'multipart/form-data': {
            'type': 'object',
            'properties': {
                'email': {'type': 'string', 'format': 'email'},
                'first_name': {'type': 'string'},
                'last_name': {'type': 'string'},
                'role': {'type': 'string', 'enum': ['Doctor', 'Nurse', 'Radiologist', 'LabTechnician']},
                'phone_number': {'type': 'string'},
                'address': {'type': 'string'},
                'gender': {'type': 'string', 'enum': ['Male', 'Female']},
                'nss': {'type': 'string'},
                'date_of_birth': {'type': 'string', 'format': 'date'},
                'place_of_birth': {'type': 'string'},
                'speciality': {'type': 'string'}
            },
            'required': [
                'email', 'first_name', 'last_name', 'role', 'phone_number',
                'address', 'gender', 'nss', 'date_of_birth', 'place_of_birth',
                'speciality'
            ]
        }
    },
    responses={
        201: OpenApiResponse(
            description='Worker created successfully',
            response={
                'type': 'object',
                'properties': {
                    'message': {'type': 'string'},
                    'user_id': {'type': 'integer'}
                }
            }
        ),
        400: OpenApiResponse(description='Invalid input or user already exists')
    }
)     
class CreateWorkerView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def post(self, request):
        data = request.data 
      
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
            
        if not all([  email,first_name,last_name,role,phone_number,address,gender,nss,date_of_birth,place_of_birth,speciality]):
            return JsonResponse({'error': 'Missing required fields'}, status=400)
        try:
          username = f'{first_name}_{last_name}'
          user = User.objects.create_user(username=username, password=nss, email=email,first_name=first_name,last_name=last_name)
          
          appuser = AppUser.objects.create(user=user,hospital=request.user.appuser.hospital,role=role,phone_number=phone_number,address=address,is_active=True,gender=gender,nss=nss,date_of_birth=date_of_birth,place_of_birth=place_of_birth)
          
          worker = Worker.objects.create(user=appuser,speciality=speciality)
        
        except Exception as e:
          if user:
                user.delete()
          print(f"Error: {str(e)}")
          return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return JsonResponse({'message': 'User created successfully', 'user_id': appuser.id}, status=201)

@extend_schema(
    tags=['Patient Management'],
    description='Get list of all patients in the hospital',
    responses={
        200: {
            'type': 'object',
            'properties': {
                'patients': {
                    'type': 'array',
                    'items': {
                        'type': 'object',
                        'properties': {
                            'user_id': {'type': 'integer'},
                            'name': {'type': 'string'},
                            'created_at': {'type': 'string', 'format': 'date-time'},
                            'nss': {'type': 'string'},
                            'email': {'type': 'string'},
                            'address': {'type': 'string'},
                            'phone_number': {'type': 'string'},
                            'emergency_contact_name': {'type': 'string'},
                            'emergency_contact_phone': {'type': 'string'},
                            'consultation_count': {'type': 'integer'},
                            'profile_image': {'type': 'string'}
                        }
                    }
                }
            }
        }
    }
)
class GetPatientsList(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        patients = AppUser.objects.filter(role='Patient',hospital=request.user.appuser.hospital)
        patients_serialized=[]
        for patient in patients:
          consultation_count = patient.patient.consultation_set.count()
          patients_serialized.append(
          {
              'user_id':patient.id,
              'name': f"{patient.user.first_name} {patient.user.last_name}",
              'created_at': patient.created_at,
              'nss':patient.nss,
              'email': patient.user.email,
              'address': patient.address,
              'phone_number': patient.phone_number,
              'emergency_contact_name':patient.patient.emergency_contact_name,
              'emergency_contact_phone':patient.patient.emergency_contact_phone,
              'consultation_count':consultation_count,
              'profile_image':patient.image.url
              
          }
          
        )
       
       
        return JsonResponse({"patients":patients_serialized}, status=200)
      
@extend_schema(
    tags=['Worker Management'],
    description='Get list of all workers in the hospital',
    responses={
        200: {
            'type': 'object',
            'properties': {
                'workers': {
                    'type': 'array',
                    'items': {
                        'type': 'object',
                        'properties': {
                            'user_id': {'type': 'integer'},
                            'name': {'type': 'string'},
                            'role': {'type': 'string'},
                            'speciality': {'type': 'string'},
                            'email': {'type': 'string'},
                            'phone_number': {'type': 'string'},
                            'nss': {'type': 'string'},
                            'address': {'type': 'string'},
                            'created_at': {'type': 'string', 'format': 'date-time'},
                            'profile_image': {'type': 'string'},
                            'gender': {'type': 'string'}
                        }
                    }
                }
            }
        }
    }
)
class GetWorkersList(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        worker_roles = ["Doctor","Nurse","Radiologist","Labtechnician"]
        workers = AppUser.objects.filter(hospital=request.user.appuser.hospital,role__in=worker_roles)
        workers_serialized = [
          {
              'user_id':worker.id,
              'name': f"{worker.user.first_name} {worker.user.last_name}",
              'role':worker.role,
              'speciality':worker.worker.speciality,
              'email': worker.user.email,
              'phone_number': worker.phone_number,
              'nss':worker.nss,
              'address': worker.address,
              'created_at': worker.created_at,
              'profile_image':worker.image.url,
              'gender':worker.gender
          }
          for worker in workers
        ]
       
       
        return JsonResponse({"workers":workers_serialized}, status=200)

@extend_schema(
    tags=['User Management'],
    description='Delete a user account',
    parameters=[
        OpenApiParameter(
            name='pk',
            location=OpenApiParameter.PATH,
            description='User ID to delete',
            required=True,
            type=int
        )
    ],
    responses={
        201: OpenApiResponse(description='User deleted successfully'),
        404: OpenApiResponse(description='User not found')
    }
)     
class DeleteUser(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def delete(self, request,pk,format=None):
        try:
            user = AppUser.objects.get(pk=pk)
        except:
            raise NotFound(detail="deletion failed.")
        
        user.user.delete()
        return JsonResponse({'message': 'User deleted successfully'}, status=201)


@extend_schema(
    tags=['Patient Management'],
    description='Modify existing patient information',
    parameters=[
        OpenApiParameter(
            name='pk',
            location=OpenApiParameter.PATH,
            description='Patient ID to modify',
            required=True,
            type=int
        )
    ],
    request={
        'multipart/form-data': {
            'type': 'object',
            'properties': {
                'email': {'type': 'string', 'format': 'email'},
                'first_name': {'type': 'string'},
                'last_name': {'type': 'string'},
                'phone_number': {'type': 'string'},
                'address': {'type': 'string'},
                'gender': {'type': 'string', 'enum': ['Male', 'Female']},
                'nss': {'type': 'string'},
                'date_of_birth': {'type': 'string', 'format': 'date'},
                'place_of_birth': {'type': 'string'},
                'emergency_contact_name': {'type': 'string'},
                'emergency_contact_phone': {'type': 'string'},
                'medical_condition': {'type': 'string'},
                'image': {'type': 'string', 'format': 'binary'}
            }
        }
    },
    responses={
        201: OpenApiResponse(description='Patient modified successfully'),
        400: OpenApiResponse(description='Invalid input')
    }
)     
class ModifyPatientView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def patch(self, request,pk):
        data = request.data

        email=data.get('email')
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
        file = request.FILES.get('image')  
        
        try:
         
          appuser = AppUser.objects.get(pk=pk)
          user = appuser.user
          
          if file:
             appuser.image = file     
       
          if(first_name):
              user.first_name=first_name
          if(last_name):
             user.last_name=last_name
          if(email):
            user.email=email
          
          if(phone_number):
             appuser.phone_number=phone_number
          if(address):
            appuser.address=address
          if(gender):
              appuser.gender=gender
          if(nss):
            appuser.nss=nss
          if(date_of_birth):
            appuser.date_of_birth=date_of_birth
          if(place_of_birth):
             appuser.place_of_birth=place_of_birth
          
          patient = appuser.patient
          if(emergency_contact_name):
            patient.emergency_contact_name=emergency_contact_name
          if(emergency_contact_phone):
            patient.emergency_contact_phone=emergency_contact_phone
          if(medical_condition):
             patient.medical_condition=medical_condition
          user.save()
          appuser.save()
          patient.save()
        except Exception as e:
          print(e)
          return Response({"error": "user already exist"}, status=status.HTTP_400_BAD_REQUEST)
        return JsonResponse({'message': 'Patient modified successfully', 'user_id': appuser.id}, status=201)


@extend_schema(
    tags=['Worker Management'],
    description='Modify existing worker information',
    parameters=[
        OpenApiParameter(
            name='pk',
            location=OpenApiParameter.PATH,
            description='Worker ID to modify',
            required=True,
            type=int
        )
    ],
    request={
        'multipart/form-data': {
            'type': 'object',
            'properties': {
                'email': {'type': 'string', 'format': 'email'},
                'first_name': {'type': 'string'},
                'last_name': {'type': 'string'},
                'phone_number': {'type': 'string'},
                'address': {'type': 'string'},
                'gender': {'type': 'string', 'enum': ['Male', 'Female']},
                'nss': {'type': 'string'},
                'date_of_birth': {'type': 'string', 'format': 'date'},
                'place_of_birth': {'type': 'string'},
                'speciality': {'type': 'string'},
                'role': {'type': 'string'},
                'image': {'type': 'string', 'format': 'binary'}
            }
        }
    },
    responses={
        201: OpenApiResponse(description='Worker modified successfully'),
        400: OpenApiResponse(description='Invalid input')
    }
)       
class ModifyWorkerView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def patch(self, request,pk):
        data = request.data

        email = data.get('email')
        first_name = data.get('first_name')
        last_name = data.get('last_name')
        phone_number= data.get('phone_number')
        address = data.get('address')
        gender = data.get('gender')
        nss =  data.get('nss')
        date_of_birth =  data.get('date_of_birth')
        place_of_birth =  data.get('place_of_birth')
        speciality =  data.get('speciality')
        role=data.get('role')
        file = request.FILES.get('image')  
        
       
        try:
          appuser = AppUser.objects.get(pk=pk)
          user = appuser.user
          if file:    
             appuser.image = file  
          if(first_name):
              user.first_name=first_name
          if(last_name):
             user.last_name=last_name
          if(email):
            user.email=email
          

          if(phone_number):
             appuser.phone_number=phone_number
          if(address):
            appuser.address=address
          if(gender):
              appuser.gender=gender
          if(nss):
            appuser.nss=nss
          if(date_of_birth):
            appuser.date_of_birth=date_of_birth
          if(place_of_birth):
             appuser.place_of_birth=place_of_birth
          if(role):
             appuser.role = role
          
          worker = appuser.worker
          if(speciality):
             worker.speciality=speciality
          
          user.save()
          appuser.save()
          worker.save()
        except Exception as e:
          print(e)
          return Response({"error": f"user already exist , {e}"}, status=status.HTTP_400_BAD_REQUEST)
        return JsonResponse({'message': 'Worker modified successfully', 'user_id': appuser.id}, status=201)
       
@extend_schema(
    tags=['User Management'],
    description='Get current admin user information',
    responses={
        200: {
            'type': 'object',
            'properties': {
                'first_name': {'type': 'string'},
                'last_name': {'type': 'string'},
                'hospital': {'type': 'string'},
                'nss': {'type': 'string'},
                'address': {'type': 'string'},
                'phone_number': {'type': 'string'},
                'profile_image': {'type': 'string'}
            }
        }
    }
)  
class getPatientView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        app_user=request.user.appuser
        data={
          "first_name":app_user.user.first_name,
          "last_name": app_user.user.last_name,
          "hospital" : app_user.hospital.name,
          "nss" :app_user.nss,
          "address" : app_user.address,
          "phone_number" :app_user.phone_number,
          "profile_image":app_user.image.url

        }
        return JsonResponse(data)
      
@extend_schema(
    tags=['User Management'],
    description='Modify current admin user information',
    request={
        'multipart/form-data': {
            'type': 'object',
            'properties': {
                'first_name': {'type': 'string'},
                'last_name': {'type': 'string'},
                'hospital_name': {'type': 'string'},
                'nss': {'type': 'string'},
                'address': {'type': 'string'},
                'phone_number': {'type': 'string'},
                'password': {'type': 'string'},
                'email': {'type': 'string', 'format': 'email'},
                'image': {'type': 'string', 'format': 'binary'}
            }
        }
    },
    responses={
        201: OpenApiResponse(description='User modified successfully')
    }
)
class ModifyMyUser(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

   
    def patch(self, request, format=None):
       
        app_user = AppUser.objects.get(pk=request.user.appuser.id)  
        first_name=request.data.get('first_name')
        last_name=request.data.get('last_name')
        hospital_name = request.data.get('hospital_name')
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
        if hospital_name:
            hospital=Hospital.objects.get(pk=app_user.hospital.id)
            hospital.name=hospital_name
            hospital.save()
        if last_name:
            app_user.user.last_name = last_name
        if hospital_name:
            app_user.hospital.name = hospital_name
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
        return JsonResponse({'message': 'User modified successfully', 'user_id': app_user.id}, status=201)
      
@extend_schema(
    tags=['QR Code'],
    description='Generate QR code for NSS',
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'nss': {'type': 'string'}
            },
            'required': ['nss']
        }
    },
    responses={
        200: OpenApiResponse(
            description='QR code image',
            response={'type': 'string', 'format': 'binary'}
        ),
        400: OpenApiResponse(description='NSS not provided')
    }
)
class GenerateQRView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
      nss = request.data.get('nss')
      if not nss:
          return HttpResponse("NSS not provided", status=400)
      
      # Generate the QR code
      qr = qrcode.QRCode(
          version=1,
          error_correction=qrcode.constants.ERROR_CORRECT_L,
          box_size=10,
          border=4,
      )
      qr.add_data(nss)
      qr.make(fit=True)

      img = qr.make_image(fill_color="black", back_color="white")

      # Convert image to HTTP response
      buffer = io.BytesIO()
      img.save(buffer, format='PNG')
      buffer.seek(0)

      return HttpResponse(buffer, content_type='image/png')
   
@extend_schema(
    tags=['User Management'],
    description='Get current user information',
    responses={
        200: {
            'type': 'object',
            'properties': {
                'first_name': {'type': 'string'},
                'last_name': {'type': 'string'},
                'hospital': {'type': 'string'},
                'nss': {'type': 'string'},
                'address': {'type': 'string'},
                'phone_number': {'type': 'string'},
                'profile_image': {'type': 'string'}
            }
        }
    }
) 
class getUserView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        app_user=request.user.appuser
        def dispatch(self, request, *args, **kwargs):
            return super().dispatch(request, *args, **kwargs)
        data={
          "first_name":app_user.user.first_name,
          "last_name": app_user.user.last_name,
          "hospital" : app_user.hospital.name,
          "nss" :app_user.nss,
          "address" : app_user.address,
          "phone_number" :app_user.phone_number,
          "profile_image":app_user.image.url

        }
        return JsonResponse(data)