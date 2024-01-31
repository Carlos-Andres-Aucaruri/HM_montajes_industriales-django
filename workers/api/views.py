from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from workers.models import Worker, RawSignings
from ..serializers import WorkerSerializer, RawSigningsSerializer

@api_view(['GET'])
def getRoutes(request):
    routes = [
        'GET /api',
        'GET /api/workers',
        'GET /api/workers/:id',
        'GET /api/signings',
        'GET /api/signings/:worker_id',
    ]
    return Response(routes)

@api_view(['GET'])
def getWorkers(request):
    workers = Worker.objects.all()
    serializer = WorkerSerializer(workers, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def getWorker(request, pk):
    worker = Worker.objects.get(id=pk)
    serializer = WorkerSerializer(worker, many=False)
    return Response(serializer.data)

@api_view(['GET'])
def getSignings(request):
    signings = RawSignings.objects.all()
    serializer = RawSigningsSerializer(signings, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def getSigningsByWorker(request, worker_id):
    worker = Worker.objects.get(id=int(worker_id))
    signings = RawSignings.objects.filter(worker=worker).all()
    serializer = RawSigningsSerializer(signings, many=True)
    return Response(serializer.data)