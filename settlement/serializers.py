from rest_framework.serializers import ModelSerializer
from .models import Settlement, SettlementDetails

class SettlementSerializer(ModelSerializer):
    class Meta:
        model = Settlement
        fields = '__all__'

class SettlementDetailsSerializer(ModelSerializer):
    class Meta:
        model = SettlementDetails
        fields = '__all__'