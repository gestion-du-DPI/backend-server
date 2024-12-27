from django.contrib.auth.models import User
from django.db import models

# Hospital Model
class Hospital(models.Model):
    name = models.CharField(max_length=50, unique=True)

# Base User Model
class AppUser(models.Model):
    ROLE_CHOICES = [
        ('Admin', 'Admin'),
        ('Doctor', 'Doctor'),
        ('Nurse', 'Nurse'),
        ('Pharmacist', 'Pharmacist'),
        ('LabTechnician', 'LabTechnician'),
        ('Patient', 'Patient')
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    phone_number = models.CharField(max_length=20)
    address = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

# Patient Model
class Patient(models.Model):
    user = models.OneToOneField(AppUser, on_delete=models.CASCADE)
    gender = models.CharField(max_length=10)
    nss = models.CharField(max_length=50, unique=True)
    date_of_birth = models.DateField()
    place_of_birth = models.CharField(max_length=50)
    emergency_contact_name = models.CharField(max_length=20)
    emergency_contact_phone = models.CharField(max_length=20)
    medical_condition = models.TextField()
    
# Worker Model
class Worker(models.Model):
    user = models.OneToOneField(AppUser, on_delete=models.CASCADE)
    gender = models.CharField(max_length=10)
    date_of_birth = models.DateField()
    place_of_birth = models.CharField(max_length=50)
    speciality  = models.CharField(max_length=50, unique=True)
  
# Admin Model
class Admin(models.Model):
    user = models.OneToOneField(AppUser, on_delete=models.CASCADE)
   
# Consultation Model
class Consultation(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    doctor = models.ForeignKey( Worker, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    summary = models.TextField()
    notes = models.TextField(blank=True, null=True)   
    prescription = models.OneToOneField('Prescription', on_delete=models.CASCADE, null=True, blank=True, related_name='prescript')

class Medicine(models.Model):
    name = models.CharField(max_length=100)


class Prescription(models.Model):
    consultation = models.ForeignKey(Consultation, on_delete=models.CASCADE, null= True, related_name='consult')
    valid = models.BooleanField(default=False)
    medicines = models.ManyToManyField(Medicine, through='PrescriptionDetail')
    

class PrescriptionDetail(models.Model):
    prescription = models.ForeignKey(Prescription, on_delete=models.CASCADE)
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE)
    dosage = models.CharField(max_length=50)
    duration = models.CharField(max_length=50)
    instructions = models.TextField(blank=True, null=True)
    
class NurseNote(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    nurse = models.ForeignKey(Worker, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    actions_taken = models.TextField(blank=True, null=True)
    observations = models.TextField()

class BilanRadiologique(models.Model):
    consultation = models.ForeignKey(Consultation, on_delete=models.CASCADE)
    radiologist = models.ForeignKey(Worker, on_delete=models.CASCADE)
    title = models.CharField(max_length=50)
    description = models.TextField(max_length=255)
    priority = models.CharField(max_length=10)
    compteRendu = models.OneToOneField('CompteRendu', on_delete=models.CASCADE, null=True, blank=True)
  
class CompteRendu(models.Model):
    bilan = models.ForeignKey(BilanRadiologique, on_delete=models.CASCADE, null=True)
    summary = models.TextField(blank=True,null=True)
    
class RadioImage(models.Model):
    compteRendu = models.ForeignKey(CompteRendu, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='radio_images/')  
    observation = models.CharField(max_length=255, blank=True,null=True)  
    
class BilanBiologique(models.Model):
    consultation = models.ForeignKey(Consultation, on_delete=models.CASCADE)
    labtechnician = models.ForeignKey(Worker, on_delete=models.CASCADE)
    title = models.CharField(max_length=50)
    description = models.TextField(max_length=255)
    priority = models.CharField(max_length=10)
    
    
class LabImage(models.Model):
    bilan = models.ForeignKey(BilanBiologique, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='bilan_images/')   
    
class LabObservation(models.Model):
    bilan = models.ForeignKey(BilanBiologique, on_delete=models.CASCADE)
    observation = models.CharField(max_length=255, blank=True,null=True)  
    

class DemandCertificate(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    doctor = models.ForeignKey(Worker, on_delete=models.CASCADE)
    done = models.BooleanField(default=False)
    date = models.DateTimeField(auto_now_add=True)
    
class DemandFacture(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    done = models.BooleanField(default=False)
    date = models.DateTimeField(auto_now_add=True)