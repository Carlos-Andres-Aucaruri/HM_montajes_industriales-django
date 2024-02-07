from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import pandas as pd
from .models import Settlement, SettlementDetails
from workers.models import Worker, RawSignings
from datetime import datetime
from common.util import get_hours_difference
from io import BytesIO
from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from .serializers import SettlementSerializer, SettlementDetailsSerializer

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

            if settlement.end_date.day == current_date.day and is_inside:
                # Fixes bug of counting next monday entry
                continue

            if is_starting_new_day and is_inside:
                start_date_signed = current_date
                is_starting_new_day = False

            # print(raw_signing.get_original_normalized_date_signed(), raw_signing.signed_type, raw_signing.worker.name)
            if index+1 < len(raw_signings):
                next_worker_id = raw_signings[index+1].worker.id
                next_date = raw_signings[index+1].get_original_normalized_date_signed()
                next_signed_type = raw_signings[index+1].signed_type
                if next_worker_id != current_worker_id:
                    settlement_details.classify_hours(start_date_signed, current_date)
                    settlement_details.set_total_hours()
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
                            settlement_details.set_total_hours()
                            settlement_details.save()
                            is_starting_new_day = True
            elif index == len(raw_signings)-1:
                settlement_details.classify_hours(start_date_signed, current_date)
                settlement_details.set_total_hours()
                settlement_details.save()
        settlement.processed = True
        settlement.save()

    return redirect('settlement_view', pk=settlement.id)

def export_settlement(request, pk):
    settlement = Settlement.objects.get(id=int(pk))
    if request.method == 'POST':
        try:
            days_dict = settlement.get_days_dict()
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
                'total_hours',
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
                'monday': f'Lunes {days_dict["monday"]}',
                'tuesday': f'Martes {days_dict["tuesday"]}',
                'wednesday': f'Miércoles {days_dict["wednesday"]}',
                'thursday': f'Jueves {days_dict["thursday"]}',
                'friday': f'Viernes {days_dict["friday"]}',
                'saturday': f'Sábado {days_dict["saturday"]}',
                'sunday': f'Domingo {days_dict["sunday"]}',
                'total_hours': 'Total Horas',
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

            with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Liquidación')

                # Adjust the width of the columns
                for column in df.columns:
                    column_length = max(df[column].astype(str).map(len).max(), len(column))
                    col_idx = df.columns.get_loc(column)
                    writer.sheets['Liquidación'].set_column(col_idx, col_idx, column_length + 2)
                
            response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            response.write(excel_buffer.getvalue())
            return response
        except Exception as e:
            print(f'There was a problem exporting the excel file: {e}')
    return redirect('settlement_view', pk=settlement.id)

class SettlementView(viewsets.ModelViewSet):
    serializer_class = SettlementSerializer
    queryset = Settlement.objects.all()
    permission_classes = [AllowAny]

class SettlementDetailView(viewsets.ModelViewSet):
    serializer_class = SettlementDetailsSerializer
    queryset = SettlementDetails.objects.all()
    permission_classes = [AllowAny]
