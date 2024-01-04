from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import Worker, RawSignings
from settlement.models import Settlement
from datetime import datetime, timezone, timedelta
import pandas as pd

# Create your views here.
def home(request):
    return render(request, 'workers/home.html')

def upload_signings(request):
    if request.method == 'POST' and request.FILES['excel_file']:
        excel_file = request.FILES['excel_file']
        df = pd.read_excel(excel_file)

        dates = []
        for index, row in df.iterrows():
            if index > 3:
                document = row.iloc[10]
                name = row.iloc[2]
                worker = Worker.objects.filter(document=document).first()
                if not worker:
                    worker = Worker.objects.create(
                        document=document,
                        name=name,
                    )

                date_signed = row.iloc[1].replace(tzinfo=timezone(timedelta(hours=-5)))
                normalized_date_signed = normalize_date(date_signed)
                signed_type="E" if row.iloc[4] == "entrada" else "S"

                if not dates:
                    start_date, end_date = get_start_end_dates(normalized_date_signed)
                    dates.append({"start_date": start_date, "end_date": end_date})
                else:
                    found_in_week = False
                    for date_range in dates:
                        if date_range["start_date"] <= normalized_date_signed <= date_range["end_date"]:
                            found_in_week = True
                            break
                    if not found_in_week:
                        start_date, end_date = get_start_end_dates(normalized_date_signed)
                        dates.append({"start_date": start_date, "end_date": end_date})

                entry = RawSignings.objects.filter(worker=worker, date_signed=date_signed).first()
                if not entry:
                    RawSignings.objects.create(
                        folder_number=row.iloc[0],
                        date_signed=date_signed,
                        normalized_date_signed=normalized_date_signed,
                        worker=worker,
                        signed_type=signed_type,
                        door=row.iloc[5],
                        contract_number=row.iloc[6],
                    )
        
        for date_range in dates:
            settlement = Settlement.objects.filter(start_date=date_range["start_date"], end_date=date_range["end_date"]).first()
            if not settlement:
                Settlement.objects.create(
                    start_date=date_range["start_date"],
                    end_date=date_range["end_date"],
                )

        return redirect('/settlement/')

    return render(request, 'workers/upload_excel.html')

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

def get_start_end_dates(datetime: datetime):
    days_to_monday = datetime.weekday()
    monday_date = datetime - timedelta(days=days_to_monday)
    start_date = monday_date.replace(hour=6, minute=0, second=0)
    end_date = start_date + timedelta(days=7)
    return start_date, end_date