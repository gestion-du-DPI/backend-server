from django.db import models
from users.models import Patient,Worker
# Create your models here.
class NurseNote(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    nurse = models.ForeignKey(Worker, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    actions_taken = models.TextField(blank=True, null=True)
    observations = models.TextField()