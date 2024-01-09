from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import pandas as pd
from .models import Settlement, SettlementDetails
from workers.models import Worker, RawSignings
from datetime import datetime
from common.util import get_hours_difference
from io import BytesIO

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

def index(request):
    settlements_list = Settlement.objects.order_by('-start_date').all()
    settlements_per_page = 20
    paginator = Paginator(settlements_list, settlements_per_page)
    page = request.GET.get('page')
    try:
        settlements = paginator.page(page)
    except PageNotAnInteger:
        settlements = paginator.page(1)
    except EmptyPage:
        settlements = paginator.page(paginator.num_pages)
    return render(request, 'settlement/index.html', {'settlements': settlements})

def view(request, pk):
    settlement = Settlement.objects.get(id=int(pk))
    settlement_details_list = SettlementDetails.objects.filter(settlement=settlement).order_by('worker__id').all()
    settlement_details_per_page = 20
    paginator = Paginator(settlement_details_list, settlement_details_per_page)
    page = request.GET.get('page')
    try:
        settlement_details = paginator.page(page)
    except PageNotAnInteger:
        settlement_details = paginator.page(1)
    except EmptyPage:
        settlement_details = paginator.page(paginator.num_pages)
    context = {'settlement': settlement, 'settlement_details': settlement_details}
    return render(request, 'settlement/view.html', context)

def process_signing(request, pk):
    settlement = Settlement.objects.get(id=int(pk))
    if request.method == 'POST':
        raw_signings = RawSignings.objects.filter(normalized_date_signed__range=(settlement.start_date, settlement.end_date)).order_by('worker__id', 'normalized_date_signed').all()
        is_starting_new_day = True
        start_date_signed = None
        is_inside = True
        current_worker_id = 0
        settlement_details = None
        for index, raw_signing in enumerate(raw_signings):
            # print(raw_signing.get_original_normalized_date_signed(), raw_signing.signed_type, raw_signing.worker.name)
            if is_starting_new_day and raw_signing.signed_type == "S":
                continue

            if raw_signing.worker.id != current_worker_id:
                current_worker_id = raw_signing.worker.id
                settlement_details, created = SettlementDetails.objects.get_or_create(
                    settlement=settlement,
                    worker=raw_signing.worker
                )
                if not created:
                    settlement_details.reset_hours()

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
                    settlement_details.save()
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
                settlement_details.save()
        settlement.processed = True
        settlement.save()

    return redirect('settlement_view', pk=settlement.id)

def export_settlement(request, pk):
    settlement = Settlement.objects.get(id=int(pk))
    if request.method == 'POST':
        try:
            settlement_details = SettlementDetails.objects.filter(settlement=settlement).order_by('worker__id').all()
            df = pd.DataFrame.from_records(settlement_details.values(
                'worker__name',
                'monday',
                'tuesday',
                'wednesday',
                'thursday',
                'friday',
                'saturday',
                'sunday',
                'ordinary_hours',
                'daytime_overtime',
                'night_surcharge_hours',
                'night_overtime',
                'holiday_hours',
                'night_holiday_hours',
                'daytime_holiday_overtime',
                'night_holiday_overtime'))
            df = df.rename(columns={
                'worker__name': 'Trabajador',
                'monday': 'Lunes',
                'tuesday': 'Martes',
                'wednesday': 'Miércoles',
                'thursday': 'Jueves',
                'friday': 'Viernes',
                'saturday': 'Sábado',
                'sunday': 'Domingo',
                'ordinary_hours': 'H.O',
                'daytime_overtime': 'H.E.D',
                'night_surcharge_hours': 'H.R.N',
                'night_overtime': 'H.E.N',
                'holiday_hours': 'H.F',
                'night_holiday_hours': 'H.F.N',
                'daytime_holiday_overtime': 'H.E.F.D',
                'night_holiday_overtime': 'H.E.F.N',
            })

            # Create an in-memory buffer for the Excel file
            excel_buffer = BytesIO()
            start_day = settlement.start_date.day
            end_day = settlement.end_date.day
            filename = f'LIQ. SEM {start_day}-AL-{end_day}-{settlement.start_date.month}.xlsx'
            df.to_excel(excel_buffer)
            response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            response.write(excel_buffer.getvalue())
            return response
        except Exception as e:
            print(f'There was a problem exporting the excel file: {e}')
    return redirect('settlement_view', pk=settlement.id)