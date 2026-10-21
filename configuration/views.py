from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.views.generic import ListView, CreateView
from django.urls import reverse_lazy
from django.db.models import Sum

from .models import Goal, Period
from .forms import GoalForm, PeriodForm

class GoalListView(LoginRequiredMixin, ListView):
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


class GoalCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Goal
    form_class = GoalForm
    template_name = 'configuration/goal_form.html'
    success_url = reverse_lazy('configuration:goal_list')

    def form_valid(self, form):
        messages.success(self.request, 'Meta registrada correctamente.')
        return super().form_valid(form)

    def test_func(self):
            # 1. Verificamos si el usuario tiene un funcionario asociado
            if hasattr(self.request.user, 'functionary'):
                
                # --- TRUCO DE DEBUG ---
                # Vamos a imprimir en la terminal los roles exactos que tiene este usuario
                roles_actuales = list(self.request.user.functionary.functionaryrole_set.values_list('role__role_name', flat=True))
                print(f"ROLES DEL USUARIO EN LA BD: {roles_actuales}")
                
                # 2. Verificamos si tiene el permiso
                tiene_permiso = self.request.user.functionary.functionaryrole_set.filter(
                    role__role_name__in=['Administrador', 'Coordinador']
                ).exists()
                
                print(f"¿SE LE PERMITE EL ACCESO?: {tiene_permiso}")
                return tiene_permiso
                
            print("EL USUARIO LOGUEADO NO TIENE UN PERFIL 'FUNCTIONARY' ASOCIADO")
            return False

# Asegúrate de que Period esté importado arriba junto con Goal
# from .models import Goal, Period

class PeriodCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Period
    form_class = PeriodForm
    template_name = 'configuration/period_form.html'
    success_url = reverse_lazy('configuration:goal_list')

    def form_valid(self, form):
        messages.success(self.request, 'Período registrado correctamente.')
        return super().form_valid(form)

    def test_func(self):
        """Bloquea el acceso a quienes no sean Administrador o Coordinador"""
        if hasattr(self.request.user, 'functionary'):
            return self.request.user.functionary.functionaryrole_set.filter(
                role__role_name__in=['Administrador', 'Coordinador']
            ).exists()
        return False
