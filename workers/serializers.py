from rest_framework.serializers import ModelSerializer
from .models import Worker, RawSignings

class RawSigningsSerializer(ModelSerializer):
    class Meta:
        model = RawSignings
        fields = '__all__'

class WorkerSerializer(ModelSerializer):
    signings = RawSigningsSerializer(many=True, read_only=True)

    class Meta:
        model = Worker
        fields = ['id', 'document', 'name', 'signings']

class WorkersSerializer(ModelSerializer):
    class Meta:
        model = Worker
        fields = '__all__'

class RawSigningsSerializerFull(ModelSerializer):
    worker_info = WorkersSerializer(source='worker', read_only=True)

    class Meta:
        model = RawSignings
        fields = ['id', 'folder_number', 'date_signed', 'normalized_date_signed', 'signed_type', 'door', 'contract_number', 'worker', 'worker_info']