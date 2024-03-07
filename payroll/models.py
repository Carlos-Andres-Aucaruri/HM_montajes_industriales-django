from django.db import models
from settlement.models import Settlement
from workers.models import Worker

class Payroll(models.Model):
    worker = models.ForeignKey(Worker, on_delete=models.CASCADE)
    total_hours = models.FloatField(default=0.0)
    ordinary_hours = models.FloatField(default=0.0)
    daytime_overtime = models.FloatField(default=0.0)
    night_surcharge_hours = models.FloatField(default=0.0)
    night_overtime = models.FloatField(default=0.0)
    holiday_hours = models.FloatField(default=0.0)
    night_holiday_hours = models.FloatField(default=0.0)
    daytime_holiday_overtime = models.FloatField(default=0.0)
    night_holiday_overtime = models.FloatField(default=0.0)

class SettlementPayroll(models.Model):
    settlement = models.ForeignKey(Settlement, on_delete=models.CASCADE, related_name='settlements')
    payroll = models.ForeignKey(Payroll, on_delete=models.CASCADE)
