def can_select_delegation(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)


def current_delegation_id(request):
    if not request.user.is_authenticated:
        return None

    if can_select_delegation(request.user):
        delegation_id = request.session.get("selected_delegation_id")
        if not delegation_id:
            return None

        from personal.models import Delegation

        if Delegation.objects.filter(pk=delegation_id).exists():
            return delegation_id
        request.session.pop("selected_delegation_id", None)
        return None

    functionary = getattr(request.user, "functionary", None)
    return functionary.delegation_id if functionary else None


def scope_queryset(request, queryset, lookup="functionary__delegation_id"):
    if not request.user.is_authenticated:
        return queryset.none()

    delegation_id = current_delegation_id(request)
    if delegation_id is None:
        return queryset if can_select_delegation(request.user) else queryset.none()

    return queryset.filter(**{lookup: delegation_id})
