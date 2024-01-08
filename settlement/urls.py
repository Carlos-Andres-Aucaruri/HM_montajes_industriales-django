from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name="index"),
    path('view/<str:pk>', views.view, name="view"),
    path('process-signing/<str:pk>', views.process_signing, name="process-signing"),
    path('export-settlement/<str:pk>', views.export_settlement, name="export-settlement"),
    path('room/<str:pk>', views.room, name="room"),
]