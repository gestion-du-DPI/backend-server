from django.contrib import admin
from doctor.models import Consultation, Prescription, Medicine,PrescriptionDetail,RadioImage,LabImage,LabObservation,RadioObservation,NursingObservation,NursingResult,RadioResult,LabResult,Ticket
# Register your models here.

admin.site.register(Consultation)
admin.site.register(Prescription)
admin.site.register(Medicine)
admin.site.register(PrescriptionDetail)
admin.site.register(LabResult)
admin.site.register(RadioResult)
admin.site.register(Ticket)
admin.site.register(NursingResult)
admin.site.register(RadioImage)
admin.site.register(LabImage)
admin.site.register(LabObservation)
admin.site.register(RadioObservation)
admin.site.register(NursingObservation)

