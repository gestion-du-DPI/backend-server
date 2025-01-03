from django.urls import path,include
from doctor.views import (
    DoctorOnlyView,
    GetPatientView,
    ModifyMyUser,
    GetPatientsList,
    CreateConultationView,
    getConultationView,
    getAttachmentsView,
    CreateTicketView,
    CreatePrescriptionView,
    ArchiveConsultationView,
    GetPrescriptionView,
    GetDPIView,
    GetLabImageView,
    GetRadioImageView,
    GetRadioObservationView,
    GetLabObservationView,
    GetNurseObservationView
)
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('home', DoctorOnlyView.as_view(), name='doctor_home'),
    path('getpatient', GetPatientView.as_view(), name='get_patient'),
    path('modifymyuser', ModifyMyUser.as_view(), name='myuser_modify'),
    path('patients', GetPatientsList.as_view(), name='patients_list'),
    path('consultation/create', CreateConultationView.as_view(), name='create_consultation'),
    path('consultation/get', getConultationView.as_view(), name='get_consultation'),
    path('consultation/attachments', getAttachmentsView.as_view(), name='get_attachments'),
    path('consultation/archive', ArchiveConsultationView.as_view(), name='archive_consultation'),
    path('ticket/create', CreateTicketView.as_view(), name='create_ticket'),
    path('prescription/create', CreatePrescriptionView.as_view(), name='create_prescription'),
    path('prescription/get', GetPrescriptionView.as_view(), name='get_prescription'),
    path('dpi/get', GetDPIView.as_view(), name='get_dpi'),
    path('lab/image/<int:id>', GetLabImageView.as_view(), name='get_lab_image'),
    path('radio/image/<int:id>', GetRadioImageView.as_view(), name='get_radio_image'),
    path('radio/observation/<int:id>', GetRadioObservationView.as_view(), name='get_radio_observation'),
    path('lab/observation/<int:id>', GetLabObservationView.as_view(), name='get_lab_observation'),
    path('nurse/observation/<int:id>', GetNurseObservationView.as_view(), name='get_nurse_observation')
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)