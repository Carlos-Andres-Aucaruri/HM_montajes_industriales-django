from django.contrib import admin
from .models import Worker, RawSignings

# Register your models here.
admin.site.register(Worker)
admin.site.register(RawSignings)