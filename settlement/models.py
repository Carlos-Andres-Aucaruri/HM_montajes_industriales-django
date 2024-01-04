from django.db import models
from django.core.serializers.json import DjangoJSONEncoder
from datetime import datetime

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

    def classify_hours(self, start_date: datetime, end_date: datetime):
        MORNING = 0
        AFTERNOON = 1
        EVENING = 2

        print(f'TURN STARTED AT {start_date} AND FINISHED AT {end_date}')
        if start_date.hour < 10:
            time_of_day = MORNING
        elif 10 <= start_date.hour < 17:
            time_of_day = AFTERNOON
        elif start_date.hour >= 17:
            time_of_day = EVENING

        if time_of_day == MORNING:
            time_difference = end_date - start_date
            total_hours = time_difference.total_seconds() / 3600
            remaining_hours = total_hours-8
            ordinary_hours = 8 if remaining_hours > 0 else total_hours
            daytime_overtime = remaining_hours if remaining_hours > 0 else 0
            print(f'HO: {ordinary_hours} | HE: {daytime_overtime}')

        pass

    def classify_week(self):
        pass