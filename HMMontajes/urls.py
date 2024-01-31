"""
URL configuration for HMMontajes project.
"""
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

urlpatterns = [
    path('admin/', admin.site.urls),
    path('__debug__/', include('debug_toolbar.urls')),
    path('settlement/', include('settlement.urls')),
    path('workers/', include('workers.urls')),
    path('', lambda request: redirect('/workers/upload-signings'), name='index'),
    path('api/', include('workers.api.urls')),
]
