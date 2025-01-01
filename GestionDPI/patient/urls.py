from django.urls import path
from .views import PatientDashboardView, ConsultationDetailView , EditPatientProfileView

urlpatterns = [
    path('dashboard/', PatientDashboardView.as_view(), name='patient-dashboard'),
    path('consultations/<int:consultation_id>/', ConsultationDetailView.as_view(), name='consultation-detail'),
    path('editProfile/', EditPatientProfileView.as_view(), name='EditPatientProfile'),
]
