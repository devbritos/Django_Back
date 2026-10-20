from personal.models import Delegation

from .delegation_scope import can_select_delegation, current_delegation_id


def delegation_context(request):
    if not request.user.is_authenticated:
        return {}

    delegation_id = current_delegation_id(request)
    can_select = can_select_delegation(request.user)
    context = {
        "current_delegation": None,
        "can_select_delegation": can_select,
        "viewing_all_delegations": can_select and delegation_id is None,
    }

    if delegation_id is not None:
        context["current_delegation"] = Delegation.objects.filter(
            pk=delegation_id
        ).first()

    if can_select:
        context["delegation_choices"] = Delegation.objects.order_by("name")
    else:
        functionary = getattr(request.user, "functionary", None)
        context["current_delegation"] = functionary.delegation if functionary else None

    return context
