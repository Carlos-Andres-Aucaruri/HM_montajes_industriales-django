from django.db import models
from django.core.serializers.json import DjangoJSONEncoder
from datetime import datetime, timedelta
from common.util import get_hours_difference
from holidays.models import Holiday

class Settlement(models.Model):
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    processed = models.BooleanField(default=False)

    def __str__(self) -> str:
        return f'{self.start_date} - {self.end_date}'

    def get_days_dict(self):
        days_dict = {}
        current_date = self.start_date
        while current_date < self.end_date:
            day_name = current_date.strftime('%A').lower()
            days_dict[day_name] = current_date.day
            current_date += timedelta(days=1)
        return days_dict

class SettlementDetails(models.Model):
    def working_shifts_default():
        return {
            'monday': {'start': '', 'end': '', 'start_normalized': '', 'end_normalized': ''},
            'tuesday': {'start': '', 'end': '', 'start_normalized': '', 'end_normalized': ''},
            'wednesday': {'start': '', 'end': '', 'start_normalized': '', 'end_normalized': ''},
            'thursday': {'start': '', 'end': '', 'start_normalized': '', 'end_normalized': ''},
            'friday': {'start': '', 'end': '', 'start_normalized': '', 'end_normalized': ''},
            'saturday': {'start': '', 'end': '', 'start_normalized': '', 'end_normalized': ''},
            'sunday': {'start': '', 'end': '', 'start_normalized': '', 'end_normalized': ''},
        }

    settlement = models.ForeignKey(Settlement, on_delete=models.CASCADE, related_name='details')
    worker = models.ForeignKey("workers.Worker", on_delete=models.CASCADE)
    monday = models.FloatField(default=0.0)
    tuesday = models.FloatField(default=0.0)
    wednesday = models.FloatField(default=0.0)
    thursday = models.FloatField(default=0.0)
    friday = models.FloatField(default=0.0)
    saturday = models.FloatField(default=0.0)
    sunday = models.FloatField(default=0.0)
    total_hours = models.FloatField(default=0.0)
    ordinary_hours = models.FloatField(default=0.0)
    daytime_overtime = models.FloatField(default=0.0)
    night_surcharge_hours = models.FloatField(default=0.0)
    night_overtime = models.FloatField(default=0.0)
    holiday_hours = models.FloatField(default=0.0)
    night_holiday_hours = models.FloatField(default=0.0)
    daytime_holiday_overtime = models.FloatField(default=0.0)
    night_holiday_overtime = models.FloatField(default=0.0)
    working_shifts = models.JSONField(encoder=DjangoJSONEncoder, default=working_shifts_default)

    # This variable should be a constant elsewhere
    __weekly_hours_needed = 47
    __weekly_hours_completed = 0
    __holiday_dict = {}
    # Defines the normal hours during holidays, and if the counter is over 8 then increases extra hours
    __holiday_hours_dict = {}

    class Meta:
        verbose_name_plural = 'Settlement details'

    def __str__(self) -> str:
        return f'HO: {self.ordinary_hours} | HED: {self.daytime_overtime} | HRN: {self.night_surcharge_hours} | HEN: {self.night_overtime} | HF: {self.holiday_hours} | HFN: {self.night_holiday_hours} | HEFD: {self.daytime_holiday_overtime} | HEFN: {self.night_holiday_overtime}'
    
    def __set_working_shift_day(self, start_date: datetime, end_date: datetime, start_date_normalized: datetime, end_date_normalized: datetime, total_hours: float):
        working_shift = {'start': start_date, 'end': end_date, 'start_normalized': start_date_normalized, 'end_normalized': end_date_normalized}
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

    '''
    Classifies hours per day using a day shift and saves the dayshift in working_shifts
    '''
    def classify_hours(self, start_day_time: datetime, end_day_time: datetime, start_day_raw_time: datetime, end_day_raw_time: datetime):
        total_day_hours = get_hours_difference(start_day_time, end_day_time)
        is_food_included = False if total_day_hours > 8 else True

        start_day = datetime(start_day_time.year, start_day_time.month, start_day_time.day, 6, 0, 0, 0, start_day_time.tzinfo)
        end_day = start_day + timedelta(days=1)
        # Lunch time between 12 and 1 pm added only when is_food_included
        start_lunch = datetime(start_day_time.year, start_day_time.month, start_day_time.day, 12, 0, 0, 0, start_day_time.tzinfo)
        end_lunch = start_lunch + timedelta(hours=1)
        # Eating time between 9 and 10 pm added only when is_food_included
        start_dinner = datetime(start_day_time.year, start_day_time.month, start_day_time.day, 21, 0, 0, 0, start_day_time.tzinfo)
        end_dinner = start_dinner + timedelta(hours=1)

        remaining_hours = total_day_hours
        total_day_hours = 0.0
        current_time = start_day_time
        is_holiday = self.is_holiday(current_time)
        while remaining_hours > 0.0:
            if (start_lunch <= current_time < end_lunch) or (start_dinner <= current_time < end_dinner):
                current_time = current_time + timedelta(minutes=30)
                remaining_hours -= 0.5
                if is_food_included:
                    total_day_hours += 0.5
                    is_daytime = current_time < start_dinner
                    self.__increase_hours(is_daytime, is_holiday, current_time)
                continue
            is_daytime = (start_day <= current_time < start_dinner) or (current_time >= end_day)
            self.__increase_hours(is_daytime, is_holiday, current_time)
            current_time = current_time + timedelta(minutes=30)
            is_holiday = self.is_holiday(current_time)
            total_day_hours += 0.5
            remaining_hours -= 0.5
        self.__set_working_shift_day(start_day_raw_time, end_day_raw_time, start_day_time, end_day_time, total_day_hours)

    def __increase_hours(self, is_daytime: bool, is_holiday: bool, current_time: datetime):
        str_current_time = current_time.strftime("%Y-%m-%d")
        if is_holiday:
            if self.__holiday_hours_dict.get(str_current_time) is None:
                self.__holiday_hours_dict[str_current_time] = 0

            if is_daytime:
                if self.__holiday_hours_dict[str_current_time] < 8:
                    self.holiday_hours += 0.5
                    self.__holiday_hours_dict[str_current_time] = self.__holiday_hours_dict[str_current_time] + 0.5
                else:
                    self.daytime_holiday_overtime += 0.5
            else:
                if self.__holiday_hours_dict[str_current_time] < 8:
                    self.night_holiday_hours += 0.5
                    self.__holiday_hours_dict[str_current_time] = self.__holiday_hours_dict[str_current_time] + 0.5
                else:
                    self.night_holiday_overtime += 0.5
        else:
            if is_daytime:
                if self.__weekly_hours_completed < self.__weekly_hours_needed:
                    self.ordinary_hours += 0.5
                    self.__weekly_hours_completed += 0.5
                else:
                    self.daytime_overtime += 0.5
            else:
                if self.__weekly_hours_completed < self.__weekly_hours_needed:
                    self.night_surcharge_hours += 0.5
                    self.__weekly_hours_completed += 0.5
                else:
                    self.night_overtime += 0.5

    def set_total_hours(self):
        self.total_hours = self.monday + self.tuesday + self.wednesday + self.thursday + self.friday + self.saturday + self.sunday

    def reset_hours(self):
        self.ordinary_hours = 0.0
        self.daytime_overtime = 0.0
        self.night_surcharge_hours = 0.0
        self.night_overtime = 0.0
        self.holiday_hours = 0.0
        self.night_holiday_hours = 0.0
        self.daytime_holiday_overtime = 0.0
        self.night_holiday_overtime = 0.0
    
    def reset_weekly_counters(self):
        self.__weekly_hours_completed = 0
        for key in self.__holiday_hours_dict:
            self.__holiday_hours_dict[key] = 0

    def set_week_holidays(self):
        start_date = self.settlement.start_date
        end_date = self.settlement.end_date
        start_date = datetime(start_date.year, start_date.month, start_date.day)
        end_date = datetime(end_date.year, end_date.month, end_date.day)
        holidays_list = Holiday.objects.filter(holiday_date__range=(start_date, end_date)).all()
        self.__holiday_dict = {holiday.holiday_date.strftime("%Y-%m-%d"): holiday.holiday_date for holiday in holidays_list}

    def is_holiday(self, date):
        if date.weekday() == 6:
            return True
        if date.strftime("%Y-%m-%d") in self.__holiday_dict:
            return True
        return False

    def set_weekly_hours_needed(self):
        for str_holiday, holiday_date in self.__holiday_dict.items():
            if holiday_date.weekday() == 6:
                continue
            # Fix when the next monday is holiday, that monday is not included
            if holiday_date.weekday() == 0 and str_holiday == self.settlement.end_date.strftime("%Y-%m-%d"):
                continue
            if self.__weekly_hours_needed == 47:
                self.__weekly_hours_needed -= 7
            else:
                self.__weekly_hours_needed -= 8
