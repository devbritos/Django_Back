from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.utils import timezone
from configuration.models import Goal, Period
from .models import Activity, Evidence
from .forms import ActivityForm, EvidenceForm, EvidenceValidationForm


from datetime import date
from django.views.generic import TemplateView
from django.db.models import Sum, Q
from personal.models import Functionary

# ---------- Activity ----------

class ActivityListView(LoginRequiredMixin, ListView):
    model = Activity
    template_name = 'activities/activity_list.html'
    context_object_name = 'activities'
    ordering = ['-date']

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        
        # Filtrado por rol si tiene perfil Functionary
        if hasattr(user, 'functionary'):
            functionary = user.functionary
            es_admin_o_delegado = functionary.functionaryrole_set.filter(
                role__role_name__in=['Administrador', 'Delegado', 'Coordinador']
            ).exists()
            
            # Si no es jefe/admin, solo ve sus propias actividades
            if not es_admin_o_delegado:
                qs = qs.filter(functionary=functionary)
                
        return qs

class ActivityCreateView(LoginRequiredMixin, CreateView):
    model = Activity
    form_class = ActivityForm
    template_name = 'activities/activity_form.html'
    success_url = reverse_lazy('activities:activity_list')

    def form_valid(self, form):
        # 1. Asigna el funcionario si existe en el usuario logueado
        if hasattr(self.request.user, 'functionary'):
            form.instance.functionary = self.request.user.functionary
        else:
            messages.error(
                self.request,
                'Tu usuario no tiene un perfil de Funcionario asociado.',
            )
            return self.form_invalid(form)

        # 2. Guarda la actividad en la BD y genera self.object
        response = super().form_valid(form)
        messages.success(self.request, 'Actividad registrada correctamente.')

        # 3. Si la actividad ingresa al tubo de trabajo (RF-07), redirige a crear compromiso
        if getattr(self.object, 'enters_pipe', False):
            url_compromiso = reverse('agenda:commitment_create')
            return redirect(f'{url_compromiso}?activity_id={self.object.id}')

        return response

class ActivityUpdateView(LoginRequiredMixin, UpdateView):
    model = Activity
    form_class = ActivityForm
    template_name = 'activities/activity_form.html'
    success_url = reverse_lazy('activities:activity_list')

    def form_valid(self, form):
        messages.success(self.request, 'Actividad actualizada correctamente.')
        return super().form_valid(form)


class ActivityDeleteView(LoginRequiredMixin, DeleteView):
    model = Activity
    template_name = 'activities/activity_confirm_delete.html'
    success_url = reverse_lazy('activities:activity_list')

    def form_valid(self, form):
        messages.success(self.request, 'Actividad eliminada correctamente.')
        return super().form_valid(form)


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


class TrafficLightView(LoginRequiredMixin, TemplateView):
    template_name = 'activities/traffic_light.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = date.today()

                # 1. Obtener el período activo o más reciente
        # Si tu campo status es de texto (ej. 'ACTIVO' / 'INACTIVO')
        period = Period.objects.filter(status='True').order_by('-start_date').first()

        # O si tu campo status es un booleano (True/False):
        # period = Period.objects.filter(status=True).order_by('-start_date').first()
        
        if not period:
            context['error'] = "No hay un período de medición activo configurado."
            return context

        # 2. Cálculos del Período (Avance Esperado al Día)
        total_days = (period.end_date - period.start_date).days + 1
        
        if today < period.start_date:
            elapsed_days = 0
        elif today > period.end_date:
            elapsed_days = total_days
        else:
            elapsed_days = (today - period.start_date).days + 1

        expected_percentage = (elapsed_days / total_days * 100) if total_days > 0 else 0

        # 3. Métrica por Funcionario
        functionaries = Functionary.objects.filter(deleted_at__isnull=True).select_related('position', 'delegation')
        traffic_light_data = []

        for func in functionaries:
            # Obtener las metas configuradas para el cargo del funcionario en este período
            goals = Goal.objects.filter(
                position=func.position,
                period=period,
                validity=True
            ).select_related('measuring')

            total_weighted_compliance = 0.0

            for goal in goals:
                # Sumar actividades realizadas y validadas por el funcionario para esta meta/ítem
                # Usas la suma acumulada de la cantidad:
                achieved_query = Activity.objects.filter(
                    functionary=func,
                    measuring=goal.measuring,
                    date__range=[period.start_date, period.end_date],
                    is_validated=True
                ).aggregate(total=Sum('quantity'))

                achieved = achieved_query['total'] or 0

                # Porcentaje de cumplimiento del ítem (Avance / Meta)
                item_compliance = (achieved / goal.target_value) if goal.target_value > 0 else 0
                # Cap de 100% por ítem antes de ponderar (opcional según reglas)
                item_compliance = min(item_compliance, 1.0)

                # Sumar al cumplimiento ponderado
                total_weighted_compliance += (item_compliance * float(goal.weight))

            # 4. Determinar Estado del Semáforo (Verde, Amarillo, Rojo)
            # Diferencia entre lo logrado y lo esperado
            diff = total_weighted_compliance - expected_percentage

            if diff >= -5:
                status = 'green'    # En línea o superior
                label = 'En línea con lo esperado'
            elif -15 <= diff < -5:
                status = 'yellow'   # Atención
                label = 'Atención'
            else:
                status = 'red'      # Bajo lo esperado
                label = 'Bajo lo esperado'

            traffic_light_data.append({
                'functionary': func,
                'achieved_percentage': round(total_weighted_compliance, 1),
                'expected_percentage': round(expected_percentage, 1),
                'status': status,
                'label': label,
            })

        # Contexto final para el template
        context['period'] = period
        context['today'] = today
        context['total_days'] = total_days
        context['elapsed_days'] = elapsed_days
        context['expected_percentage'] = round(expected_percentage, 1)
        context['traffic_light_data'] = traffic_light_data

        return context