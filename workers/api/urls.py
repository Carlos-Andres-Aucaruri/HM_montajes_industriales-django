from django.urls import path
from . import views

urlpatterns = [
    path('', views.getRoutes),
    path('workers/', views.getWorkers),
    path('workers/<str:pk>', views.getWorker),
    path('signings/', views.getSignings),
    path('signings/<str:worker_id>', views.getSigningsByWorker),
]