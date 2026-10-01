from django.contrib import admin, messages
from django.utils import timezone

from activities.models import Activity

from .models import Commitment

AUDIT_FIELDS = ('created_at', 'updated_at', 'deleted_at')


class ActivityInline(admin.TabularInline):
    """Actividades que cumplieron el compromiso (solo lectura)."""
    model = Activity
    fields = ("date", "application", "functionary", "measuring")
    readonly_fields = fields
    extra = 0
    can_delete = False
    show_change_link = True

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Commitment)
class CommitmentAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'applic_name',
        'origin',
        'territory',
        'commitment_date',
        'state',
        'is_overdue',
        'functionary',
        'measuring',
    )
    list_filter = ('state', 'territory', 'functionary', 'measuring')
    search_fields = ('applic_name', 'origin', 'territory', 'functionary__lastnames')
    ordering = ('commitment_date',)
    date_hierarchy = 'commitment_date'
    list_select_related = ('functionary', 'measuring')
    readonly_fields = AUDIT_FIELDS
    inlines = [ActivityInline]
    actions = ['mark_in_progress', 'mark_done']

    @admin.display(boolean=True, description="Vencido")
    def is_overdue(self, obj):
        return obj.state != 'DONE' and obj.commitment_date < timezone.localdate()

    def _set_state(self, request, queryset, state, label):
        changed = 0
        for obj in queryset.exclude(state=state):
            obj.state = state
            obj.save()
            changed += 1
        self.message_user(request, f"{changed} compromiso(s) marcado(s) como {label}.", messages.SUCCESS)

    @admin.action(description="Marcar como En proceso")
    def mark_in_progress(self, request, queryset):
        self._set_state(request, queryset, 'IN_PROGRESS', 'En proceso')

    @admin.action(description="Marcar como Realizado")
    def mark_done(self, request, queryset):
        self._set_state(request, queryset, 'DONE', 'Realizado')