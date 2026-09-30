from django.shortcuts import render
from django.urls import reverse_lazy
# Create your views here.
# personal/views.py
from django.views.generic import ListView,CreateView,UpdateView,DeleteView
from .models import Delegation

class DelegationListView(ListView):
    model = Delegation
    template_name = 'personal/delegation_list.html'
    context_object_name = 'delegations'

class DelegationCreateView(CreateView):
    model = Delegation
    fields = ['name','state','field']
    template_name = 'personal/delegation_form.html'
    success_url = reverse_lazy('delegation_list')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        for field in form.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
        return form


class DelegationUpdateView(UpdateView):
    model = Delegation
    fields = ['name','state','field']
    template_name = 'personal/delegation_form.html'
    success_url = reverse_lazy('delegation_list')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        for field in form.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
        return form

class DelegationDeleteView(DeleteView):
    model = Delegation
    template_name = "personal/delegation_delete.html"
    success_url = reverse_lazy('delegation_list')