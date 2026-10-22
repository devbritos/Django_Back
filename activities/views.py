from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.utils import timezone
from configuration.models import Goal, Period
from .models import Activity, Evidence
from .forms import (
    ActivityForm,
    ActivityValidationForm,
    EvidenceForm,
    EvidenceValidationForm,
)
from django.views.generic import TemplateView
from django.db.models import Sum
from core.exports import excel_response
from core.lists import search_queryset
from personal.models import Functionary
from core.mixins import (
    DelegateRequiredMixin,
    FunctionaryRequiredMixin,
    FunctionaryOrStaffRequiredMixin,
    VerifierRequiredMixin,
)


def get_activity_scope(user):
    activities = Activity.objects.all()
    functionary = getattr(user, 'functionary', None)
    if user.is_staff or user.is_superuser or (
        functionary is not None and functionary.has_global_scope
    ):
        return activities
    if functionary is None:
        return activities.none()
    if functionary.is_delegate or functionary.is_verifier:
        return activities.filter(functionary__delegation=functionary.delegation)
    return activities.filter(functionary=functionary)


def can_validate_own_activity(user):
    functionary = getattr(user, 'functionary', None)
    return (
        user.is_staff
        or user.is_superuser
        or (functionary is not None and functionary.is_admin)
    )


# ---------- Activity ----------

class ActivityListView(LoginRequiredMixin, FunctionaryOrStaffRequiredMixin, ListView):
    model = Activity
    template_name = 'activities/activity_list.html'
    context_object_name = 'activities'
    ordering = ['-date']
    paginate_by = 20

    def get_queryset(self):
        queryset = get_activity_scope(self.request.user).select_related(
            'functionary',
            'functionary__delegation',
            'measuring',
        )
        queryset = search_queryset(
            queryset,
            self.request.GET.get('q'),
            'application',
            'taken_action',
            'name_contact',
            'telephone_contact',
            'measuring__service',
            'measuring__measurable_item',
            'functionary__names',
            'functionary__lastnames',
        )
        return queryset.order_by(*self.ordering)

    def render_to_response(self, context, **response_kwargs):
        if self.request.GET.get('export') == 'xlsx':
            return excel_response(
                'actividades.xlsx',
                ['Fecha', 'Solicitud', 'Acción realizada', 'Contacto',
                 'Teléfono', 'Ítem', 'Cantidad', 'Delegación', 'Responsable',
                 'Estado'],
                (
                    [
                        item.date,
                        item.application,
                        item.taken_action,
                        item.name_contact,
                        item.telephone_contact,
                        item.measuring.service,
                        item.quantity,
                        item.functionary.delegation.name,
                        item.functionary.full_name,
                        item.get_state_validity_display(),
                    ]
                    for item in self.get_queryset()
                ),
            )
        add_pagination_context(self.request, context)
        return super().render_to_response(context, **response_kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        functionary = getattr(self.request.user, 'functionary', None)
        context['can_validate_activities'] = (
            self.request.user.is_staff
            or self.request.user.is_superuser
            or (functionary is not None and functionary.is_verifier)
        )
        context['can_validate_own_activities'] = can_validate_own_activity(
            self.request.user
        )
        context['current_functionary_id'] = (
            functionary.pk if functionary is not None else None
        )
        return context


class ActivityCreateView(LoginRequiredMixin, FunctionaryRequiredMixin, CreateView):
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

class ActivityUpdateView(LoginRequiredMixin, FunctionaryOrStaffRequiredMixin, UpdateView):
    model = Activity
    form_class = ActivityForm
    template_name = 'activities/activity_form.html'
    success_url = reverse_lazy('activities:activity_list')

    def get_queryset(self):
        return get_activity_scope(self.request.user)

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Actividad actualizada correctamente.')
        return response


class ActivityDeleteView(LoginRequiredMixin, FunctionaryOrStaffRequiredMixin, DeleteView):
    model = Activity
    template_name = 'activities/activity_confirm_delete.html'
    success_url = reverse_lazy('activities:activity_list')

    def get_queryset(self):
        return get_activity_scope(self.request.user)

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Actividad eliminada correctamente.')
        return response


class ActivityValidateView(
    LoginRequiredMixin,
    VerifierRequiredMixin,
    UpdateView,
):
    model = Activity
    form_class = ActivityValidationForm
    template_name = 'activities/activity_validate.html'
    context_object_name = 'activity'
    success_url = reverse_lazy('activities:activity_list')

    def get_queryset(self):
        queryset = get_activity_scope(self.request.user).filter(
            state_validity='PENDING',
        )
        functionary = getattr(self.request.user, 'functionary', None)
        if functionary is not None and not can_validate_own_activity(
            self.request.user
        ):
            queryset = queryset.exclude(functionary=functionary)
        return queryset

    def form_valid(self, form):
        response = super().form_valid(form)
        if self.object.state_validity == 'VALIDATED':
            messages.success(
                self.request,
                'Actividad validada; su avance se reflejará en el semáforo.',
            )
        else:
            messages.warning(
                self.request,
                'Actividad rechazada; no se contabilizará en el semáforo.',
            )
        return response


# ---------- Evidence ----------

class EvidenceListView(LoginRequiredMixin, FunctionaryOrStaffRequiredMixin, ListView):
    model = Evidence
    template_name = 'activities/evidence_list.html'
    context_object_name = 'evidences'
    ordering = ['-created_at']
    paginate_by = 20

    def get_queryset(self):
        queryset = get_evidence_scope(self.request.user).select_related(
            'activity',
            'functionary',
            'functionary__delegation',
        )
        queryset = search_queryset(
            queryset,
            self.request.GET.get('q'),
            'name',
            'author',
            'metadata',
            'activity__application',
            'functionary__names',
            'functionary__lastnames',
        )
        return queryset.order_by(*self.ordering)

    def render_to_response(self, context, **response_kwargs):
        if self.request.GET.get('export') == 'xlsx':
            return excel_response(
                'evidencias.xlsx',
                ['Nombre', 'Actividad', 'Autor', 'Fecha', 'Estado',
                 'Funcionario', 'Delegación'],
                (
                    [
                        evidence.name,
                        evidence.activity.application,
                        evidence.author,
                        evidence.date_evidence,
                        evidence.get_validity_state_display(),
                        evidence.functionary.full_name,
                        evidence.functionary.delegation.name,
                    ]
                    for evidence in self.get_queryset()
                ),
            )
        add_pagination_context(self.request, context)
        return super().render_to_response(context, **response_kwargs)


class EvidenceCreateView(LoginRequiredMixin, FunctionaryRequiredMixin, CreateView):
    model = Evidence
    form_class = EvidenceForm
    template_name = 'activities/evidence_form.html'
    success_url = reverse_lazy('activities:evidence_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        user = self.request.user
        functionary = user.functionary
        kwargs['activities'] = get_activity_scope(user)
        return kwargs

    def form_valid(self, form):
        form.instance.functionary = self.request.user.functionary
        response = super().form_valid(form)
        messages.success(self.request, 'Evidencia subida correctamente.')
        return response


class EvidenceValidateView(
    LoginRequiredMixin,
    VerifierRequiredMixin,
    UpdateView,
):
    model = Evidence
    form_class = EvidenceValidationForm
    template_name = 'activities/evidence_validate.html'
    success_url = reverse_lazy('activities:evidence_list')

    def get_queryset(self):
        return get_evidence_scope(self.request.user)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['verificator'] = getattr(self.request.user, 'functionary', None)
        return kwargs

    def form_valid(self, form):
        evidence = form.save(commit=False)
        evidence.date_validity = timezone.localdate()
        evidence.save()
        messages.success(self.request, 'Validación registrada correctamente.')
        return redirect(self.get_success_url())

# Create your views here.


class TrafficLightView(LoginRequiredMixin, DelegateRequiredMixin, TemplateView):
    template_name = 'activities/traffic_light.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.localdate()
        period = Period.objects.filter(status=True).order_by('-start_date').first()
        
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
        functionaries = Functionary.objects.filter(
            deleted_at__isnull=True
        ).select_related('position', 'delegation')
        user = self.request.user
        if not user.is_superuser and not user.functionary.has_global_scope:
            functionaries = functionaries.filter(
                delegation=user.functionary.delegation
            )
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
                    state_validity='VALIDATED',
                ).aggregate(total=Sum('quantity'))

                achieved = achieved_query['total'] or 0

                # Porcentaje de cumplimiento del ítem (Avance / Meta)
                target_value = float(goal.target_value)
                item_compliance = (achieved / target_value) if target_value > 0 else 0
                # Cap de 100% por ítem antes de ponderar (opcional según reglas)
                item_compliance = min(item_compliance, 1.0)

                # Sumar al cumplimiento ponderado
                total_weighted_compliance += item_compliance * float(goal.weight)

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


def get_evidence_scope(user):
    evidences = Evidence.objects.all()
    functionary = getattr(user, 'functionary', None)
    if user.is_staff or user.is_superuser or (
        functionary is not None and functionary.has_global_scope
    ):
        return evidences
    if functionary is None:
        return evidences.none()
    if functionary.is_delegate:
        return evidences.filter(functionary__delegation=functionary.delegation)
    return evidences.filter(functionary=functionary)


def add_pagination_context(request, context):
    query_params = request.GET.copy()
    query_params.pop('page', None)
    query_params.pop('export', None)
    context['query_params'] = query_params.urlencode()
    context['search_query'] = request.GET.get('q', '')