from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.db.models import Q

from .models import Commitment
from .forms import CommitmentForm
from personal.models import Functionary


class CommitmentListView(LoginRequiredMixin, ListView):
    model = Commitment
    template_name = 'agenda/commitment_list.html'
    context_object_name = 'commitments'
    ordering = ['commitment_date']

    def get_queryset(self):
        queryset = super().get_queryset().select_related('functionary')
        
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
        context['functionaries'] = Functionary.objects.all()
        
        context['selected_state'] = self.request.GET.get('state', '')
        context['selected_functionary'] = self.request.GET.get('functionary', '')
        context['selected_territory'] = self.request.GET.get('territory', '')

        # Cálculos basados en los enum de tu modelo
        all_commitments = Commitment.objects.all()
        total_count = all_commitments.count()
        realized_count = all_commitments.filter(state=Commitment.State.DONE).count()
        
        context['completion_percentage'] = round((realized_count / total_count * 100), 1) if total_count > 0 else 0
        context['pending_count'] = all_commitments.exclude(state=Commitment.State.DONE).count()
        context['expired_count'] = all_commitments.filter(
            commitment_date__lt=today
        ).exclude(state=Commitment.State.DONE).count()

        return context

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now().date()
        context['today'] = today
        
        # Para poblar los select de filtros en la plantilla
        context['states'] = Commitment.State.choices if hasattr(Commitment, 'State') else []
        context['functionaries'] = Functionary.objects.all()
        
        # Filtros seleccionados para mantener los valores en el formulario
        context['selected_state'] = self.request.GET.get('state', '')
        context['selected_responsible'] = self.request.GET.get('responsible', '')
        context['selected_territory'] = self.request.GET.get('territory', '')

        # Cálculos de Indicadores Superiores (RF-15 y RF-16)
        all_commitments = Commitment.objects.all()
        total_count = all_commitments.count()
        
        # Estado asumido para completados: 'REALIZADO'
        realized_count = all_commitments.filter(Q(state='REALIZADO') | Q(state='Realizado')).count()
        
        # Porcentaje realizado del tubo (RF-16)
        context['completion_percentage'] = round((realized_count / total_count * 100), 1) if total_count > 0 else 0
        
        # Cantidad de pendientes
        context['pending_count'] = all_commitments.exclude(Q(state='REALIZADO') | Q(state='Realizado')).count()
        
        # Alertas de compromisos vencidos (RF-15)
        context['expired_count'] = all_commitments.filter(
            commitment_date__lt=today
        ).exclude(Q(state='REALIZADO') | Q(state='Realizado')).count()

        return context


class CommitmentCreateView(LoginRequiredMixin, CreateView):
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
        if hasattr(self.request.user, 'functionary'):
            form.instance.functionary = self.request.user.functionary
        
        messages.success(self.request, 'Compromiso registrado en la Agenda Colectiva.')
        return super().form_valid(form)

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