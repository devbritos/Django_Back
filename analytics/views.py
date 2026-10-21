from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import redirect
from personal.models import Functionary, Delegation
from agenda.models import Commitment
from activities.models import Activity  # ajusta el nombre real
from django.utils import timezone
from .calculations import obtener_indicador_funcionario
from configuration.models import Period
@login_required
@user_passes_test(
    lambda user: user.is_staff
    or user.is_superuser
    or (
        hasattr(user, 'functionary')
        and user.functionary.is_admin
    )
)
def admin_dashboard(request):
    context = {
        'total_funcionarios': Functionary.objects.count(),
        'total_delegaciones': Delegation.objects.count(),
        'compromisos_pendientes': Commitment.objects.filter(state='PENDING').count(),
        'compromisos_vencidos': Commitment.objects.filter(state='PENDING', commitment_date__lt=timezone.now()).count(),
    }
    return render(request, 'analytics/admin_dashboard.html', context)
# Create your views here.

@login_required
def user_dashboard(request):
    funcionario = getattr(request.user, 'functionary', None)
    if funcionario is None:
        return render(request, 'analytics/no_functionary.html')

    period = Period.objects.filter(status=True).order_by('-start_date').first()
    indicador = obtener_indicador_funcionario(funcionario, period) if period else None

    context = {
        'funcionario': funcionario,
        'mis_compromisos': funcionario.commitments.all(),
        'period': period,
        'indicador': indicador,
    }
    return render(request, 'analytics/user_dashboard.html', context)


@login_required
def dashboard_redirect(request):
    functionary = getattr(request.user, 'functionary', None)
    if request.user.is_staff or request.user.is_superuser or (
        functionary and functionary.is_admin
    ):
        return redirect('admin_dashboard')
    return redirect('user_dashboard')