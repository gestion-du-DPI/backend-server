from django.urls import path
from . import views 
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('dashboard/get_open_tickets', view= views.GetAllLabTicketsView.as_view()),
    path('dashboard/submit_result', view= views.SubmitResult.as_view()),
    path('dashboard/add_image', view= views.AddImage.as_view()),
    path('dashboard/del_image/<int:id>', view= views.DelImage.as_view()),
    path('dashboard/get_result/<int:ticket_id>', view= views.GetResult.as_view()),
    path('get_patients_list', view= views.GetPatientListView.as_view()),
    path('get_patient/<str:nss>', view= views.GetPatientByNSS.as_view()),
    path('get_tickets_list', view= views.GetTicketListView.as_view()),
    path('get_ticket/<int:id>', view= views.GetTicketByID.as_view()),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)