from django.contrib import admin
from patient.models import DemandCertificate,DemandFacture
# Register your models here.
admin.site.register(DemandCertificate)
admin.site.register(DemandFacture)