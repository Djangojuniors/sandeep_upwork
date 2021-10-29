from django.urls import path
# from .ui.app import views
from . import views

urlpatterns = [
    path('', views.upload, name='upload'),
    path('display_data/', views.display_data, name='display_data'),
    ]
