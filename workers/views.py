from datetime import datetime

from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.shortcuts import redirect, render
from rest_framework import filters, viewsets
from rest_framework.decorators import action, api_view, parser_classes
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response

from .models import RawSignings, Worker
from .serializers import (
    RawSigningsSerializer,
    RawSigningsSerializerFull,
    WorkerSerializer,
    WorkersSerializer,
)
from .tasks import process_excel
from .utils import save_excel_file


def index(request):
    workers_list = Worker.objects.all()
    workers_per_page = 20
    paginator = Paginator(workers_list, workers_per_page)
    page = request.GET.get("page")
    try:
        workers = paginator.page(page)
    except PageNotAnInteger:
        workers = paginator.page(1)
    except EmptyPage:
        workers = paginator.page(paginator.num_pages)
    return render(request, "workers/index.html", {"workers": workers})


def view(request, pk):
    worker = Worker.objects.get(id=int(pk))
    raw_signings_list = (
        RawSignings.objects.filter(worker=worker).order_by("-date_signed").all()
    )
    raw_signings_per_page = 20
    paginator = Paginator(raw_signings_list, raw_signings_per_page)
    page = request.GET.get("page")
    try:
        raw_signings = paginator.page(page)
    except PageNotAnInteger:
        raw_signings = paginator.page(1)
    except EmptyPage:
        raw_signings = paginator.page(paginator.num_pages)
    context = {"worker": worker, "raw_signings": raw_signings}
    return render(request, "workers/view.html", context)


def signings(request):
    signings_list = RawSignings.objects.order_by("-date_signed").all()
    signings_per_page = 20
    paginator = Paginator(signings_list, signings_per_page)
    page = request.GET.get("page")
    try:
        signings = paginator.page(page)
    except PageNotAnInteger:
        signings = paginator.page(1)
    except EmptyPage:
        signings = paginator.page(paginator.num_pages)
    return render(request, "workers/signings.html", {"signings": signings})


def upload_signings(request):
    if request.method == "POST" and request.FILES["excel_file"]:
        excel_file = request.FILES["excel_file"]
        file_path = save_excel_file(excel_file)
        process_excel.apply_async(file_path)
        return redirect("/settlement/")

    return render(request, "workers/upload_excel.html")


class WorkerView(viewsets.ModelViewSet):
    serializer_class = WorkersSerializer
    queryset = Worker.objects.all()
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    ordering_fields = "__all__"
    ordering = ["name"]
    search_fields = ["name", "document"]
    pagination_class = PageNumberPagination
    pagination_class.page_size = 10
    pagination_class.max_page_size = 100
    pagination_class.page_size_query_param = "page_size"

    def get_serializer_class(self):
        if self.action == "retrieve":
            return WorkerSerializer
        return WorkersSerializer


class SigningView(viewsets.ModelViewSet):
    serializer_class = RawSigningsSerializer
    queryset = RawSignings.objects.all()
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    ordering_fields = "__all__"
    ordering = ["worker__name", "-date_signed"]
    search_fields = ["worker__name", "worker__document"]
    pagination_class = PageNumberPagination
    pagination_class.page_size = 10
    pagination_class.max_page_size = 100
    pagination_class.page_size_query_param = "page_size"

    def get_serializer_class(self):
        if self.action == "list":
            return RawSigningsSerializerFull
        return RawSigningsSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        start_date = self.request.query_params.get("start_date", None)
        end_date = self.request.query_params.get("end_date", None)
        if start_date and end_date:
            start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
            queryset = queryset.filter(
                normalized_date_signed__range=(start_date, end_date)
            )
        return queryset

    @action(detail=False, methods=["DELETE"])
    def delete_all(self, request):
        self.get_queryset().delete()
        return Response(
            {"message": "Todos los fichajes han sido eliminados correctamente"},
            status=204,
        )


@api_view(["POST"])
@parser_classes([MultiPartParser, FormParser])
def import_signings(request, format=None):
    excel_file = request.FILES["excel_file"]
    file_path = save_excel_file(excel_file)
    process_excel.apply_async(file_path)
    signings = RawSignings.objects.order_by("worker__name", "-date_signed").all()
    paginator = PageNumberPagination()
    paginator.page_size = 100
    result_page = paginator.paginate_queryset(signings, request)
    serializer = RawSigningsSerializerFull(result_page, many=True)
    return paginator.get_paginated_response(serializer.data)
