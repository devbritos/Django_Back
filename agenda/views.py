from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import ListView, CreateView, UpdateView, DeleteView

from .models import Commitment
from .forms import CommitmentForm
from personal.models import Functionary
from core.mixins import FunctionaryOrStaffRequiredMixin, FunctionaryRequiredMixin


def get_commitment_scope(user):
    commitments = Commitment.objects.select_related(
        'functionary',
        'functionary__delegation',
    )
    if user.is_staff or user.is_superuser:
        return commitments

    functionary = getattr(user, 'functionary', None)
    if functionary is None:
        return commitments.none()
    if functionary.is_admin:
        return commitments
    if functionary.is_delegate:
        return commitments.filter(functionary__delegation=functionary.delegation)
    return commitments.filter(functionary=functionary)


class CommitmentListView(LoginRequiredMixin, FunctionaryOrStaffRequiredMixin, ListView):
    model = Commitment
    template_name = 'agenda/commitment_list.html'
    context_object_name = 'commitments'
    ordering = ['commitment_date']

    def get_queryset(self):
        queryset = get_commitment_scope(self.request.user)
        
        state = self.request.GET.get('state')
        functionary_id = self.request.GET.get('functionary')
        territory = self.request.GET.get('territory')
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')

        if state:
            queryset = queryset.filter(state=state)
        if functionary_id:
            queryset = queryset.filter(functionary_id=functionary_id)
        if territory:
            queryset = queryset.filter(territory__icontains=territory)
        if date_from:
            queryset = queryset.filter(commitment_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(commitment_date__lte=date_to)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.localdate()
        context['states'] = Commitment.State.choices
        commitments = get_commitment_scope(self.request.user)
        functionary = getattr(self.request.user, 'functionary', None)
        if (
            self.request.user.is_staff
            or self.request.user.is_superuser
            or (functionary is not None and functionary.is_admin)
        ):
            context['functionaries'] = Functionary.objects.all()
        elif functionary is not None and functionary.is_delegate:
            context['functionaries'] = Functionary.objects.filter(
                delegation=functionary.delegation
            )
        else:
            context['functionaries'] = Functionary.objects.filter(
                pk=functionary.pk
            )
        context['selected_state'] = self.request.GET.get('state', '')
        context['selected_functionary'] = self.request.GET.get('functionary', '')
        context['selected_territory'] = self.request.GET.get('territory', '')
        context['today'] = today
        total_count = commitments.count()
        realized_count = commitments.filter(state=Commitment.State.DONE).count()
        context['completion_percentage'] = round((realized_count / total_count * 100), 1) if total_count > 0 else 0
        context['pending_count'] = commitments.exclude(state=Commitment.State.DONE).count()
        context['expired_count'] = commitments.filter(
            commitment_date__lt=today
        ).exclude(state=Commitment.State.DONE).count()
        return context


class CommitmentCreateView(LoginRequiredMixin, FunctionaryRequiredMixin, CreateView):
    model = Commitment
    form_class = CommitmentForm
    template_name = 'agenda/commitment_form.html'
    success_url = reverse_lazy('agenda:commitment_list')

    def get_initial(self):
        initial = super().get_initial()
        # Si venimos redirigidos desde crear una actividad
        activity_id = self.request.GET.get('activity_id')
        if activity_id:
            initial['activity_id'] = activity_id
        return initial

    def form_valid(self, form):
        # Asigna automáticamente al funcionario conectado
        functionary = getattr(self.request.user, 'functionary', None)
        if functionary is None:
            form.add_error(
                None,
                'Tu usuario no tiene un perfil de funcionario asociado.',
            )
            return self.form_invalid(form)
        form.instance.functionary = functionary
        messages.success(self.request, 'Compromiso registrado correctamente.')
        return super().form_valid(form)


class CommitmentUpdateView(LoginRequiredMixin, FunctionaryOrStaffRequiredMixin, UpdateView):
    model = Commitment
    form_class = CommitmentForm
    template_name = 'agenda/commitment_form.html'
    success_url = reverse_lazy('agenda:commitment_list')

    def get_queryset(self):
        return get_commitment_scope(self.request.user)

    def form_valid(self, form):
        messages.success(self.request, 'Compromiso actualizado.')
        return super().form_valid(form)


class CommitmentDeleteView(LoginRequiredMixin, FunctionaryOrStaffRequiredMixin, DeleteView):
    model = Commitment
    template_name = 'agenda/commitment_confirm_delete.html'
    success_url = reverse_lazy('agenda:commitment_list')

    def get_queryset(self):
        return get_commitment_scope(self.request.user)

    def form_valid(self, form):
        messages.success(self.request, 'Compromiso eliminado correctamente.')
        return super().form_valid(form)