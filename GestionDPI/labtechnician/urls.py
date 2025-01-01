from django.urls import path
from . import views 
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('dashboard/get_tickets', view= views.GetAllLabTicketsView.as_view()),
    path('dashboard/add_observation', view= views.SetObservation.as_view()),
    path('dashboard/add_image', view= views.SetImage.as_view()),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)