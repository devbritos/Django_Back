from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, CreateView
from django.urls import reverse_lazy
from django.db.models import Sum

from .models import Goal, Period

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
    template_name = 'configuration/goal_form.html'
    fields = ['position', 'measuring', 'period', 'weight', 'validity','target_value'] 
    success_url = reverse_lazy('configuration:goal_list')

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
    template_name = 'configuration/period_form.html'
    
    # ATENCIÓN: Revisa tu models.py para confirmar que estos sean los nombres 
    # exactos de los campos de tu modelo Period. 
    fields = ['start_date', 'end_date', 'status','minimum_threshold','maximum_computable_days' ] 
    
    # Por ahora lo redirigimos a la lista de metas al terminar de guardarlo
    success_url = reverse_lazy('configuration:goal_list')

    def test_func(self):
        """Bloquea el acceso a quienes no sean Administrador o Coordinador"""
        if hasattr(self.request.user, 'functionary'):
            return self.request.user.functionary.functionaryrole_set.filter(
                role__role_name__in=['Administrador', 'Coordinador']
            ).exists()
        return False

    def form_valid(self, form):
        # 1. Pausamos el guardado para modificar el objeto
        period = form.save(commit=False)
        
        # 2. Calculamos la diferencia entre las fechas (Término - Inicio)
        diferencia = period.end_date - period.start_date
        
        # 3. Asignamos el resultado al campo computable_days (+1 para incluir el día actual)
        period.computable_days = diferencia.days + 1 
        
        # 4. Ahora sí, guardamos el registro en la base de datos
        period.save()
        
        return super().form_valid(form)