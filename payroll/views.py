from rest_framework.decorators import api_view, permission_classes
from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework import filters
from settlement.models import Settlement, SettlementDetails
from .models import Payroll, PayrollDetail
from .serializers import PayrollSerializer

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
    permission_classes = [AllowAny]
    serializer_class = PayrollSerializer
    queryset = Payroll.objects.all()
    filter_backends = [filters.OrderingFilter]
    ordering_fields = '__all__'
    ordering = ['-payroll_date']