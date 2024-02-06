from django.db import models
from datetime import datetime, timedelta

class Holiday(models.Model):
    holiday_date = models.DateField()
    holiday_name = models.CharField(max_length=200, default='')

    def __str__(self) -> str:
        return f'{self.holiday_date}: {self.holiday_name}'