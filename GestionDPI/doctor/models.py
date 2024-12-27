from django.db import models
from users.models import Patient,Worker
# Create your models here.
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
    