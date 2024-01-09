from django.db import models
from django.core.serializers.json import DjangoJSONEncoder
from datetime import datetime, timedelta
from common.util import get_hours_difference

class Settlement(models.Model):
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    processed = models.BooleanField(default=False)

    def __str__(self) -> str:
        return f'{self.start_date} - {self.end_date}'

class SettlementDetails(models.Model):
    def working_shifts_default():
        return {
            'monday': None,
            'tuesday': None,
            'wednesday': None,
            'thursday': None,
            'friday': None,
            'saturday': None,
            'sunday': None,
        }

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
    working_shifts = models.JSONField(encoder=DjangoJSONEncoder, default=working_shifts_default)

    class Meta:
        verbose_name_plural = 'Settlement details'

    def __str__(self) -> str:
        return f'HO: {self.ordinary_hours} | HED: {self.daytime_overtime} | HRN: {self.night_surcharge_hours} | HEN: {self.night_overtime} | HF: {self.holiday_hours} | HFN: {self.night_holiday_hours} | HEFD: {self.daytime_holiday_overtime} | HEFN: {self.night_holiday_overtime}'
    
    def set_working_shift_day(self, start_date: datetime, end_date: datetime, total_hours: float):
        working_shift = {'start': start_date, 'end': start_date}
        if start_date.weekday() == 0:
            self.monday = total_hours
            self.working_shifts['monday'] = working_shift
        elif start_date.weekday() == 1:
            self.tuesday = total_hours
            self.working_shifts['tuesday'] = working_shift
        elif start_date.weekday() == 2:
            self.wednesday = total_hours
            self.working_shifts['wednesday'] = working_shift
        elif start_date.weekday() == 3:
            self.thursday = total_hours
            self.working_shifts['thursday'] = working_shift
        elif start_date.weekday() == 4:
            self.friday = total_hours
            self.working_shifts['friday'] = working_shift
        elif start_date.weekday() == 5:
            self.saturday = total_hours
            self.working_shifts['saturday'] = working_shift
        elif start_date.weekday() == 6:
            self.sunday = total_hours
            self.working_shifts['sunday'] = working_shift

    def classify_hours(self, start_date: datetime, end_date: datetime):
        # print(f'SHIFT STARTED AT {start_date} AND FINISHED AT {end_date}')
        total_hours = get_hours_difference(start_date, end_date)
        self.set_working_shift_day(start_date, end_date, total_hours)
        starting_day_time = datetime(start_date.year, start_date.month, start_date.day, 6, 0, 0, 0, start_date.tzinfo)
        finishing_day_time = starting_day_time + timedelta(days=1)
        # Lunch time between 12 and 1 pm not included when adding hours
        start_lunch_time = datetime(start_date.year, start_date.month, start_date.day, 12, 0, 0, 0, start_date.tzinfo)
        end_lunch_time = start_lunch_time + timedelta(hours=1)
        # Eating time between 9 and 10 pm not included when adding hours
        start_eat_time = datetime(start_date.year, start_date.month, start_date.day, 21, 0, 0, 0, start_date.tzinfo)
        end_eat_time = start_eat_time + timedelta(hours=1)
        remaining_hours = total_hours
        normal_hours = 0.0
        current_time = start_date
        is_holiday = True if current_time.weekday() == 6 else False
        while remaining_hours > 0.0:
            if (start_lunch_time <= current_time < end_lunch_time) or (start_eat_time <= current_time < end_eat_time):
                current_time = current_time + timedelta(minutes=30)
                remaining_hours -= 0.5
                continue
            if (starting_day_time <= current_time < start_eat_time) or (current_time >= finishing_day_time):
                if normal_hours < 8:
                    if is_holiday:
                        self.holiday_hours += 0.5
                    else:
                        self.ordinary_hours += 0.5
                    normal_hours += 0.5
                else:
                    if is_holiday:
                        self.daytime_holiday_overtime += 0.5
                    else:
                        self.daytime_overtime += 0.5
            else:
                if normal_hours < 8:
                    if is_holiday:
                        self.night_holiday_hours += 0.5
                    else:
                        self.night_surcharge_hours += 0.5
                    normal_hours += 0.5
                else:
                    if is_holiday:
                        self.night_holiday_overtime += 0.5
                    else:
                        self.night_overtime += 0.5
            current_time = current_time + timedelta(minutes=30)
            is_holiday = True if current_time.weekday() == 6 else False
            remaining_hours -= 0.5
        # print(self)
            
    def reset_hours(self):
        self.ordinary_hours = 0.0
        self.daytime_overtime = 0.0
        self.night_surcharge_hours = 0.0
        self.night_overtime = 0.0
        self.holiday_hours = 0.0
        self.night_holiday_hours = 0.0
        self.daytime_holiday_overtime = 0.0
        self.night_holiday_overtime = 0.0
