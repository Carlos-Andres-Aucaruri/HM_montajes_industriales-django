from django.contrib import admin
from .models import Settlement, SettlementDetails

# Register your models here.
admin.site.register(Settlement)
admin.site.register(SettlementDetails)