from django.shortcuts import render

# Create your views here.
# personal/views.py
from django.views.generic import ListView
from .models import Delegacion

class DelegacionListView(ListView):
    model = Delegacion
    template_name = 'personal/delegacion_list.html'
    context_object_name = 'delegaciones'