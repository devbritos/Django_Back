from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.utils import timezone

from agenda.models import Commitment
from core.delegation_scope import scope_queryset
from personal.models import Functionary

from .models import Activity, Evidence
from .forms import ActivityForm, EvidenceForm, EvidenceValidationForm


# ---------- Activity ----------

class DelegationScopedView:
    delegation_lookup = 'functionary__delegation_id'

    def get_queryset(self):
        return scope_queryset(
            self.request,
            super().get_queryset(),
            lookup=self.delegation_lookup,
        )

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if 'functionary' in form.fields:
            form.fields['functionary'].queryset = scope_queryset(
                self.request,
                Functionary.objects.all(),
                lookup='delegation_id',
            )
        if 'activity' in form.fields:
            form.fields['activity'].queryset = scope_queryset(
                self.request, Activity.objects.all()
            )
        if 'commitment' in form.fields:
            form.fields['commitment'].queryset = scope_queryset(
                self.request,
                Commitment.objects.all(),
                lookup='functionary__delegation_id',
            )
        return form


class ActivityListView(DelegationScopedView, LoginRequiredMixin, ListView):
    model = Activity
    template_name = 'activities/activity_list.html'
    context_object_name = 'activities'
    ordering = ['-date']


class ActivityCreateView(DelegationScopedView, LoginRequiredMixin, CreateView):
    model = Activity
    form_class = ActivityForm
    template_name = 'activities/activity_form.html'
    success_url = reverse_lazy('activities:activity_list')

    def form_valid(self, form):
        messages.success(self.request, 'Actividad registrada correctamente.')
        return super().form_valid(form)


class ActivityUpdateView(DelegationScopedView, LoginRequiredMixin, UpdateView):
    model = Activity
    form_class = ActivityForm
    template_name = 'activities/activity_form.html'
    success_url = reverse_lazy('activities:activity_list')

    def form_valid(self, form):
        messages.success(self.request, 'Actividad actualizada correctamente.')
        return super().form_valid(form)


class ActivityDeleteView(DelegationScopedView, LoginRequiredMixin, DeleteView):
    model = Activity
    template_name = 'activities/activity_confirm_delete.html'
    success_url = reverse_lazy('activities:activity_list')


# ---------- Evidence ----------

class EvidenceListView(DelegationScopedView, LoginRequiredMixin, ListView):
    model = Evidence
    template_name = 'activities/evidence_list.html'
    context_object_name = 'evidences'
    ordering = ['-created_at']


class EvidenceCreateView(DelegationScopedView, LoginRequiredMixin, CreateView):
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
    evidence = get_object_or_404(
        scope_queryset(request, Evidence.objects.all()), pk=pk
    )

    if request.method == 'POST':
        form = EvidenceValidationForm(request.POST, instance=evidence)
        if form.is_valid():
            evidencia = form.save(commit=False)
            evidencia.verificator = getattr(request.user, 'functionary', None)
            evidencia.date_validity = timezone.now().date()
            evidencia.save()
            messages.success(request, 'Validación registrada correctamente.')
            return redirect('activities:evidence_list')
    else:
        form = EvidenceValidationForm(instance=evidence)

    return render(request, 'activities/evidence_validate.html', {'form': form, 'evidence': evidence})

# Create your views here.
