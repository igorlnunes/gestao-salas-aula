from django.shortcuts import render, redirect
from django.views.generic import ListView, CreateView
from django.urls import reverse_lazy
from .models import Room
from .forms import RoomForm

# Create your views here.
def welcome(request):
    return render(request, 'welcome.html')

class RoomListView(ListView):
    model = Room
    template_name = 'room_list.html'
    context_object_name = 'rooms'

class RoomCreateView(CreateView):
    model = Room
    form_class = RoomForm
    template_name = 'room_form.html'
    success_url = reverse_lazy('room_list')
