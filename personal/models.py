from django.contrib.auth.models import User
from django.db import models
from core.models import BaseModel


class Delegation(BaseModel):
    STATES_CHOICES = [('ACTIVO', 'Activo'), ('INACTIVO', 'Inactivo')]

    FIELD_CHOICES = [('RURAL', 'Rural'), ('URBANO', 'Urbano')]

    name = models.CharField(max_length=50, unique=True)
    state = models.CharField(
        max_length=15, choices=STATES_CHOICES, default='ACTIVO'
    )
    field = models.CharField(max_length=50, choices=FIELD_CHOICES)

    def __str__(self):
        return self.name


class Position(BaseModel):
    name = models.CharField(max_length=50)
    validity = models.BooleanField(default=True)
    default_role = models.ForeignKey(
        'Role',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Rol por defecto',
        help_text='Rol asignado automáticamente al seleccionar este cargo.',
    )

    def __str__(self):
        return self.name


class Role(BaseModel):
    # Nombres estandarizados según requerimientos SGR (RF-002)
    ADMIN = 'ADMIN'
    COORDINATOR = 'COORDINATOR'
    DELEGATE = 'DELEGATE'
    FUNCTIONARY = 'FUNCTIONARY'
    VERIFIER = 'VERIFIER'
    READONLY = 'READONLY'

    ROLE_CHOICES = [
        (ADMIN, 'Administrador'),
        (COORDINATOR, 'Coordinador del Sistema'),
        (DELEGATE, 'Delegado / Jefatura'),
        (FUNCTIONARY, 'Funcionario Operativo'),
        (VERIFIER, 'Verificador'),
        (READONLY, 'Usuario de Consulta'),
    ]

    role_name = models.CharField(
        max_length=30, unique=True, choices=ROLE_CHOICES
    )

    def __str__(self):
        return self.get_role_name_display()


class Functionary(BaseModel):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='functionary',
        null=True,
        blank=True,
    )
    delegation = models.ForeignKey(Delegation, on_delete=models.PROTECT)
    position = models.ForeignKey(Position, on_delete=models.PROTECT)
    names = models.CharField(max_length=50)
    lastnames = models.CharField(max_length=50)

    @property
    def full_name(self):
        return f'{self.names} {self.lastnames}'

    # --- Helpers de Verificación de Roles para Vistas y Permisos (RBAC) ---
# En personal/models.py, dentro de class Functionary(BaseModel):


    def has_role(self, role_name):
        return self.functionaryrole_set.filter(
            role__role_name__iexact=role_name
        ).exists()


    @property
    def is_admin(self):
        return self.has_role('ADMIN') or self.has_role('Administrador')


    @property
    def is_delegate(self):
        return (
            self.has_role('DELEGATE')
            or self.has_role('Delegado')
            or self.has_role('COORDINATOR')
        )


    @property
    def is_verifier(self):
        return (
            self.has_role('VERIFIER')
            or self.has_role('Verificador')
            or self.is_delegate
            or self.is_admin
        )
            
    @property
    def roles_list(self):
        """Retorna lista con los códigos de roles asignados."""
        return list(
            self.functionaryrole_set.values_list('role__role_name', flat=True)
        )

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)

        # Si es un funcionario nuevo y su cargo tiene un rol por defecto, se le asigna automáticamente
        if is_new and self.position and self.position.default_role:
            FunctionaryRole.objects.get_or_create(
                functionary=self, role=self.position.default_role
            )

    def __str__(self):
        return f'{self.full_name} - {self.position.name}'


class FunctionaryRole(BaseModel):
    functionary = models.ForeignKey(Functionary, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['functionary', 'role'], name='unique_functionary_role'
            )
        ]

    def __str__(self):
        return f'{self.functionary.full_name} -> {self.role}'