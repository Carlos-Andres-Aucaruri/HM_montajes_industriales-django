from django.urls import path, include
from rest_framework import routers
from . import views

urlpatterns = [
    path('api/v1/create/', views.create_payroll, name="create_payroll"),
]