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
        is_starting_new_week = True
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
        for index, raw_signing in enumerate(raw_signings):
            print(raw_signing.get_original_normalized_date_signed(), raw_signing.signed_type, raw_signing.worker.name)
            if is_starting_new_day and raw_signing.signed_type == "S":
                continue

            if raw_signing.worker.id != current_worker_id:
                current_worker_id = raw_signing.worker.id

            current_date = raw_signing.get_original_normalized_date_signed()
            is_inside = True if raw_signing.signed_type == "E" else False

            if is_starting_new_week and current_date.weekday() == 0:
                is_starting_new_week = False

            if is_starting_new_day and is_inside:
                start_date_signed = current_date
                is_starting_new_day = False

            if index+1 < len(raw_signings):
                next_date = raw_signings[index+1].get_original_normalized_date_signed()
                if not is_inside:
                    next_signed_type = raw_signings[index+1].signed_type
                    if next_signed_type == "E":
                        hours = get_hours_difference(current_date, next_date)
                        if hours > 4:
                            # The worker is not inside and their next signing was in another day
                            # We can classify the hours now
                            end_date_signed = current_date
                            classify_hours(start_date_signed, end_date_signed)
                            is_starting_new_day = True
                if not is_starting_new_week and next_date.weekday() == 0:
                    is_starting_new_week = True
                    # Save the hours classified for the week
                    pass
            elif index == len(raw_signings)-1:
                end_date_signed = current_date
                classify_hours(start_date_signed, end_date_signed)
                # Save the hours classified for the week
                pass

            if index > 23:
                break
    # return redirect('view', pk=settlement.id)
    return HttpResponse('Entries Processed')

def get_hours_difference(start_date: datetime, end_date: datetime) -> int:
    time_difference = end_date - start_date
    return time_difference.total_seconds() / 3600

def classify_hours(start_date: datetime, end_date: datetime):
    print(f'TURN STARTED AT {start_date} AND FINISHED AT {end_date}')
    pass