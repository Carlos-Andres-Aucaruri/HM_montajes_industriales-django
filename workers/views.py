from django.shortcuts import render
from django.http import HttpResponse
from .models import Worker, RawSignings
from datetime import datetime, timezone, timedelta
import pandas as pd

# Create your views here.
def home(request):
    return render(request, 'workers/home.html')

def upload_signings(request):
    if request.method == 'POST' and request.FILES['excel_file']:
        excel_file = request.FILES['excel_file']
        df = pd.read_excel(excel_file)

        for index, row in df.iterrows():
            if index > 3:
                document = row.iloc[10]
                name = row.iloc[2]
                worker = Worker.objects.filter(document=document).first()
                if not worker:
                    worker = Worker.objects.create(
                        document=document,
                        name=name,
                    )

                date_signed = row.iloc[1].replace(tzinfo=timezone(timedelta(hours=-5)))
                entry = RawSignings.objects.filter(worker=worker, date_signed=date_signed).first()
                if not entry:
                    RawSignings.objects.create(
                        folder_number=row.iloc[0],
                        date_signed=date_signed,
                        worker=worker,
                        signed_type="E" if row.iloc[4] == "entrada" else "S",
                        door=row.iloc[5],
                        contract_number=row.iloc[6],
                    )

        return HttpResponse("File uploaded and processed successfully")

    return render(request, 'workers/upload_excel.html')