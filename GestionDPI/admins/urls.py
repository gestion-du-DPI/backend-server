from django.urls import path,include
from admins.views import AdminOnlyView

urlpatterns = [
    path('home/',AdminOnlyView.as_view(),name ='admin_home')
]
