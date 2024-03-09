from django.urls import path, include
from rest_framework import routers
from . import views

router = routers.DefaultRouter()
router.register(r'payrolls', views.PayrollView, 'payrolls')

urlpatterns = [
    path('api/v1/', include(router.urls)),
    path('api/v1/create/', views.create_payroll, name="create_payroll"),
    path('api/v1/export/', views.export_payroll, name="export_payroll"),
]