"""
URL configuration for HMMontajes project.
"""
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from rest_framework.documentation import include_docs_urls
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('__debug__/', include('debug_toolbar.urls')),
    path('settlement/', include('settlement.urls')),
    path('workers/', include('workers.urls')),
    path('', lambda request: redirect('/workers/upload-signings'), name='index'),
    path('api/', include('workers.api.urls')),
    path('docs/', include_docs_urls(title='HM API')),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
]
