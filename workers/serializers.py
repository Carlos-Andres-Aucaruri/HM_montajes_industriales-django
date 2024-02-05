from rest_framework.serializers import ModelSerializer
from .models import Worker, RawSignings

class RawSigningsSerializer(ModelSerializer):
    class Meta:
        model = RawSignings
        fields = '__all__'

class WorkerSerializer(ModelSerializer):
    class Meta:
        model = Worker
        fields = '__all__'