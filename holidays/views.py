from rest_framework import viewsets
from .serializers import HolidaySerializer
from .models import Holiday

class HolidayView(viewsets.ModelViewSet):
    serializer_class = HolidaySerializer
    queryset = Holiday.objects.all()