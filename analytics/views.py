from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import redirect
from personal.models import Functionary, Delegation
from agenda.models import Commitment
from activities.models import Actividad  # ajusta el nombre real
from django.utils import timezone

@login_required
@user_passes_test(lambda u: u.is_staff)
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
    funcionario = request.user.functionary  # gracias al OneToOneField que ya armamos
    context = {
        'funcionario': funcionario,
        'mis_actividades': funcionario.actividades.count(),  # si tienes ese related_name
        'mis_compromisos': funcionario.commitments.all(),
    }
    return render(request, 'analytics/user_dashboard.html', context)


@login_required
def dashboard_redirect(request):
    if request.user.is_staff:
        return redirect('admin_dashboard')
    return redirect('user_dashboard')