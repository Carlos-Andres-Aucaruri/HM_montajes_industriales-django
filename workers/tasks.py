from datetime import datetime, timedelta, timezone

import pandas as pd
from celery import shared_task

from common.util import get_start_end_week_dates, normalize_date
from settlement.models import Settlement

from .models import RawSignings, Worker


@shared_task
def process_excel(file_path):
    df = pd.read_excel(file_path)
    dates = []
    workers = {}
    for index, row in df.iterrows():
        if index > 3:
            document = row.iloc[10]
            name = row.iloc[2]
            worker = (
                workers[document]
                if workers.get(document) is not None
                else Worker.objects.filter(document=document).first()
            )
            if not worker:
                worker = Worker.objects.create(
                    document=document,
                    name=name,
                )
                workers[document] = worker
            if workers.get(document) == None:
                workers[document] = worker

            date_signed = row.iloc[1].replace(tzinfo=timezone(timedelta(hours=-5)))
            signed_type = "E" if row.iloc[4] == "entrada" else "S"
            normalized_date_signed = normalize_date(date_signed, signed_type)

            if not dates:
                start_date, end_date = get_start_end_week_dates(normalized_date_signed)
                dates.append({"start_date": start_date, "end_date": end_date})
            else:
                found_in_week = False
                for date_range in dates:
                    if (
                        date_range["start_date"]
                        <= normalized_date_signed
                        <= date_range["end_date"]
                    ):
                        found_in_week = True
                        break
                if not found_in_week:
                    start_date, end_date = get_start_end_week_dates(
                        normalized_date_signed
                    )
                    dates.append({"start_date": start_date, "end_date": end_date})

            raw_signing, created = RawSignings.objects.get_or_create(
                folder_number=row.iloc[0],
                date_signed=date_signed,
                worker=worker,
                signed_type=signed_type,
                door=row.iloc[5],
                contract_number=row.iloc[6],
            )
            raw_signing.normalized_date_signed = normalized_date_signed
            raw_signing.save()

    settlements = []
    for date_range in dates:
        settlement = Settlement.objects.filter(
            start_date=date_range["start_date"], end_date=date_range["end_date"]
        ).first()
        if not settlement:
            settlement = Settlement(
                start_date=date_range["start_date"],
                end_date=date_range["end_date"],
            )
            settlements.append(settlement)
    Settlement.objects.bulk_create(settlements)
