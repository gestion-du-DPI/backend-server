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
    Gender_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female')
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    gender = models.CharField(max_length=10,choices=Gender_CHOICES)
    phone_number = models.CharField(max_length=20)
    address = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    nss = models.CharField(max_length=50, unique=True)
    date_of_birth = models.DateField()
    place_of_birth = models.CharField(max_length=50)
    image = models.ImageField(upload_to='user_images/', blank=True, null=True)
    

class Patient(models.Model):
    user = models.OneToOneField(AppUser, on_delete=models.CASCADE)
    emergency_contact_name = models.CharField(max_length=20)
    emergency_contact_phone = models.CharField(max_length=20)
    medical_condition = models.TextField()
    
class Worker(models.Model):
    user = models.OneToOneField(AppUser, on_delete=models.CASCADE)
  
    speciality  = models.CharField(max_length=50)
  
# Admin Model
class Admin(models.Model):
    user = models.OneToOneField(AppUser, on_delete=models.CASCADE)
   