from django.db import models
from django.contrib.auth.models import User
from cloudinary.models import CloudinaryField
from django.core.exceptions import ValidationError

# Create your models here.
# Hospital Model
class Hospital(models.Model):
    name = models.CharField(max_length=50, unique=True)
    def __str__(self):
        return f"{self.name}"
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
    image = CloudinaryField('image', default='default_user')  
    def __str__(self):
        return f"{self.user.first_name}_{self.role}"
    def clean(self):
        if self.role not in dict(self.ROLE_CHOICES):
            raise ValidationError({'role': f"{self.role} is not a valid choice."})
        if self.gender not in dict(self.Gender_CHOICES):
            raise ValidationError({"We dont support LGBTQ"})

    def save(self, *args, **kwargs):
        self.full_clean() 
        super().save(*args, **kwargs)
    

class Patient(models.Model):
    user = models.OneToOneField(AppUser, on_delete=models.CASCADE)
    emergency_contact_name = models.CharField(max_length=20)
    emergency_contact_phone = models.CharField(max_length=20)
    medical_condition = models.TextField()
    def __str__(self):
        return f"{self.user.user.first_name}"
    
    def number_of_consultations(self):
        return self.consultation_set.count()
        
    
class Worker(models.Model):
    user = models.OneToOneField(AppUser, on_delete=models.CASCADE)
  
    speciality  = models.CharField(max_length=50)
    def __str__(self):
        
        return f"{self.user.user.first_name}_{self.user.role}"

# Admin Model
class Admin(models.Model):
    user = models.OneToOneField(AppUser, on_delete=models.CASCADE)
