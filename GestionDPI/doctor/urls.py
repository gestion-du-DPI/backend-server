from django.urls import path,include
from doctor.views import DoctorOnlyView,GetPatientView,ModifyMyUser,GetPatientsList,CreateConultationView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('home',DoctorOnlyView.as_view(),name ='doctor_home'),
    path('getpatient',GetPatientView.as_view(),name ='get_patient'),
    path('modifymyuser', ModifyMyUser.as_view(), name='myuser_modify'),
    path('patients', GetPatientsList.as_view(), name='patients_list'),
    path('consultation/create', CreateConultationView.as_view(), name='create_consultation'),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
