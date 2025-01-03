from django.urls import path
from .views import SetPrescriptionView, GetPrescriptionsView

urlpatterns = [
    path('set-prescription/', SetPrescriptionView.as_view(), name='set-prescription'),
    path('get-prescriptions/', GetPrescriptionsView.as_view(), name='get-prescriptions'),
]
