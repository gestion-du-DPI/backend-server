
from GestionDPI.permissions import IsDoctor
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from django.http import JsonResponse 
from datetime import datetime, timedelta,date
from django.utils.timezone import now
from users.models import AppUser,Patient,Worker
from doctor.models import Consultation,Ticket,Prescription,PrescriptionDetail,Medicine,LabResult,LabImage,LabObservation,RadioImage,RadioObservation,RadioResult,NursingObservation,NursingResult
from django.db.models.functions import TruncMonth
from django.db.models import Count
from calendar import month_name
from django.contrib.auth.models import User
from rest_framework import status
import qrcode
from django.http import HttpResponse
import io


class DoctorOnlyView(APIView):
    permission_classes = [IsAuthenticated, IsDoctor]

    def get(self, request):
        user = request.user
  
        doctor_info = {
          'id':user.appuser.id,
          'name': f"{user.first_name} {user.last_name}",
          'hospital': user.appuser.hospital.name,
          'address': user.appuser.address,
          'nss':user.appuser.nss,
          'phone_number':user.appuser.phone_number,
          'email':user.email,
          'profile_image':user.appuser.image.url
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
            month_name[(six_months_ago + timedelta(days=31 * i)).month]: {
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
class GetPatientsList(APIView):
    permission_classes = [IsAuthenticated, IsDoctor]

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
              'date_of_birth': patient.date_of_birth,
              'phone_number': patient.phone_number,
              'emergency_contact_name':patient.patient.emergency_contact_name,
              'emergency_contact_phone':patient.patient.emergency_contact_phone,
              'consultation_count':consultation_count,
              'profile_image':patient.image.url
              
          }
          
        )
       
       
        return JsonResponse({"patients":patients_serialized}, status=200)
      
  
class GetPatientView(APIView):
    permission_classes = [IsAuthenticated, IsDoctor]

    def get(self, request,user_id):
     
        patient =AppUser.objects.get(id=user_id)
       
        consultation_count = patient.patient.consultation_set.count()
        data={
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
          
        
        return JsonResponse(data)
class GetDPIView(APIView):
    permission_classes = [IsAuthenticated, IsDoctor]

    def get(self, request,id):
       
        patient =AppUser.objects.get(id=id)
        consultations = Consultation.objects.filter(patient=patient.patient)
        consultations_list = []
        for consultation in consultations:
            doctor= Worker.objects.get(id=consultation.doctor.id)
            
            last_prescription = Prescription.objects.filter(consultation=consultation).order_by('-id').first()
            if not last_prescription: sgph="-----"
            else : sgph = last_prescription.status
            
            if(consultation.archived):
                lasted_for=(consultation.archived_at-consultation.created_at).days
            else : lasted_for="-----"
            
            consultations_list.append({
                "consultation_id":consultation.id,
                "archived":consultation.archived,
                "date":consultation.created_at,
                "doctor_name":f"{doctor.user.user.first_name} {doctor.user.user.last_name}",
                "lasted_for":lasted_for,
                "sgph":sgph,
                "reason":consultation.reason,
                "priority":consultation.priority,
                "resume":consultation.resume
                
                
            })
        data ={
              'user_id':patient.id,
              'profile_image':patient.image.url,
              'name': f"{patient.user.first_name} {patient.user.last_name}",
              'date_of_birth': patient.date_of_birth,
              'nss':patient.nss,
              'email': patient.user.email,
              'phone_number': patient.phone_number,
              'emergency_contact_name':patient.patient.emergency_contact_name,
              'emergency_contact_phone':patient.patient.emergency_contact_phone,
              'medical_condition':patient.patient.medical_condition,
              'consultations_list':consultations_list
              
          }
      
          
        
        return JsonResponse(data)
class CreateConultationView(APIView):
    permission_classes = [IsAuthenticated, IsDoctor]

    def post(self, request):
        doctor = AppUser.objects.get(id= request.user.appuser.id).worker
        patient = AppUser.objects.get(id= request.data.get('patient_id')).patient
        priority = request.data.get('priority')
        reason=request.data.get('reason')
        if not all([ patient,priority,reason]):
            return JsonResponse({'error': 'Missing required fields'}, status=400)
        try:
           consultation =Consultation.objects.create(patient=patient,doctor=doctor,priority=priority,reason=reason,archived=False,resume="")
           return JsonResponse({'message': 'Consutation created successfully', 'consultation_id': consultation.id}, status=201)
        except Exception as e:
          print(e)
          return Response("creation failed")
        
      
class getConultationView(APIView):
    permission_classes = [IsAuthenticated, IsDoctor]

    def get(self, request,consultation_id):
        doctor_id = request.user.appuser.id
        consultation = Consultation.objects.get(id=consultation_id)
        patient= Patient.objects.get(id=consultation.patient.id).user
        data ={
              'user_id':patient.id,
              'profile_image':patient.image.url,
              'consultation_id':consultation.id,
              'name': f"{patient.user.first_name} {patient.user.last_name}",
              'date_of_birth': patient.date_of_birth,
              'nss':patient.nss,
              'email': patient.user.email,
              'phone_number': patient.phone_number,
              'emergency_contact_name':patient.patient.emergency_contact_name,
              'emergency_contact_phone':patient.patient.emergency_contact_phone,
              'resume':consultation.resume,
              'archived':consultation.archived
          }
        return JsonResponse(data)
class getAttachmentsView(APIView):
    permission_classes = [IsAuthenticated, IsDoctor]

    def get(self, request,consultation_id):
        doctor_id = request.user.appuser.id
        consultation = Consultation.objects.get(id=consultation_id)
        results_serialized = []

        # Lab Results
        lab_results = LabResult.objects.filter(ticket__consultation=consultation)
        for result in lab_results:
             ticket = Ticket.objects.get(pk=result.ticket)
             for image in result.labimage_set.all():
                
                results_serialized.append({
                    'type': 'Lab_image',
                    'title':ticket.title,
                    'made_by':f"{result.labtechnician.user.user.first_name} {result.labtechnician.user.user.last_name}",
                    'profile_image':result.labtechnician.user.image.url,
                    'created_at':result.created_at,
                    'attachment_id': image.image.url ,
                   
                })
             for obs in result.labobservation_set.all():    
                 results_serialized.append({
                    'type': 'lab_observation',
                    'title':ticket.title,
                    'made_by':f"{result.labtechnician.user.user.first_name} {result.labtechnician.user.user.last_name}",
                    'profile_image':result.labtechnician.user.image.url,
                    'created_at':result.created_at,
                    'attachment_id':obs.id
                   
                })


        # Radio Results
        radio_results = RadioResult.objects.filter(ticket__consultation=consultation)
        for result in radio_results:
             ticket = Ticket.objects.get(pk=result.ticket)
             for image in result.radioimage_set.all():
                
                results_serialized.append({
                    'type': 'Radio_image',
                    'title':ticket.title,
                    'made_by': f"{result.radiologist.user.user.first_name} {result.radiologist.user.user.last_name}",
                    'profile_image':result.radiologist.user.image.url,
                    'created_at':result.created_at,
                    'attachment_id': image.image.url ,
                   
                })
             for obs in result.radioobservation_set.all():    
                 results_serialized.append({
                    'type': 'Radio_observation',
                    'title':ticket.title,
                    'made_by': f"{result.radiologist.user.user.first_name} {result.radiologist.user.user.last_name}",
                    'profile_image':result.radiologist.user.image.url,
                    'created_at':result.created_at,
                    'attachment_id':obs.id
                   
                })


        # Nursing Results
        nursing_results = NursingResult.objects.filter(ticket__consultation=consultation)
        for result in nursing_results:
             ticket = Ticket.objects.get(pk=result.ticket)
             for obs in result.nursingobservation_set.all():    
                 results_serialized.append({
                    'type': 'Nursing_observation',
                    'title':ticket.title,
                    'made_by': f"{result.nurse.user.user.first_name} {result.nurse.user.user.last_name}",
                    'profile_image':result.nurse.user.image.url,
                    'created_at':result.created_at,
                    'attachment_id':obs.id ,
                })
        prescriptions = Prescription.objects.filter(consultation=consultation)
        for prescription in prescriptions:
                 consultation=Consultation.objects.get(pk=prescription.consultation)
                 doctor=Worker.objects.get(pk=consultation.doctor)
                 results_serialized.append({
                    'type': 'prescription',
                    'title': f'Doctor Prescription',
                    'made_by': f"{doctor.user.user.first_name} {doctor.user.user.last_name}",
                    'profile_image':doctor.user.image.url,
                    'created_at':prescription.created_at,
                    'attachment_id':prescription.id,
                    
                })

        return JsonResponse(results_serialized)
class GetLabImageView(APIView):
    permission_classes = [IsAuthenticated, IsDoctor]
    def get(self, request,id):    
        try:
          image= LabImage.objects.get(pk=id)
          result = LabResult.objects.get(pk=image.labresult)
          ticket = Ticket.objects.get(pk=result.ticket)
        except:
          return Response("unavailable data")

        return JsonResponse(
            {'title':ticket.title,
             'created_at':result.created_at,
             'made_by': f"{result.labtechnician.user.user.first_name} {result.labtechnician.user.user.last_name}",'image':image.url}
            )

class GetRadioImageView(APIView):
    permission_classes = [IsAuthenticated, IsDoctor]
    def get(self,id, request):    
        try:
          image= RadioImage.objects.get(pk=id)
          result = RadioResult.objects.get(pk=image.radioresult)
          ticket = Ticket.objects.get(pk=result.ticket)
        except:
          return Response("unavailable data")

        return JsonResponse(
            {'title':ticket.title,
             'created_at':result.created_at,
             'made_by': f"{result.radiologist.user.user.first_name} {result.radiologist.user.user.last_name}",
             'image':image.url}
            )

class GetRadioObservationView(APIView):
    permission_classes = [IsAuthenticated, IsDoctor]
    def get(self,request,id):    
        try:
          obs= RadioObservation.objects.get(pk=id)
          result = RadioResult.objects.get(pk=obs.radioresult)
          ticket = Ticket.objects.get(pk=result.ticket)
        except:
          return Response("unavailable data")

        return JsonResponse(
            {
             'created_at':result.created_at,
             'made_by': f"{result.radiologist.user.user.first_name} {result.radiologist.user.user.last_name}",
             'title':obs.title,
             'notes':obs.notes
            })
class GetLabObservationView(APIView):
    permission_classes = [IsAuthenticated, IsDoctor]
    def get(self, request,id):    
        try:
          obs= LabObservation.objects.get(pk=id)
          result = LabResult.objects.get(pk=obs.labresult)
          ticket = Ticket.objects.get(pk=result.ticket)
        except:
          return Response("unavailable data")

        return JsonResponse(
            {
             'created_at':result.created_at,
             'made_by': f"{result.labtechnician.user.user.first_name} {result.labtechnician.user.user.last_name}",
             'title':obs.title,
             'notes':obs.notes
            })
class GetNurseObservationView(APIView):
    permission_classes = [IsAuthenticated, IsDoctor]
    def get(self, request,id):    
        try:
          obs= NursingObservation.objects.get(pk=id)
          result = NursingResult.objects.get(pk=obs.nursingresult)
          ticket = Ticket.objects.get(pk=result.ticket)
        except:
          return Response("unavailable data")

        return JsonResponse(
            {
             'created_at':result.created_at,
             'made_by': f"{result.nurse.user.user.first_name} {result.nurse.user.user.last_name}",
             'title':obs.title,
             'notes':obs.notes
            })             
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
           ticket =Ticket.objects.create(consultation=consultation_id,priority=priority,status='Open',type=type,title=title,description=description,hospital=AppUser.hospital)
           JsonResponse({'message': 'Ticket created successfully', 'ticket_id': ticket.id}, status=201)
        except:
          return Response("creation failed")

class CreatePrescriptionView(APIView):
    permission_classes = [IsAuthenticated, IsDoctor]

    def post(self, request):
        consultation_id = request.data.get('consultation_id')
        status = 'Pending'
        medicines_list = request.data.get("medicines_list")
        notes = request.data.get("notes")
        
        if not all([ consultation_id,status,medicines_list,notes]):
            return JsonResponse({'error': 'Missing required fields'}, status=400)
        try:
           prescription =Prescription.objects.create(consultation=consultation_id,status=status,notes=notes)
           for medicine_detail in medicines_list:
               medicine = Medicine.objects.create(name=medicine_detail['name'])
               prescription_detail=PrescriptionDetail.objects.create(prescription=prescription,medicine=medicine,dosage=medicine_detail['dosage'],duration=medicine_detail['duration'],instructions=medicine_detail['instructions'],frequency=medicine_detail['frequency'])
           JsonResponse({'message': 'Prescription created successfully', 'prescription_id': prescription.id}, status=201)
        except:
          return Response("creation failed")
class ArchiveConsultationView(APIView):
    permission_classes = [IsAuthenticated, IsDoctor]

    def post(self, request):
        consultation_id = request.data.get('consultation_id')
        resume = request.data.get('resume')
        
        if not all([ consultation_id,resume]):
            return JsonResponse({'error': 'Missing required fields'}, status=400)
       
        try:
           consultation = Consultation.objects.get(id=consultation_id)
           consultation.resume=resume
           consultation.archived=True
           consultation.save()
           JsonResponse({'message': 'Consultation archived successfully', 'consultation_id': consultation_id}, status=201)
        except:
          return Response("archiving failed")     
class GetPrescriptionView(APIView):
    permission_classes = [IsAuthenticated, IsDoctor]

    def get(self, request,prescription_id):
     
        if not prescription_id :
            return JsonResponse({'error': 'Missing required fields'}, status=400)
        
        prescription = Prescription.objects.get(id=prescription_id)
        consultation = Consultation.objects.get(id=prescription.consultation)
        patient = Patient.objects.get(id=consultation.patient)
        doctor = Worker.objects.get(id=consultation.doctor)
        
        today = date.today()
        age = today.year - patient.user.date_of_birth.year
        prescription_details = PrescriptionDetail.objects.filter(prescription=prescription)
        details_string = "\n".join(
            f"- {detail.medicine.name} {detail.dosage} {detail.frequency} for {detail.duration} {detail.instructions}"
            for detail in prescription_details
        )
        
        data={
            "hospital_name":patient.user.hospital.name,
            "doctor_name":f"{doctor.user.user.first_name} {doctor.user.user.last_name}",
            "speciality":doctor.speciality,
            "patient_name":f"{patient.user.user.first_name} {patient.user.user.last_name}",
            "age":age,
            "gender":patient.user.gender,
            "date":prescription.created_at,
            "medications":details_string,
            "notes":prescription.notes
        }
       
        
        JsonResponse(data, status=200)
          
class ModifyMyUser(APIView):
    permission_classes = [IsAuthenticated, IsDoctor]

   
    def patch(self, request, format=None):
       
        app_user = AppUser.objects.get(pk=request.user.appuser.id)  
        first_name=request.data.get('first_name')
        last_name=request.data.get('last_name')
        gender = request.data.get('gender')
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
    
        
        app_user.user.save()
        app_user.save()
        print(app_user.image.url)
        return JsonResponse({'message': 'Doctor modified successfully', 'user_id': app_user.id}, status=201)
              

class GenerateQRView(APIView):
    permission_classes = [IsAuthenticated, IsDoctor]

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
    