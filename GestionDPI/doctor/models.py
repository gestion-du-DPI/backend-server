from django.db import models
from users.models import Patient,Worker,Hospital
from cloudinary.models import CloudinaryField
from django.core.exceptions import ValidationError

# Create your models here.
# Consultation Model
class Consultation(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    doctor = models.ForeignKey(Worker, on_delete=models.CASCADE)
    PRIORITY_CHOICES = [
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('Critical', 'Critical')
    ]
    priority = models.CharField(max_length=20,choices=PRIORITY_CHOICES)
    reason = models.CharField(max_length=80)
    archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    resume = models.TextField(blank=True, null=True)
    def clean(self):
        if self.priority not in dict(self.PRIORITY_CHOICES):
            raise ValidationError({'priority': f"{self.priority} is not a valid choice."})

    def save(self, *args, **kwargs):
        self.full_clean() 
        super().save(*args, **kwargs)
       
    

class Medicine(models.Model):
    name = models.CharField(max_length=100)


class Prescription(models.Model):
    consultation = models.ForeignKey(Consultation, on_delete=models.CASCADE)
    Status_CHOICES = [
        ('Pending', 'Pending'),
        ('Completed', 'Completed'),
        ('Failed', 'Failed')
    ]
    status = models.CharField(max_length=20,choices=Status_CHOICES)
    medicines = models.ManyToManyField(Medicine, through='PrescriptionDetail')
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def clean(self):
        if self.status not in dict(self.Status_CHOICES):
            raise ValidationError({'status': f"{self.status} is not a valid choice."})

    def save(self, *args, **kwargs):
        self.full_clean() 
        super().save(*args, **kwargs)
    

class PrescriptionDetail(models.Model):
    prescription = models.ForeignKey(Prescription, on_delete=models.CASCADE)
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE)
    dosage = models.CharField(max_length=50)
    duration = models.CharField(max_length=50)
    frequency = models.CharField(max_length=50)
    instructions = models.TextField(blank=True, null=True)
    
class Ticket(models.Model):
    consultation = models.ForeignKey(Consultation, on_delete=models.CASCADE)
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE)
    TYPE_CHOICES = [
        ('Lab', 'Lab'),
        ('Radio', 'Radio'),
        ('Nursing', 'Nursing')
    ]
    PRIORITY_CHOICES = [
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('Critical', 'Critical')
    ]
    STATUS_CHOICES = [
        ('Open', 'Open'),
        ('Closed', 'Closed')
    ]
    type = models.CharField(max_length=20,choices=TYPE_CHOICES)
    title = models.CharField(max_length=50)
    description = models.TextField(max_length=255)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default= 'Open')
    created_at = models.DateTimeField(auto_now_add=True)
    def clean(self):
        if self.type not in dict(self.TYPE_CHOICES)  :
            raise ValidationError({'type': f"{self.type} is not a valid choice."})
        if  self.priority not in dict(self.PRIORITY_CHOICES):
            raise ValidationError({'priority': f"{self.priority} is not a valid choice."})
        if  self.status not in dict(self.STATUS_CHOICES):
            raise ValidationError({'status': f"{self.status} is not a valid choice."})
    def save(self, *args, **kwargs):
        self.full_clean() 
        super().save(*args, **kwargs)
    
    
class LabResult(models.Model):
    ticket = models.OneToOneField(Ticket,on_delete=models.CASCADE)
    labtechnician = models.ForeignKey(Worker, on_delete=models.CASCADE)
  
class LabImage(models.Model):
    labresult = models.ForeignKey(LabResult, on_delete=models.CASCADE)
    image = CloudinaryField('image')  
    
class LabObservation(models.Model):
    labresult = models.ForeignKey(LabResult, on_delete=models.CASCADE)
    title = models.CharField(max_length=80)  
    notes = models.TextField(max_length=255, blank=True,null=True)  

class RadioResult(models.Model):
    ticket = models.OneToOneField(Ticket,on_delete=models.CASCADE)
    radiologist = models.ForeignKey(Worker, on_delete=models.CASCADE)
  
class RadioImage(models.Model):
    radioresult = models.ForeignKey(RadioResult, on_delete=models.CASCADE)
    image = CloudinaryField('image')    
    
class RadioObservation(models.Model):
    radioresult = models.ForeignKey(RadioResult, on_delete=models.CASCADE)
    title = models.CharField(max_length=80)  
    notes = models.TextField(max_length=255, blank=True,null=True)  
    
class NursingResult(models.Model):
    ticket = models.OneToOneField(Ticket,on_delete=models.CASCADE)
    nurse = models.ForeignKey(Worker, on_delete=models.CASCADE)
  
class NursingObservation(models.Model):
    nursingresult = models.ForeignKey(NursingResult, on_delete=models.CASCADE)
    title = models.CharField(max_length=80)  
    notes = models.TextField(max_length=255, blank=True,null=True)  
    
