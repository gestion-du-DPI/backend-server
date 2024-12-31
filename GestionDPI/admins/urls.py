from django.urls import path,include
from admins.views import AdminOnlyView,CreatePatientView,CreateWorkerView,DeleteUser,GetPatientsList,GetWorkersList,ModifyUser,GenerateQRView,getUserView,ModifyMyUser
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('home',AdminOnlyView.as_view(),name ='admin_home'),
    path('create/patient',CreatePatientView.as_view(),name ='create_patient'),
    path('create/worker',CreateWorkerView.as_view(),name ='create_patient'),
    path('deleteuser/<int:pk>', DeleteUser.as_view(), name='user_delete'),
    path('modifyuser/<int:pk>', ModifyUser.as_view(), name='myuser_modify'),
    path('modifymyuser', ModifyMyUser.as_view(), name='user_modify'),
    path('myuser', getUserView.as_view(), name='user_info'),
    path('patients',GetPatientsList.as_view(),name ='get_patients'),
    path('workers',GetWorkersList.as_view(),name ='get_workers'),
    path('getqr',GenerateQRView.as_view(),name='generate_qr')
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
