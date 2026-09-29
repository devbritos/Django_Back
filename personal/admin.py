from django.contrib import admin
from .models import Delegation, Functionary,Position,Role,FunctionaryRole
# Register your models here.

@admin.register(Delegation)

class DelegationAdmin(admin.ModelAdmin):
    list_display = ('name','state','field')
    list_filter = ('state','field')
    search_fields = ('name',)

@admin.register(Functionary)

class FunctionaryAdmin(admin.ModelAdmin):
    list_display = ('names','lastnames','delegation','position')
    list_filter = ('delegation','position')
    search_fields = ('names','lastnames','delegation__name')

@admin.register(Position)

class PositionAdmin(admin.ModelAdmin):
    list_display = ('name','validity')
    list_filter = ('validity',)
    search_fields = ('name',)
    
@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('role_name',)
    search_fields = ('role_name',)


@admin.register(FunctionaryRole)
class FunctionaryRoleAdmin(admin.ModelAdmin):
    list_display= ('functionary','role')
    search_fields = ('role__role_name',)