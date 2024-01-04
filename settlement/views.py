from django.shortcuts import render, redirect
from django.http import HttpResponse
import pandas as pd
from .models import Settlement, SettlementDetails
from workers.models import Worker, RawSignings
from datetime import datetime

rooms = [
    {'id': 1, 'name': 'Lets learn Python!'},
    {'id': 2, 'name': 'Design with me'},
    {'id': 3, 'name': 'Frontend developers'},
]

# Create your views here.
def home(request):
    context = {'rooms': rooms}
    return render(request, 'settlement/home.html', context)

def room(request, pk):
    room = None
    for i in rooms:
        if i['id'] == int(pk):
            room = i
    context = {'room': room}
    return render(request, 'settlement/room.html', context)

def settlements(request):
    settlements = Settlement.objects.all()
    context = {'settlements': settlements}
    return render(request, 'settlement/index.html', context)

def view(request, pk):
    settlement = Settlement.objects.get(id=int(pk))
    context = {'settlement': settlement}
    return render(request, 'settlement/view.html', context)

def process_signing(request, pk):
    settlement = Settlement.objects.get(id=int(pk))
    if request.method == 'POST':
        raw_signings = RawSignings.objects.filter(normalized_date_signed__range=(settlement.start_date, settlement.end_date)).order_by('worker__id', 'normalized_date_signed').all()
        is_starting_new_day = True
        ordinary_hours = 0
        daytime_overtime = 0
        night_surcharge_hours = 0
        night_overtime = 0
        holiday_hours = 0
        night_holiday_hours = 0
        daytime_holiday_overtime = 0
        night_holiday_overtime = 0
        start_date_signed = None
        is_inside = True
        current_worker_id = 0
        settlement_details = None
        for index, raw_signing in enumerate(raw_signings):
            print(raw_signing.get_original_normalized_date_signed(), raw_signing.signed_type, raw_signing.worker.name)
            if is_starting_new_day and raw_signing.signed_type == "S":
                continue

            if raw_signing.worker.id != current_worker_id:
                current_worker_id = raw_signing.worker.id
                settlement_details, created = SettlementDetails.objects.get_or_create(
                    settlement=settlement,
                    worker=raw_signing.worker
                )
                # Set defaults of settlement_details to 0

            current_date = raw_signing.get_original_normalized_date_signed()
            is_inside = True if raw_signing.signed_type == "E" else False

            if is_starting_new_day and is_inside:
                start_date_signed = current_date
                is_starting_new_day = False

            if index+1 < len(raw_signings):
                next_worker_id = raw_signings[index+1].worker.id
                next_date = raw_signings[index+1].get_original_normalized_date_signed()
                next_signed_type = raw_signings[index+1].signed_type
                if next_worker_id != current_worker_id:
                    settlement_details.classify_hours(start_date_signed, current_date)
                    settlement_details.classify_week()
                    # settlement_details.save()
                    is_starting_new_day = True
                    continue
                if not is_inside:
                    if next_signed_type == "E":
                        hours = get_hours_difference(current_date, next_date)
                        if hours > 4:
                            # The worker is not inside and their next signing was in another day
                            # We can classify the hours now
                            settlement_details.classify_hours(start_date_signed, current_date)
                            is_starting_new_day = True
            elif index == len(raw_signings)-1:
                settlement_details.classify_hours(start_date_signed, current_date)
                settlement_details.classify_week()
                # settlement_details.save()

            if index > 50:
                break
    # return redirect('view', pk=settlement.id)
    return HttpResponse('Entries Processed')

def get_hours_difference(start_date: datetime, end_date: datetime) -> int:
    time_difference = end_date - start_date
    return time_difference.total_seconds() / 3600
