from django.urls import path,include
from doctor.views import DoctorOnlyView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('home',DoctorOnlyView.as_view(),name ='doctor_home'),
   
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
