from django.contrib.auth.models import AbstractUser
from django.db import models

# Hospital Model
class Hospital(models.Model):
    name = models.CharField(max_length=50, unique=True)

# Base User Model
class User(AbstractUser):
    ROLE_CHOICES = [
        ('Admin', 'Admin'),
        ('Doctor', 'Doctor'),
        ('Nurse', 'Nurse'),
        ('Pharmacist', 'Pharmacist'),
        ('LabTechnician', 'LabTechnician'),
        ('Patient', 'Patient')
    ]
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    phone_number = models.CharField(max_length=20)
    address = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

# Patient Model
class Patient(model.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    gender = models.CharField(max_length=10)
    nss = models.CharField(max_length=50, unique=True)
    date_of_birth = models.DateField()
    place_of_birth = models.CharField(max_length=50)
    emergency_contact_name = models.CharField(max_length=20)
    emergency_contact_phone = models.CharField(max_length=20)
    medical_condition = models.TextField()
    
# Worker Model
class Worker(model.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    gender = models.CharField(max_length=10)
    date_of_birth = models.DateField()
    place_of_birth = models.CharField(max_length=50)
    speciality = place_of_birth = models.CharField(max_length=50, unique=True)
  
# Admin Model
class Admin(model.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
   
# Consultation Model
class Consultation(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    doctor = models.ForeignKey( Worker, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    summary = models.TextField()
    notes = models.TextField(blank=True, null=True)   

# Prescription Model
class Prescription(models.Model):
    consultation = models.ForeignKey(Consultation, on_delete=models.CASCADE)
    valid = models.BooleanField(default=False)
    medicines = models.ManyToManyField(Medicine, through='PrescriptionDetail')

class PrescriptionDetail(models.Model):
    prescription = models.ForeignKey(Prescription, on_delete=models.CASCADE)
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE)
    dosage = models.CharField(max_length=50)
    duration = models.CharField(max_length=50)
    instructions = models.TextField(blank=True, null=True)
    
class Medicine(models.Model):
    name = models.CharField(max_length=100)



class NurseNote(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    nurse = models.ForeignKey(Worker, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    actions_taken = models.TextField(blank=True, null=True)
    observations = models.TextField()

class DemandeCerteficat(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    doctor = models.ForeignKey(Worker, on_delete=models.CASCADE)
    done = models.BooleanField(default=False)
    date = models.DateTimeField(auto_now_add=True)
    
class DemandeFacture(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    done : models.BooleanField(default=False)
    date = models.DateTimeField(auto_now_add=True)
        