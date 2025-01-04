from django.urls import path
from .views import PatientDashboardView, ConsultationDetailView , ModifyMyUser

urlpatterns = [
    path('home/', PatientDashboardView.as_view(), name='patient_home'),
    path('consultations/<int:consultation_id>/', ConsultationDetailView.as_view(), name='consultation-detail'),
    path('editProfile/', ModifyMyUser.as_view(), name='EditPatientProfile'),
]
