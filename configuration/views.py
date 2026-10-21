from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import ListView, CreateView
from django.urls import reverse_lazy

from .models import Goal, Period
from .forms import GoalForm, PeriodForm
from core.mixins import AdminRequiredMixin


class GoalListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    model = Goal
    template_name = 'configuration/goal_list.html'
    context_object_name = 'goals'

    def get_queryset(self):
        queryset = Goal.objects.select_related('position', 'measuring', 'period').filter(validity=True)
        period_id = self.request.GET.get('period')
        if period_id:
            queryset = queryset.filter(period_id=period_id)

        return queryset.order_by('period', 'position__name', 'measuring__service')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['periods'] = Period.objects.all().order_by('-start_date')
        context['selected_period'] = self.request.GET.get('period', '')

        resumen = {}

        for goal in context['goals']:
            key = (goal.position_id, goal.period_id)
            if key not in resumen:
                resumen[key] = {
                    'position': goal.position,
                    'period': goal.period,
                    'total_weight': 0,
                    'items': [],
                }
            resumen[key]['total_weight'] += goal.weight
            resumen[key]['items'].append(goal)

        context['resumen'] = resumen.values()
        return context


class GoalCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    model = Goal
    form_class = GoalForm
    template_name = 'configuration/goal_form.html'
    success_url = reverse_lazy('configuration:goal_list')

    def form_valid(self, form):
        messages.success(self.request, 'Meta registrada correctamente.')
        return super().form_valid(form)

class PeriodCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    model = Period
    form_class = PeriodForm
    template_name = 'configuration/period_form.html'
    success_url = reverse_lazy('configuration:goal_list')

    def form_valid(self, form):
        messages.success(self.request, 'Período registrado correctamente.')
        return super().form_valid(form)
