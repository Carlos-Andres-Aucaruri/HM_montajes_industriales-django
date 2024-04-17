from rest_framework.decorators import api_view
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status
from rest_framework import filters
import pandas as pd
from io import BytesIO
from django.http import HttpResponse
from settlement.models import Settlement, SettlementDetails
from .models import Payroll, PayrollDetail
from .serializers import PayrollSerializer

@api_view(['POST'])
def create_payroll(request):
    try:
        data = request.data['settlements']
        date = request.data['payroll_date']
        payroll, created = Payroll.objects.get_or_create(payroll_date=date)
        settlements_ids = [int(item['settlement_id']) for item in data]
        settlements = Settlement.objects.filter(id__in=settlements_ids)
        worker_payroll_mapping = {}
        for settlement in settlements:
            settlement_details = settlement.details.all()
            for settlement_detail in settlement_details:
                worker_id = settlement_detail.worker_id
                if worker_id not in worker_payroll_mapping:
                    payroll_detail = PayrollDetail.objects.create(
                        payroll=payroll,
                        worker_id=worker_id,
                        total_hours=settlement_detail.total_hours,
                        ordinary_hours=settlement_detail.ordinary_hours,
                        daytime_overtime=settlement_detail.daytime_overtime,
                        night_surcharge_hours=settlement_detail.night_surcharge_hours,
                        night_overtime=settlement_detail.night_overtime,
                        holiday_hours=settlement_detail.holiday_hours,
                        night_holiday_hours=settlement_detail.night_holiday_hours,
                        daytime_holiday_overtime=settlement_detail.daytime_holiday_overtime,
                        night_holiday_overtime=settlement_detail.night_holiday_overtime
                    )
                    worker_payroll_mapping[worker_id] = payroll_detail
                else:
                    # Reuse existing Payroll instance
                    payroll_detail = worker_payroll_mapping[worker_id]
                    payroll_detail.total_hours += settlement_detail.total_hours
                    payroll_detail.ordinary_hours += settlement_detail.ordinary_hours
                    payroll_detail.daytime_overtime += settlement_detail.daytime_overtime
                    payroll_detail.night_surcharge_hours += settlement_detail.night_surcharge_hours
                    payroll_detail.night_overtime += settlement_detail.night_overtime
                    payroll_detail.holiday_hours += settlement_detail.holiday_hours
                    payroll_detail.night_holiday_hours += settlement_detail.night_holiday_hours
                    payroll_detail.daytime_holiday_overtime += settlement_detail.daytime_holiday_overtime
                    payroll_detail.night_holiday_overtime += settlement_detail.night_holiday_overtime
                    
                    payroll_detail.save()
                payroll_detail.settlement_detail.add(settlement_detail)
            payroll.settlement.add(settlement)

        return Response({'message': 'Payroll created successfully.', 'status': status.HTTP_200_OK})
    except Exception as e:
        return Response({'error': str(e)}, status=400)

class PayrollView(viewsets.ModelViewSet):
    serializer_class = PayrollSerializer
    queryset = Payroll.objects.all()
    filter_backends = [filters.OrderingFilter]
    ordering_fields = '__all__'
    ordering = ['-payroll_date']

def export_payroll_detail(payroll: Payroll):
    try:
        settlements = payroll.settlement.order_by('start_date').all()
        payroll_details = payroll.details.order_by('worker__name').all()

        columns = ['worker__name']
        rename_columns = {
            'worker__name': 'Trabajador',
            'total_hours': 'Total Horas',
            'ordinary_hours': 'H.O',
            'daytime_overtime': 'H.E.D',
            'night_surcharge_hours': 'H.R.N',
            'night_overtime': 'H.E.N',
            'holiday_hours': 'H.F',
            'night_holiday_hours': 'H.F.N',
            'daytime_holiday_overtime': 'H.E.F.D',
            'night_holiday_overtime': 'H.E.F.N',
        }

        days_shifts_dict = {}
        days_translate = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
        for settlement in settlements:
            days_dict = settlement.get_days_dict()
            for idx, day in enumerate(['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']):
                column_name = f'settlement_detail_{settlement.id}__{day}'
                columns.append(column_name)
                rename_column_name = f'{days_translate[idx]} {days_dict[day]}'
                rename_columns[column_name] = rename_column_name
                days_shifts_dict[column_name] = []

        columns.append('total_hours')
        columns.append('ordinary_hours')
        columns.append('daytime_overtime')
        columns.append('night_surcharge_hours')
        columns.append('night_overtime')
        columns.append('holiday_hours')
        columns.append('night_holiday_hours')
        columns.append('daytime_holiday_overtime')
        columns.append('night_holiday_overtime')

        data = {column: [] for column in columns}
        for payroll_detail in payroll_details:
            for column in columns:
                value_found = False
                if 'settlement_detail' in column:
                    related_model, day = column.split('__')
                    settlement_details = payroll_detail.settlement_detail.order_by('settlement__start_date').all()
                    for settlement_detail in settlement_details:
                        if str(settlement_detail.settlement.id) in related_model:
                            value_found = True
                            value = getattr(settlement_detail, day, 0)
                            shift = settlement_detail.working_shifts[day]['shift']
                            days_shifts_dict[column].append(shift)
                elif 'worker' in column:
                    value_found = True
                    value = payroll_detail.worker.name
                else:
                    value_found = True
                    value = getattr(payroll_detail, column, 0)
                if not value_found:
                    value = 0
                    days_shifts_dict[column].append(0)
                data[column].append(value)

        df = pd.DataFrame.from_dict(data=data)
        df = df.rename(columns=rename_columns)

        # Create an in-memory buffer for the Excel file
        excel_buffer = BytesIO()
        filename = f'NOMINA {payroll.payroll_date}.xlsx'

        with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Nómina')

            workbook = writer.book
            worksheet = writer.sheets['Nómina']

            green_format = workbook.add_format({'bg_color': '#C6EFCE'})
            yellow_format = workbook.add_format({'bg_color': '#FFFF00'})

            for column_day, shifts in days_shifts_dict.items():
                for row_idx, shift in enumerate(shifts):
                    column_name = rename_columns[column_day]
                    col_idx = df.columns.get_loc(column_name)
                    cell_value = df.at[row_idx, column_name]
                    if shift == 2:
                        worksheet.write(row_idx+1, col_idx, cell_value, green_format)
                    elif shift == 3:
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

@api_view(['POST'])
def export_payroll(request):
    pk = request.data['id']
    payroll = Payroll.objects.get(id=int(pk))
    try:
        response = export_payroll_detail(payroll)
        return response
    except Exception as e:
        pass

    return Response({'status': status.HTTP_200_OK})
