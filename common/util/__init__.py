from datetime import datetime, timedelta

def normalize_date(datetime: datetime) -> datetime:
    if datetime.minute > 53:
        # goes to next hour and 30
        datetime = datetime + timedelta(hours=1)
        datetime = datetime.replace(minute=30, second=0)
        return datetime
    if datetime.minute <= 23:
        # goes to hour and 30
        datetime = datetime.replace(minute=30, second=0)
        return datetime
    if 23 < datetime.minute <= 53:
        # goes to next hour o'clock
        datetime = datetime + timedelta(hours=1)
        datetime = datetime.replace(minute=0, second=0)
        return datetime
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