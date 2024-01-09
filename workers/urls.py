from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name="worker_index"),
    path('view/<str:pk>', views.view, name="worker_view"),
    path('signings/', views.signings, name="signings_index"),
    path('upload-signings', views.upload_signings, name="upload_signings"),
]