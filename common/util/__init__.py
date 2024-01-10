from datetime import datetime, timedelta

def normalize_date(datetime: datetime, signed_type: str) -> datetime:
    if signed_type == 'E':
        if 0 <= datetime.minute <= 6:
            # goes to hour o'clock
            datetime = datetime.replace(minute=0, second=0)
        elif 6 < datetime.minute < 36:
            # goes to hour and half
            datetime = datetime.replace(minute=30, second=0)
        elif 36 <= datetime.minute <= 59:
            # goes to next hour o'clock
            datetime = datetime + timedelta(hours=1)
            datetime = datetime.replace(minute=0, second=0)
    elif signed_type == 'S':
        if 0 <= datetime.minute <= 15:
            # goes to hour o'clock
            datetime = datetime.replace(minute=0, second=0)
        elif 15 < datetime.minute < 36:
            # goes to hour and half
            datetime = datetime.replace(minute=30, second=0)
        elif 36 <= datetime.minute <= 59:
            # goes to next hour o'clock
            datetime = datetime + timedelta(hours=1)
            datetime = datetime.replace(minute=0, second=0)
        
        if 6 <= datetime.hour <= 7:
            #Fixes outcome of worker when its 6 am of next day
            datetime = datetime.replace(hour=6, minute=0)
    return datetime

def get_start_end_week_dates(datetime: datetime):
    days_to_monday = datetime.weekday()
    monday_date = datetime - timedelta(days=days_to_monday)
    start_date = monday_date.replace(hour=6, minute=0, second=0)
    end_date = start_date + timedelta(days=7)
    return start_date, end_date

def get_hours_difference(start_date: datetime, end_date: datetime) -> float:
    time_difference = end_date - start_date
    return time_difference.total_seconds() / 3600