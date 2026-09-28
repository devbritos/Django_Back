from django.contrib import admin
from .models import Delegation, Functionary
# Register your models here.

@admin.register(Delegation)

class DelegationAdmin(admin.ModelAdmin):
    list_display = ('name','state','field')
    search_fields = ('name','state')

@admin.register(Functionary)

class FunctionaryAdmin(admin.ModelAdmin):
    list_display = ('names','lastnames','delegation')
    list_filter = ('delegation','names',)
    search_fields = ('names','lastnames','delegation')