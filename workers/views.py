from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import Worker, RawSignings
from settlement.models import Settlement
from datetime import datetime, timezone, timedelta
import pandas as pd
from common.util import normalize_date, get_start_end_week_dates
from rest_framework import viewsets
from rest_framework import status
from rest_framework import filters
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from .serializers import WorkerSerializer, WorkersSerializer, RawSigningsSerializer, RawSigningsSerializerFull

def index(request):
    workers_list = Worker.objects.all()
    workers_per_page = 20
    paginator = Paginator(workers_list, workers_per_page)
    page = request.GET.get('page')
    try:
        workers = paginator.page(page)
    except PageNotAnInteger:
        workers = paginator.page(1)
    except EmptyPage:
        workers = paginator.page(paginator.num_pages)
    return render(request, 'workers/index.html', {'workers': workers})

def view(request, pk):
    worker = Worker.objects.get(id=int(pk))
    raw_signings_list = RawSignings.objects.filter(worker=worker).order_by('-date_signed').all()
    raw_signings_per_page = 20
    paginator = Paginator(raw_signings_list, raw_signings_per_page)
    page = request.GET.get('page')
    try:
        raw_signings = paginator.page(page)
    except PageNotAnInteger:
        raw_signings = paginator.page(1)
    except EmptyPage:
        raw_signings = paginator.page(paginator.num_pages)
    context = {'worker': worker, 'raw_signings': raw_signings}
    return render(request, 'workers/view.html', context)

def signings(request):
    signings_list = RawSignings.objects.order_by('-date_signed').all()
    signings_per_page = 20
    paginator = Paginator(signings_list, signings_per_page)
    page = request.GET.get('page')
    try:
        signings = paginator.page(page)
    except PageNotAnInteger:
        signings = paginator.page(1)
    except EmptyPage:
        signings = paginator.page(paginator.num_pages)
    return render(request, 'workers/signings.html', {'signings': signings})

def process_excel(excel_file):
    df = pd.read_excel(excel_file)
    dates = []
    workers = {}
    for index, row in df.iterrows():
        if index > 3:
            document = row.iloc[10]
            name = row.iloc[2]
            worker = workers[document] if workers.get(document) is not None else Worker.objects.filter(document=document).first()
            if not worker:
                worker = Worker.objects.create(
                    document=document,
                    name=name,
                )
                workers[document] = worker
            if workers.get(document) == None:
                workers[document] = worker

            date_signed = row.iloc[1].replace(tzinfo=timezone(timedelta(hours=-5)))
            signed_type="E" if row.iloc[4] == "entrada" else "S"
            normalized_date_signed = normalize_date(date_signed, signed_type)

            if not dates:
                start_date, end_date = get_start_end_week_dates(normalized_date_signed)
                dates.append({"start_date": start_date, "end_date": end_date})
            else:
                found_in_week = False
                for date_range in dates:
                    if date_range["start_date"] <= normalized_date_signed <= date_range["end_date"]:
                        found_in_week = True
                        break
                if not found_in_week:
                    start_date, end_date = get_start_end_week_dates(normalized_date_signed)
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
        settlement = Settlement.objects.filter(start_date=date_range["start_date"], end_date=date_range["end_date"]).first()
        if not settlement:
            settlement = Settlement(
                start_date=date_range["start_date"],
                end_date=date_range["end_date"],
            )
            settlements.append(settlement)
    Settlement.objects.bulk_create(settlements)

def upload_signings(request):
    if request.method == 'POST' and request.FILES['excel_file']:
        excel_file = request.FILES['excel_file']
        process_excel(excel_file)
        return redirect('/settlement/')

    return render(request, 'workers/upload_excel.html')

class WorkerView(viewsets.ModelViewSet):
    serializer_class = WorkersSerializer
    queryset = Worker.objects.all()
    filter_backends = [filters.OrderingFilter]
    ordering_fields = '__all__'
    ordering = ['name']

    def get_serializer_class(self):
        if self.action == "retrieve":
            return WorkerSerializer
        return WorkersSerializer

class SigningView(viewsets.ModelViewSet):
    serializer_class = RawSigningsSerializer
    queryset = RawSignings.objects.all()
    filter_backends = [filters.OrderingFilter]
    ordering_fields = '__all__'
    ordering = ['worker__name', '-date_signed']
    pagination_class = PageNumberPagination
    pagination_class.page_size = 100

    def get_serializer_class(self):
        if self.action == "list":
            return RawSigningsSerializerFull
        return RawSigningsSerializer

@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def import_signings(request, format=None):
    excel_file = request.FILES['excel_file']
    process_excel(excel_file)
    signings = RawSignings.objects.order_by('worker__name', '-date_signed').all()
    paginator = PageNumberPagination()
    paginator.page_size = 100
    result_page = paginator.paginate_queryset(signings, request)
    serializer = RawSigningsSerializerFull(result_page, many=True)
    return paginator.get_paginated_response(serializer.data)
