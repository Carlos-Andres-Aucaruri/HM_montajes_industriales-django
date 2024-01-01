from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name="home"),
    path('upload-signings', views.upload_signings, name="upload-signings"),
]