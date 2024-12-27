from django.contrib import admin
from doctor.models import Consultation, Prescription, Medicine,PrescriptionDetail,BilanBiologique,BilanRadiologique,RadioImage,LabImage,LabObservation,CompteRendu
# Register your models here.

admin.site.register(Consultation)
admin.site.register(Prescription)
admin.site.register(Medicine)
admin.site.register(PrescriptionDetail)
admin.site.register(BilanBiologique)
admin.site.register(BilanRadiologique)
admin.site.register(RadioImage)
admin.site.register(LabImage)
admin.site.register(LabObservation)
admin.site.register(CompteRendu)
