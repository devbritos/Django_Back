from django.contrib import admin

from auditory.models import auditory

# Register your models here.
@admin.register(auditory)
class AuditoryAdmin(admin.ModelAdmin):
    list_display = ('name_event', 'date_auditory', 'affected_table')
    list_filter = ('date_auditory', 'affected_table')
    search_fields = ('name_event', 'past_value', 'new_value')
    