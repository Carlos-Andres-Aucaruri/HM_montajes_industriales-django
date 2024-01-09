from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import Worker, RawSignings
from settlement.models import Settlement
from datetime import datetime, timezone, timedelta
import pandas as pd
from common.util import normalize_date, get_start_end_week_dates

# Create your views here.
def index(request):
    workers_list = Worker.objects.all()
    workers_per_page = 20
    paginator = Paginator(workers_list, workers_per_page)
    page = request.GET.get('page')
    try:
        workers = paginator.page(page)
    except PageNotAnInteger:
        workers = paginator.page(1)
    except EmptyPage:
        workers = paginator.page(paginator.num_pages)
    return render(request, 'workers/index.html', {'workers': workers})

def view(request, pk):
    worker = Worker.objects.get(id=int(pk))
    raw_signings_list = RawSignings.objects.filter(worker=worker).order_by('-date_signed').all()
    raw_signings_per_page = 20
    paginator = Paginator(raw_signings_list, raw_signings_per_page)
    page = request.GET.get('page')
    try:
        raw_signings = paginator.page(page)
    except PageNotAnInteger:
        raw_signings = paginator.page(1)
    except EmptyPage:
        raw_signings = paginator.page(paginator.num_pages)
    context = {'worker': worker, 'raw_signings': raw_signings}
    return render(request, 'workers/view.html', context)

def signings(request):
    signings_list = RawSignings.objects.order_by('-date_signed').all()
    signings_per_page = 20
    paginator = Paginator(signings_list, signings_per_page)
    page = request.GET.get('page')
    try:
        signings = paginator.page(page)
    except PageNotAnInteger:
        signings = paginator.page(1)
    except EmptyPage:
        signings = paginator.page(paginator.num_pages)
    return render(request, 'workers/signings.html', {'signings': signings})

def upload_signings(request):
    if request.method == 'POST' and request.FILES['excel_file']:
        excel_file = request.FILES['excel_file']
        df = pd.read_excel(excel_file)

        dates = []
        raw_signings = []
        workers = {}
        for index, row in df.iterrows():
            if index > 3:
                document = row.iloc[10]
                name = row.iloc[2]
                worker = workers[document] if workers.get(document) is not None else Worker.objects.filter(document=document).first()
                if not worker:
                    worker = Worker.objects.create(
                        document=document,
                        name=name,
                    )
                    workers[document] = worker
                if workers.get(document) == None:
                    workers[document] = worker

                date_signed = row.iloc[1].replace(tzinfo=timezone(timedelta(hours=-5)))
                normalized_date_signed = normalize_date(date_signed)
                signed_type="E" if row.iloc[4] == "entrada" else "S"

                if not dates:
                    start_date, end_date = get_start_end_week_dates(normalized_date_signed)
                    dates.append({"start_date": start_date, "end_date": end_date})
                else:
                    found_in_week = False
                    for date_range in dates:
                        if date_range["start_date"] <= normalized_date_signed <= date_range["end_date"]:
                            found_in_week = True
                            break
                    if not found_in_week:
                        start_date, end_date = get_start_end_week_dates(normalized_date_signed)
                        dates.append({"start_date": start_date, "end_date": end_date})

                entry = RawSignings.objects.filter(worker=worker, date_signed=date_signed).first()
                if not entry:
                    raw_signing = RawSignings(
                        folder_number=row.iloc[0],
                        date_signed=date_signed,
                        normalized_date_signed=normalized_date_signed,
                        worker=worker,
                        signed_type=signed_type,
                        door=row.iloc[5],
                        contract_number=row.iloc[6],
                    )
                    raw_signings.append(raw_signing)
        RawSignings.objects.bulk_create(raw_signings)

        settlements = []
        for date_range in dates:
            settlement = Settlement.objects.filter(start_date=date_range["start_date"], end_date=date_range["end_date"]).first()
            if not settlement:
                settlement = Settlement(
                    start_date=date_range["start_date"],
                    end_date=date_range["end_date"],
                )
                settlements.append(settlement)
        Settlement.objects.bulk_create(settlements)

        return redirect('/settlement/')

    return render(request, 'workers/upload_excel.html')
