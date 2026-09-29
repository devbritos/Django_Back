from django.contrib import admin
from .models import Period, Measuring, Goal


@admin.register(Period)

class PeriodAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'start_date',
        'end_date',
        'computable_days',
        'status',
        'version_parameter',
        'minimum_threshold',
        'maximum_computable_days',
        'semaphore'
    )

    list_filter = ('status', 'semaphore')
    search_fields = ('version_parameter',)


@admin.register(Measuring)
class MeasuringAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'service',
        'measurable_item',
        'validity'
    )

    list_filter = ('validity',)
    search_fields = (
        'service',
        'measurable_item'
    )


@admin.register(Goal)
class GoalAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'target_value',
        'goal_value',
        'unity',
        'cargo',
        'measuring',
        'period',
        'validity'
    )

    list_filter = (
        'validity',
        'period',
        'measuring'
    )

    search_fields = (
        'target_value',
        'unity'
    )

    autocomplete_fields = (
        'cargo',
        'measuring',
        'period'
    )