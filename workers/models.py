from django.db import models
from pytz import timezone

class Worker(models.Model):
    document = models.IntegerField()
    name = models.CharField(max_length=200)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.name

class RawSignings(models.Model):
    folder_number = models.PositiveBigIntegerField()
    date_signed = models.DateTimeField()
    normalized_date_signed = models.DateTimeField(null=True)
    worker = models.ForeignKey(Worker, on_delete=models.CASCADE)
    SIGNED_TYPES = {
        "E": "Entrada",
        "S": "Salida",
    }
    signed_type = models.CharField(max_length=1, choices=SIGNED_TYPES)
    door = models.CharField(max_length=30)
    contract_number = models.CharField(max_length=30)

    class Meta:
        verbose_name_plural = 'Raw signings'

    def get_original_normalized_date_signed(self):
        return self.normalized_date_signed.astimezone(timezone('America/Bogota'))
