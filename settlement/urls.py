from django.urls import path, include
from rest_framework import routers
from . import views

router = routers.DefaultRouter()
router.register(r'settlements', views.SettlementView, 'settlements')
router.register(r'settlement-details', views.SettlementDetailView, 'settlement-details')

urlpatterns = [
    path('', views.index, name="settlement_index"),
    path('view/<str:pk>', views.view, name="settlement_view"),
    path('process-signing/<str:pk>', views.process_signing, name="process-signing"),
    path('export-settlement/<str:pk>', views.export_settlement, name="export-settlement"),
    path('api/v1/', include(router.urls)),
    path('api/v1/process/', views.process_settlement, name="process_settlement"),
    path('api/v1/export/', views.export_settlement, name="export_settlement"),
]