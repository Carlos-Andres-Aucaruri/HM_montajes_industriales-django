from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from settlement.models import Settlement, SettlementDetails
from .models import Payroll, PayrollDetail, SettlementPayroll

@api_view(['POST'])
@permission_classes([AllowAny])
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
            for detail in settlement_details:
                worker_id = detail.worker_id
                if worker_id not in worker_payroll_mapping:
                    payroll_detail = PayrollDetail.objects.create(
                        payroll=payroll,
                        worker_id=worker_id,
                        total_hours=detail.total_hours,
                        ordinary_hours=detail.ordinary_hours,
                        daytime_overtime=detail.daytime_overtime,
                        night_surcharge_hours=detail.night_surcharge_hours,
                        night_overtime=detail.night_overtime,
                        holiday_hours=detail.holiday_hours,
                        night_holiday_hours=detail.night_holiday_hours,
                        daytime_holiday_overtime=detail.daytime_holiday_overtime,
                        night_holiday_overtime=detail.night_holiday_overtime
                    )
                    worker_payroll_mapping[worker_id] = payroll_detail
                else:
                    # Reuse existing Payroll instance
                    payroll_detail = worker_payroll_mapping[worker_id]
                    payroll_detail.total_hours += detail.total_hours
                    payroll_detail.ordinary_hours += detail.ordinary_hours
                    payroll_detail.daytime_overtime += detail.daytime_overtime
                    payroll_detail.night_surcharge_hours += detail.night_surcharge_hours
                    payroll_detail.night_overtime += detail.night_overtime
                    payroll_detail.holiday_hours += detail.holiday_hours
                    payroll_detail.night_holiday_hours += detail.night_holiday_hours
                    payroll_detail.daytime_holiday_overtime += detail.daytime_holiday_overtime
                    payroll_detail.night_holiday_overtime += detail.night_holiday_overtime
                    payroll_detail.save()
                SettlementPayroll.objects.create(settlement=settlement, payroll_detail=payroll_detail)

        return Response({'message': 'Payroll created successfully.', 'status': status.HTTP_200_OK})
    except Exception as e:
        return Response({'error': str(e)}, status=400)