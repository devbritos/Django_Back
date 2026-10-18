from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.utils import timezone

from .models import Activity, Evidence
from .forms import ActivityForm, EvidenceForm, EvidenceValidationForm


# ---------- Activity ----------

class ActivityListView(LoginRequiredMixin, ListView):
    model = Activity
    template_name = 'activities/activity_list.html'
    context_object_name = 'activities'
    ordering = ['-date']


class ActivityCreateView(LoginRequiredMixin, CreateView):
    model = Activity
    form_class = ActivityForm
    template_name = 'activities/activity_form.html'
    success_url = reverse_lazy('activities:activity_list')

    def form_valid(self, form):
        messages.success(self.request, 'Actividad registrada correctamente.')
        return super().form_valid(form)


class ActivityUpdateView(LoginRequiredMixin, UpdateView):
    model = Activity
    form_class = ActivityForm
    template_name = 'activities/activity_form.html'
    success_url = reverse_lazy('activities:activity_list')


class ActivityDeleteView(LoginRequiredMixin, DeleteView):
    model = Activity
    template_name = 'activities/activity_confirm_delete.html'
    success_url = reverse_lazy('activities:activity_list')


# ---------- Evidence ----------

class EvidenceListView(LoginRequiredMixin, ListView):
    model = Evidence
    template_name = 'activities/evidence_list.html'
    context_object_name = 'evidences'
    ordering = ['-created_at']


class EvidenceCreateView(LoginRequiredMixin, CreateView):
    model = Evidence
    form_class = EvidenceForm
    template_name = 'activities/evidence_form.html'
    success_url = reverse_lazy('activities:evidence_list')

    def form_valid(self, form):
        messages.success(self.request, 'Evidencia subida correctamente.')
        return super().form_valid(form)


@login_required
def evidence_validate(request, pk):
    """Vista dedicada para que un verificador apruebe/rechace una evidencia (RF-013)."""
    evidence = get_object_or_404(Evidence, pk=pk)

    if request.method == 'POST':
        form = EvidenceValidationForm(request.POST, instance=evidence)
        if form.is_valid():
            evidencia = form.save(commit=False)
            evidencia.verificator = request.user.functionary
            evidencia.date_validity = timezone.now().date()
            evidencia.save()
            messages.success(request, 'Validación registrada correctamente.')
            return redirect('activities:evidence_list')
    else:
        form = EvidenceValidationForm(instance=evidence)

    return render(request, 'activities/evidence_validate.html', {'form': form, 'evidence': evidence})

# Create your views here.
