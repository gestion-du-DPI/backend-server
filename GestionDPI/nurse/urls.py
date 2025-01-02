from django.urls import path
from . import views 
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('dashboard/get_open_tickets', view= views.GetOpenTicketsView.as_view()),
    path('dashboard/submit_result', view= views.SubmitResult.as_view()),
    path('dashboard/get_result/<int:ticket_id>', view= views.GetResult.as_view()),
    path('get_patients_list', view= views.GetPatientListView.as_view()),
    path('get_patient/<str:nss>', view= views.GetPatientByNSS.as_view()),
    path('get_ticket_history', view= views.GetTicketHistoryView.as_view()),
    path('get_ticket/<int:id>', view= views.GetTicketByID.as_view()),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)