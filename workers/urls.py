from django.urls import path, include
from rest_framework import routers
from . import views

router = routers.DefaultRouter()
router.register(r'workers', views.WorkerView, 'workers')
router.register(r'signings', views.SigningView, 'signings')

urlpatterns = [
    path('', views.index, name="worker_index"),
    path('view/<str:pk>', views.view, name="worker_view"),
    path('signings/', views.signings, name="signings_index"),
    path('upload-signings', views.upload_signings, name="upload_signings"),
    path('api/v1/', include(router.urls)),
    path('api/v1/import-signings/', views.import_signings, name="import_signings"),
]