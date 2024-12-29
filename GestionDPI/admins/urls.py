from django.urls import path,include
from admins.views import AdminOnlyView,CreatePatientView,CreateWorkerView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('home/',AdminOnlyView.as_view(),name ='admin_home'),
    path('create/patient/',CreatePatientView.as_view(),name ='create_patient'),
    path('create/worker/',CreateWorkerView.as_view(),name ='create_patient')
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
