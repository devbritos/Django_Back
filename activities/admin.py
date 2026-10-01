from django.contrib import admin, messages
from django.db.models import Count, Q
from django.utils import timezone

from .models import Activity, Evidence

AUDIT_FIELDS = ('created_at', 'updated_at', 'deleted_at')


class EvidenceInline(admin.TabularInline):
    model = Evidence
    fk_name = "activity"
    fields = ("name", "author", "date_evidence", "metadata", "validity_state", "funcionary")
    autocomplete_fields = ("funcionary",)
    extra = 0
    show_change_link = True


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'date',
        'application',
        'name_contact',
        'telephone_contact',
        'state_validity',
        'is_valid',
        'functionary',
        'measuring',
        'commitment',
    )
    list_filter = ('state_validity', 'measuring', 'date', 'functionary')
    search_fields = (
        'application',
        'name_contact',
        'telephone_contact',
        'functionary__names',
        'functionary__lastnames',
    )
    ordering = ('-date',)
    date_hierarchy = 'date'
    list_select_related = ('functionary', 'measuring', 'commitment')
    autocomplete_fields = ('functionary', 'measuring', 'commitment')
    readonly_fields = AUDIT_FIELDS
    inlines = [EvidenceInline]

    def get_queryset(self, request):
        # Cuenta las evidencias aprobadas en la misma consulta (sin una por fila).
        return super().get_queryset(request).annotate(
            approved_count=Count(
                "evidences",
                filter=Q(evidences__validity_state=Evidence.Validity.APPROVED),
            )
        )

    @admin.display(boolean=True, description="Válida", ordering="approved_count")
    def is_valid(self, obj):
        # Una actividad solo cuenta si tiene al menos una evidencia aprobada.
        return obj.approved_count > 0


@admin.register(Evidence)
class EvidenceAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'author',
        'date_evidence',
        'validity_state',
        'verificator',
        'activity',
        'funcionary',
    )
    list_filter = ('validity_state', 'date_evidence')
    search_fields = ('name', 'author', 'activity__application')
    ordering = ('-date_evidence',)
    list_select_related = ('verificator', 'activity', 'funcionary')
    autocomplete_fields = ('activity', 'verificator', 'funcionary')
    readonly_fields = AUDIT_FIELDS
    actions = ['approve_evidences', 'reject_evidences']

    def _verifier(self, request):
        # Funcionario del usuario logueado (None hasta que exista User → Functionary).
        return getattr(request.user, "functionary", None)

    @admin.action(description="Aprobar evidencias seleccionadas", permissions=["change"])
    def approve_evidences(self, request, queryset):
        verifier = self._verifier(request)
        approved = skipped = 0
        for ev in queryset.exclude(validity_state=Evidence.Validity.APPROVED):
            if verifier and ev.funcionary_id == verifier.pk:
                skipped += 1  # no puede aprobar lo que subió él mismo
                continue
            ev.validity_state = Evidence.Validity.APPROVED
            ev.date_validity = timezone.localdate()
            ev.verificator = verifier
            ev.save()
            approved += 1
        self.message_user(request, f"{approved} evidencia(s) aprobada(s).", messages.SUCCESS)
        if skipped:
            self.message_user(
                request,
                f"{skipped} omitida(s): el verificador no puede aprobar sus propias evidencias.",
                messages.WARNING,
            )

    @admin.action(description="Rechazar evidencias seleccionadas", permissions=["change"])
    def reject_evidences(self, request, queryset):
        verifier = self._verifier(request)
        rejected = 0
        for ev in queryset.exclude(validity_state=Evidence.Validity.REJECTED):
            ev.validity_state = Evidence.Validity.REJECTED
            ev.date_validity = timezone.localdate()
            ev.verificator = verifier
            ev.save()
            rejected += 1
        self.message_user(request, f"{rejected} evidencia(s) rechazada(s).", messages.SUCCESS)