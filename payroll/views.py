from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from settlement.models import Settlement, SettlementDetails
from .models import Payroll, SettlementPayroll

@api_view(['POST'])
@permission_classes([AllowAny])
def create_payroll(request):
    try:
        data = request.data['settlements']
        settlements_ids = [int(item['settlement_id']) for item in data]
        settlements = Settlement.objects.filter(id__in=settlements_ids)
        worker_payroll_mapping = {}
        for settlement in settlements:
            settlement_details = settlement.details.all()
            for detail in settlement_details:
                worker_id = detail.worker_id
                if worker_id not in worker_payroll_mapping:
                    # Create new Payroll instance if not already created
                    payroll = Payroll.objects.create(worker_id=worker_id)
                    worker_payroll_mapping[worker_id] = payroll
                else:
                    # Reuse existing Payroll instance
                    payroll = worker_payroll_mapping[worker_id]
                SettlementPayroll.objects.create(settlement=settlement, payroll=payroll)

        return Response({'message': 'Payrolls created successfully.', 'status': status.HTTP_200_OK})
    except Exception as e:
        return Response({'error': str(e)}, status=400)