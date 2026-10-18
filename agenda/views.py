from django.shortcuts import render

# Create your views here.
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import ListView, CreateView, UpdateView, DeleteView

from .models import Commitment
from .forms import CommitmentForm


class CommitmentListView(LoginRequiredMixin, ListView):
    model = Commitment
    template_name = 'agenda/commitment_list.html'
    context_object_name = 'commitments'
    ordering = ['commitment_date']

    def get_queryset(self):
        queryset = super().get_queryset()
        state = self.request.GET.get('state')
        if state:
            queryset = queryset.filter(state=state)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now().date()
        context['today'] = today
        context['states'] = Commitment.State.choices
        return context


class CommitmentCreateView(LoginRequiredMixin, CreateView):
    model = Commitment
    form_class = CommitmentForm
    template_name = 'agenda/commitment_form.html'
    success_url = reverse_lazy('agenda:commitment_list')

    def form_valid(self, form):
        messages.success(self.request, 'Compromiso registrado correctamente.')
        return super().form_valid(form)


class CommitmentUpdateView(LoginRequiredMixin, UpdateView):
    model = Commitment
    form_class = CommitmentForm
    template_name = 'agenda/commitment_form.html'
    success_url = reverse_lazy('agenda:commitment_list')

    def form_valid(self, form):
        messages.success(self.request, 'Compromiso actualizado.')
        return super().form_valid(form)


class CommitmentDeleteView(LoginRequiredMixin, DeleteView):
    model = Commitment
    template_name = 'agenda/commitment_confirm_delete.html'
    success_url = reverse_lazy('agenda:commitment_list')