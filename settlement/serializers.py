from rest_framework.serializers import ModelSerializer, SerializerMethodField
from .models import Settlement, SettlementDetails
from workers.serializers import WorkersSerializer

class SettlementDetailsSerializer(ModelSerializer):
    worker_info = WorkersSerializer(source='worker', read_only=True)

    class Meta:
        model = SettlementDetails
        fields = ['id', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday', 'total_hours', 'ordinary_hours', 'daytime_overtime', 'night_surcharge_hours', 'night_overtime', 'holiday_hours', 'night_holiday_hours', 'daytime_holiday_overtime', 'night_holiday_overtime', 'working_shifts', 'worker', 'worker_info']
    
    def to_representation(self, instance):
        response = super().to_representation(instance)
        response['worker_info'] = WorkersSerializer(instance.worker).data
        return response

class SettlementSerializer(ModelSerializer):
    details = SettlementDetailsSerializer(many=True, read_only=True)

    class Meta:
        model = Settlement
        fields = ['id', 'start_date', 'end_date', 'processed', 'details']
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['details'] = sorted(representation['details'], key=lambda x: x['worker_info']['name'])
        return representation

class SettlementsSerializer(ModelSerializer):
    has_payroll = SerializerMethodField()
    
    class Meta:
        model = Settlement
        fields = '__all__'
    
    def get_has_payroll(self, obj):
        return obj.payroll.exists()
