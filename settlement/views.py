from django.shortcuts import render
from django.http import HttpResponse
import pandas as pd
from .models import Settlement, SettlementDetails
from workers.models import Worker, RawSignings

rooms = [
    {'id': 1, 'name': 'Lets learn Python!'},
    {'id': 2, 'name': 'Design with me'},
    {'id': 3, 'name': 'Frontend developers'},
]

# Create your views here.
def home(request):
    context = {'rooms': rooms}
    return render(request, 'settlement/home.html', context)

def room(request, pk):
    room = None
    for i in rooms:
        if i['id'] == int(pk):
            room = i
    context = {'room': room}
    return render(request, 'settlement/room.html', context)

def process_signings(request):
    return HttpResponse("File uploaded and processed successfully")
