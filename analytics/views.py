from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import redirect
from personal.models import Functionary, Delegation
from agenda.models import Commitment
from activities.models import Activity  # ajusta el nombre real
from django.utils import timezone
from .calculations import obtener_indicador_funcionario
from configuration.models import Period
from core.delegation_scope import can_select_delegation, scope_queryset
@login_required
@user_passes_test(can_select_delegation)
def admin_dashboard(request):
    functionaries = scope_queryset(
        request, Functionary.objects.all(), lookup='delegation_id'
    )
    delegations = scope_queryset(request, Delegation.objects.all(), lookup='pk')
    commitments = scope_queryset(
        request,
        Commitment.objects.all(),
        lookup='functionary__delegation_id',
    )
    context = {
        'total_funcionarios': functionaries.count(),
        'total_delegaciones': delegations.count(),
        'compromisos_pendientes': commitments.filter(state='PENDING').count(),
        'compromisos_vencidos': commitments.filter(
            state='PENDING', commitment_date__lt=timezone.now()
        ).count(),
    }
    return render(request, 'analytics/admin_dashboard.html', context)
# Create your views here.

@login_required
def user_dashboard(request):
    if can_select_delegation(request.user):
        return redirect('admin_dashboard')

    funcionario = getattr(request.user, 'functionary', None)
    if funcionario is None:
        return render(request, 'analytics/no_functionary.html')

    period = Period.objects.filter(status=True).order_by('-start_date').first()
    indicador = obtener_indicador_funcionario(funcionario, period) if period else None
    commitments = funcionario.commitments.all()
    open_commitments = commitments.exclude(state=Commitment.State.DONE)
    indicator_items = indicador['items'] if indicador else []

    context = {
        'funcionario': funcionario,
        'mis_compromisos': commitments,
        'compromisos_total': commitments.count(),
        'compromisos_pendientes': open_commitments.count(),
        'compromisos_vencidos': open_commitments.filter(
            commitment_date__lt=timezone.localdate()
        ).count(),
        'period': period,
        'indicador': indicador,
        'semaforos': {
            'verde': sum(item['semaforo'] == 'verde' for item in indicator_items),
            'ambar': sum(item['semaforo'] == 'ambar' for item in indicator_items),
            'rojo': sum(item['semaforo'] == 'rojo' for item in indicator_items),
        },
    }
    return render(request, 'analytics/user_dashboard.html', context)


@login_required
def dashboard_redirect(request):
    if can_select_delegation(request.user):
        return redirect('admin_dashboard')
    return redirect('user_dashboard')