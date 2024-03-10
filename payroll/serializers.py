from rest_framework.serializers import ModelSerializer
from .models import Payroll, PayrollDetail
from settlement.serializers import SettlementsSerializer

class PayrollSerializer(ModelSerializer):
    settlement = SettlementsSerializer(read_only=True, many=True)

    class Meta:
        model = Payroll
        fields = ('id', 'payroll_date', 'settlement')