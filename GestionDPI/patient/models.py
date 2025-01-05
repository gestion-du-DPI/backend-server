from django.db import models
from users.models import Patient,Worker
# Create your models here.
class DemandCertificate(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    doctor = models.ForeignKey(Worker, on_delete=models.CASCADE)
    done = models.BooleanField(default=False)
    date = models.DateTimeField(auto_now_add=True)
    
class DemandFacture(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    done = models.BooleanField(default=False)
    date = models.DateTimeField(auto_now_add=True)
