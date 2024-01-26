from django.db import models
from datetime import datetime, timedelta

class Holiday(models.Model):
    holiday_date = models.DateField()

    def __str__(self) -> str:
        return f'{self.holiday_date}'