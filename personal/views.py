from django.shortcuts import render

# Create your views here.
# personal/views.py
from django.views.generic import ListView
from .models import Delegation

class DelegationListView(ListView):
    model = Delegation
    template_name = 'personal/delegation_list.html'
    context_object_name = 'delegations'