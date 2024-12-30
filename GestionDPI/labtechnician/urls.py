from django.urls import path
from . import views 

urlpatterns = [
    path('dashboard/', view= views.DashboardView.as_view())
]
