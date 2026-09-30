from django.contrib import messages
from django.db.models import ProtectedError
from django.forms import modelform_factory
from django.shortcuts import get_object_or_404, redirect, render

from core.decorators import require

from .models import Delegation, Functionary, FunctionaryRole, Position, Role

# ---------- Delegation ----------
DelegationForm = modelform_factory(Delegation, fields=["name", "state", "field"])


@require("personal.view_delegation")
def delegation_list(request):
    qs = Delegation.objects.all()
    if not request.GET.get("all"):
        qs = qs.filter(state='ACTIVO')
    return render(request, "personal/delegation_list.html", {
        "object_list": qs,
        "showing_all": bool(request.GET.get("all")),
    })


@require("personal.add_delegation")
def delegation_create(request):
    form = DelegationForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, "Registro creado correctamente.")
        return redirect("personal:delegation_list")
    return render(request, "personal/delegation_form.html", {"form": form})


@require("personal.change_delegation")
def delegation_update(request, pk):
    obj = get_object_or_404(Delegation, pk=pk)
    form = DelegationForm(request.POST or None, instance=obj)
    if form.is_valid():
        form.save()
        messages.success(request, "Registro actualizado correctamente.")
        return redirect("personal:delegation_list")
    return render(request, "personal/delegation_form.html", {"form": form, "object": obj})


@require("personal.change_delegation")
def delegation_delete(request, pk):
    """No borra: marca el registro como inactivo."""
    obj = get_object_or_404(Delegation, pk=pk)
    if request.method == "POST":
        obj.state = 'INACTIVO'
        obj.save(update_fields=["state"])
        messages.success(request, "Registro desactivado.")
        return redirect("personal:delegation_list")
    return render(request, "personal/delegation_confirm_delete.html", {"object": obj})

# ---------- Position ----------
PositionForm = modelform_factory(Position, fields=["name", "validity"])


@require("personal.view_position")
def position_list(request):
    qs = Position.objects.all()
    if not request.GET.get("all"):
        qs = qs.filter(validity=True)
    return render(request, "personal/position_list.html", {
        "object_list": qs,
        "showing_all": bool(request.GET.get("all")),
    })


@require("personal.add_position")
def position_create(request):
    form = PositionForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, "Registro creado correctamente.")
        return redirect("personal:position_list")
    return render(request, "personal/position_form.html", {"form": form})


@require("personal.change_position")
def position_update(request, pk):
    obj = get_object_or_404(Position, pk=pk)
    form = PositionForm(request.POST or None, instance=obj)
    if form.is_valid():
        form.save()
        messages.success(request, "Registro actualizado correctamente.")
        return redirect("personal:position_list")
    return render(request, "personal/position_form.html", {"form": form, "object": obj})


@require("personal.change_position")
def position_delete(request, pk):
    """No borra: marca el registro como inactivo."""
    obj = get_object_or_404(Position, pk=pk)
    if request.method == "POST":
        obj.validity = False
        obj.save(update_fields=["validity"])
        messages.success(request, "Registro desactivado.")
        return redirect("personal:position_list")
    return render(request, "personal/position_confirm_delete.html", {"object": obj})

# ---------- Functionary ----------
FunctionaryForm = modelform_factory(Functionary, fields=["names", "lastnames", "delegation", "position"])


@require("personal.view_functionary")
def functionary_list(request):
    qs = Functionary.objects.select_related("delegation", "position")
    if delegation := request.GET.get("delegation"):
        qs = qs.filter(delegation_id=delegation)
    if position := request.GET.get("position"):
        qs = qs.filter(position_id=position)
    return render(request, "personal/functionary_list.html", {
        "object_list": qs,
        "showing_all": bool(request.GET.get("all")),
        "delegations": Delegation.objects.filter(state="ACTIVO"),
        "positions": Position.objects.filter(validity=True),
    })


@require("personal.add_functionary")
def functionary_create(request):
    form = FunctionaryForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, "Registro creado correctamente.")
        return redirect("personal:functionary_list")
    return render(request, "personal/functionary_form.html", {"form": form})


@require("personal.change_functionary")
def functionary_update(request, pk):
    obj = get_object_or_404(Functionary, pk=pk)
    form = FunctionaryForm(request.POST or None, instance=obj)
    if form.is_valid():
        form.save()
        messages.success(request, "Registro actualizado correctamente.")
        return redirect("personal:functionary_list")
    return render(request, "personal/functionary_form.html", {"form": form, "object": obj})


@require("personal.delete_functionary")
def functionary_delete(request, pk):
    obj = get_object_or_404(Functionary, pk=pk)
    if request.method == "POST":
        try:
            obj.delete()
            messages.success(request, "Registro eliminado.")
        except ProtectedError:
            messages.error(request, "No se puede eliminar: tiene registros asociados.")
        return redirect("personal:functionary_list")
    return render(request, "personal/functionary_confirm_delete.html", {"object": obj})


# ---------- Role ----------
RoleForm = modelform_factory(Role, fields=["role_name"])


@require("personal.view_role")
def role_list(request):
    return render(request, "personal/role_list.html", {"object_list": Role.objects.all()})


@require("personal.add_role")
def role_create(request):
    form = RoleForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, "Registro creado correctamente.")
        return redirect("personal:role_list")
    return render(request, "personal/role_form.html", {"form": form})


@require("personal.change_role")
def role_update(request, pk):
    obj = get_object_or_404(Role, pk=pk)
    form = RoleForm(request.POST or None, instance=obj)
    if form.is_valid():
        form.save()
        messages.success(request, "Registro actualizado correctamente.")
        return redirect("personal:role_list")
    return render(request, "personal/role_form.html", {"form": form, "object": obj})


@require("personal.delete_role")
def role_delete(request, pk):
    obj = get_object_or_404(Role, pk=pk)
    if request.method == "POST":
        # FunctionaryRole usa CASCADE: sin este chequeo se perderían las asignaciones en silencio.
        if obj.functionaryrole_set.exists():
            messages.error(request, "No se puede eliminar: hay funcionarios con este rol.")
        else:
            obj.delete()
            messages.success(request, "Registro eliminado.")
        return redirect("personal:role_list")
    return render(request, "personal/role_confirm_delete.html", {"object": obj})


# ---------- FunctionaryRole (asignar roles a un funcionario) ----------
FunctionaryRoleForm = modelform_factory(FunctionaryRole, fields=["functionary", "role"])


@require("personal.view_functionaryrole")
def functionary_role_list(request):
    qs = FunctionaryRole.objects.select_related("functionary", "role")
    if functionary := request.GET.get("functionary"):
        qs = qs.filter(functionary_id=functionary)
    return render(request, "personal/functionary_role_list.html", {
        "object_list": qs,
        "functionaries": Functionary.objects.all(),
    })


@require("personal.add_functionaryrole")
def functionary_role_create(request):
    # Permite abrir el formulario con el funcionario ya elegido: ?functionary=3
    initial = {"functionary": request.GET.get("functionary")}
    form = FunctionaryRoleForm(request.POST or None, initial=initial)
    if form.is_valid():
        form.save()
        messages.success(request, "Rol asignado correctamente.")
        return redirect("personal:functionary_role_list")
    return render(request, "personal/functionary_role_form.html", {"form": form})


# No hay "editar": para cambiar un rol se quita la asignación y se crea otra.
@require("personal.delete_functionaryrole")
def functionary_role_delete(request, pk):
    obj = get_object_or_404(FunctionaryRole, pk=pk)
    if request.method == "POST":
        obj.delete()
        messages.success(request, "Rol quitado.")
        return redirect("personal:functionary_role_list")
    return render(request, "personal/functionary_role_confirm_delete.html", {"object": obj})