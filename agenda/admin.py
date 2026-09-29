from django.contrib import admin
from .models import Commitment
# Register your models here.

@admin.register(Commitment)

class CommitmentAdmin(admin.ModelAdmin):
    list_display = ('origin','applic_name','state','commitment_date')
    list_filter = ('functionary','measuring')
    search_fields= ('origin','applic_name')


