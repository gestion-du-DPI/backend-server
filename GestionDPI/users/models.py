from django.db import models
from django.contrib.auth.models import User
# Create your models here.
# Hospital Model
class Hospital(models.Model):
    name = models.CharField(max_length=50, unique=True)

# Base User Model
class AppUser(models.Model):
    ROLE_CHOICES = [
        ('Admin', 'Admin'),
        ('Doctor', 'Doctor'),
        ('Nurse', 'Nurse'),
        ('Radiologist', 'Radiologist'),
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
   