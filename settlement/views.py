from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import pandas as pd
from .models import Settlement, SettlementDetails
from workers.models import Worker, RawSignings
from datetime import datetime, timedelta
from common.util import get_hours_difference
from io import BytesIO
from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import filters
from rest_framework import status
from .serializers import SettlementsSerializer, SettlementSerializer, SettlementDetailsSerializer

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

def create_ghost_datetime(start_datetime_signed: datetime, current_datetime: datetime):
    if start_datetime_signed.hour < 13:
        if current_datetime.hour >= 14:
            return datetime(start_datetime_signed.year, start_datetime_signed.month, start_datetime_signed.day, current_datetime.hour, current_datetime.minute, 0, 0, start_datetime_signed.tzinfo)
        return datetime(start_datetime_signed.year, start_datetime_signed.month, start_datetime_signed.day, 14, 0, 0, 0, start_datetime_signed.tzinfo)
    elif start_datetime_signed.hour < 21:
        return datetime(start_datetime_signed.year, start_datetime_signed.month, start_datetime_signed.day, 22, 0, 0, 0, start_datetime_signed.tzinfo)
    else:
        ghost_datetime = datetime(start_datetime_signed.year, start_datetime_signed.month, start_datetime_signed.day, 6, 0, 0, 0, start_datetime_signed.tzinfo)
        ghost_datetime = ghost_datetime + timedelta(days=1)
        return ghost_datetime

def process_settlement_signings(settlement: Settlement):
    start_filter = settlement.start_date - timedelta(hours=1)
    end_filter = settlement.end_date + timedelta(hours=1)
    raw_signings = RawSignings.objects.filter(
        normalized_date_signed__range=(start_filter, end_filter)
    ).order_by('worker__id', 'date_signed').all()
    is_starting_new_day = True
    start_datetime_signed = None
    start_datetime_raw_signed = None
    is_inside = True
    current_worker_id = 0
    settlement_details = None
    for index, raw_signing in enumerate(raw_signings):
        if is_starting_new_day and raw_signing.signed_type == "S":
            # Fixes raw_signings when worker is leaving on monday at 6am, so we skip this row
            continue

        if raw_signing.worker.id != current_worker_id:
            current_worker_id = raw_signing.worker.id
            settlement_details, created = SettlementDetails.objects.get_or_create(
                settlement=settlement,
                worker=raw_signing.worker
            )
            settlement_details.set_week_holidays()
            settlement_details.set_weekly_hours_needed()
            settlement_details.reset_hours()
            settlement_details.reset_weekly_counters()
        
        current_datetime = raw_signing.get_original_normalized_date_signed()
        is_inside = True if raw_signing.signed_type == "E" else False

        if settlement.end_date.day == current_datetime.day and is_inside:
            # Fixes bug of counting next monday entry
            continue

        if is_starting_new_day and is_inside:
            start_datetime_signed = current_datetime
            start_datetime_raw_signed = raw_signing.get_original_date_signed()
            is_starting_new_day = False

        # print(f'start_datetime_signed: {start_datetime_signed} | start_datetime_raw_signed: {start_datetime_raw_signed} | is_inside: {is_inside}')

        if index+1 < len(raw_signings):
            next_worker_id = raw_signings[index+1].worker.id
            next_datetime_signed = raw_signings[index+1].get_original_normalized_date_signed()
            next_signed_type = raw_signings[index+1].signed_type
            hours = get_hours_difference(current_datetime, next_datetime_signed)
            if next_worker_id != current_worker_id:
                # Condition that ends the week, so the settlement_detail is saved
                if is_inside:
                    # The worker is inside and their next signing was in another week
                    ghost_datetime = create_ghost_datetime(start_datetime_signed, current_datetime)
                    settlement_details.classify_hours(start_datetime_signed, ghost_datetime, start_datetime_raw_signed, ghost_datetime)
                else:
                    settlement_details.classify_hours(start_datetime_signed, current_datetime, start_datetime_raw_signed, raw_signing.get_original_date_signed())
                settlement_details.set_total_hours()
                settlement_details.save()
                is_starting_new_day = True
                continue
            if not is_inside:
                if hours > 7:
                    # Fixes a bug in excel file where the worker is not inside by mistake and actually finishes their turn later
                    if next_signed_type == 'S':
                        continue
                    # Condition that ends the day, so the working shift is saved
                    # The worker is not inside and their next signing was in another day
                    # We can classify the hours now
                    settlement_details.classify_hours(start_datetime_signed, current_datetime, start_datetime_raw_signed, raw_signing.get_original_date_signed())
                    settlement_details.set_total_hours()
                    settlement_details.save()
                    is_starting_new_day = True
            if is_inside and next_signed_type == 'E':
                if hours > 12:
                    # Condition that has no exit of the day, so we create a limit hour
                    # The worker is inside and their next signing was in another day
                    # We can classify the hours now
                    ghost_datetime = create_ghost_datetime(start_datetime_signed, current_datetime)
                    settlement_details.classify_hours(start_datetime_signed, ghost_datetime, start_datetime_raw_signed, ghost_datetime)
                    settlement_details.set_total_hours()
                    settlement_details.save()
                    is_starting_new_day = True


        elif index == len(raw_signings)-1:
            # Condition that shows the end of the signings
            settlement_details.classify_hours(start_datetime_signed, current_datetime, start_datetime_raw_signed, raw_signing.get_original_date_signed())
            settlement_details.set_total_hours()
            settlement_details.save()
    settlement.processed = True
    settlement.save()

def process_signing(request, pk):
    settlement = Settlement.objects.get(id=int(pk))
    if request.method == 'POST':
        process_settlement_signings(settlement)
    return redirect('settlement_view', pk=settlement.id)

def export_settlement_signings(settlement: Settlement):
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

        columns_rename_day_dict = {
            'monday': f'Lunes {days_dict["monday"]}',
            'tuesday': f'Martes {days_dict["tuesday"]}',
            'wednesday': f'Miércoles {days_dict["wednesday"]}',
            'thursday': f'Jueves {days_dict["thursday"]}',
            'friday': f'Viernes {days_dict["friday"]}',
            'saturday': f'Sábado {days_dict["saturday"]}',
            'sunday': f'Domingo {days_dict["sunday"]}',
        }

        df = df.rename(columns={
            'worker__name': 'Trabajador',
            'monday': columns_rename_day_dict['monday'],
            'tuesday': columns_rename_day_dict['tuesday'],
            'wednesday': columns_rename_day_dict['wednesday'],
            'thursday': columns_rename_day_dict['thursday'],
            'friday': columns_rename_day_dict['friday'],
            'saturday': columns_rename_day_dict['saturday'],
            'sunday': columns_rename_day_dict['sunday'],
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

            # Get the Workbook object and the worksheet
            workbook = writer.book
            worksheet = writer.sheets['Liquidación']

            # Format for green cells
            green_format = workbook.add_format({'bg_color': '#C6EFCE'})
            # Format for yellow cells
            yellow_format = workbook.add_format({'bg_color': '#FFFF00'})

            for row_idx, settlement_detail in enumerate(settlement_details):
                working_shifts = settlement_detail.working_shifts
                for day, shift in working_shifts.items():
                    column_name = columns_rename_day_dict[day]
                    col_idx = df.columns.get_loc(column_name)
                    cell_value = df.at[row_idx, column_name]
                    if shift['shift'] == 2:  # Turno de tarde
                        worksheet.write(row_idx+1, col_idx, cell_value, green_format)
                    elif shift['shift'] == 3:  # Turno de noche
                        worksheet.write(row_idx+1, col_idx, cell_value, yellow_format)

            # Adjust the width of the columns
            for column in df.columns:
                column_length = max(df[column].astype(str).map(len).max(), len(column))
                col_idx = df.columns.get_loc(column)
                worksheet.set_column(col_idx, col_idx, column_length + 2)

        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        response['Access-Control-Expose-Headers'] = 'Content-Disposition'
        response.write(excel_buffer.getvalue())
        return response
    except Exception as e:
        raise Exception(f'There was a problem exporting the excel file: {e}')

def export_settlement(request, pk):
    settlement = Settlement.objects.get(id=int(pk))
    if request.method == 'POST':
        try:
            response = export_settlement_signings(settlement)
            return response
        except Exception as e:
            print(f'{e}')
    return redirect('settlement_view', pk=settlement.id)

class SettlementView(viewsets.ModelViewSet):
    serializer_class = SettlementsSerializer
    queryset = Settlement.objects.all()
    filter_backends = [filters.OrderingFilter]
    ordering_fields = '__all__'
    ordering = ['-start_date']

    def get_serializer_class(self):
        if self.action == "retrieve":
            return SettlementSerializer
        return SettlementsSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        if start_date and end_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            queryset = queryset.filter(start_date__range=(start_date, end_date))
        return queryset

class SettlementDetailView(viewsets.ModelViewSet):
    serializer_class = SettlementDetailsSerializer
    queryset = SettlementDetails.objects.all()

@api_view(['POST'])
def process_settlement(request):
    pk = request.data['id']
    settlement = Settlement.objects.get(id=int(pk))
    process_settlement_signings(settlement)
    serializer = SettlementSerializer(settlement)
    return Response(serializer.data)

@api_view(['POST'])
def export_settlement(request):
    pk = request.data['id']
    settlement = Settlement.objects.get(id=int(pk))
    try:
        response = export_settlement_signings(settlement)
        return response
    except Exception as e:
        pass

    return Response({'status': status.HTTP_200_OK})