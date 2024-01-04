from django.db import models
from django.core.serializers.json import DjangoJSONEncoder

class Settlement(models.Model):
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    processed = models.BooleanField(default=False)

    def __str__(self) -> str:
        return f'{self.start_date} - {self.end_date}'

class SettlementDetails(models.Model):
    settlement = models.ForeignKey(Settlement, on_delete=models.CASCADE)
    worker = models.ForeignKey("workers.Worker", on_delete=models.CASCADE)
    monday = models.FloatField(default=0.0)
    tuesday = models.FloatField(default=0.0)
    wednesday = models.FloatField(default=0.0)
    thursday = models.FloatField(default=0.0)
    friday = models.FloatField(default=0.0)
    saturday = models.FloatField(default=0.0)
    sunday = models.FloatField(default=0.0)
    ordinary_hours = models.FloatField(default=0.0)
    daytime_overtime = models.FloatField(default=0.0)
    night_surcharge_hours = models.FloatField(default=0.0)
    night_overtime = models.FloatField(default=0.0)
    holiday_hours = models.FloatField(default=0.0)
    night_holiday_hours = models.FloatField(default=0.0)
    daytime_holiday_overtime = models.FloatField(default=0.0)
    night_holiday_overtime = models.FloatField(default=0.0)
    working_shifts = models.JSONField(encoder=DjangoJSONEncoder, default=None)