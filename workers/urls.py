from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name="index"),
    path('upload-signings', views.upload_signings, name="upload-signings"),
]