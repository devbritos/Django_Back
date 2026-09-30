from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Activity, Evidence


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'date',
        'application',
        'name_contact',
        'telephone_contact',
        'state_validity',
        'functionary',
        'measuring',
        'commitment',
    )

    list_filter = (
        'state_validity',
        'measuring',
    )

    search_fields = (
        'application',
        'name_contact',
        'telephone_contact',
    )


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

    list_filter = (
        'validity_state',
        'date_evidence',
    )

    search_fields = (
        'name',
        'author',
    )