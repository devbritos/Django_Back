from django import forms
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db import models
from .models import (
    Delegation,
    Functionary,
    FunctionaryRole,
    Position,
    Role,
)


class DelegationForm(forms.ModelForm):
    class Meta:
        model = Delegation
        fields = ['code', 'name', 'address', 'commune', 'state', 'field']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.TextInput(attrs={'class': 'form-control'}),
            'commune': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.Select(attrs={'class': 'form-select'}),
            'field': forms.Select(attrs={'class': 'form-select'}),
        }

    def clean_name(self):
        name = (self.cleaned_data.get('name') or '').strip()
        if not name:
            raise forms.ValidationError('Debe ingresar el nombre de la delegación.')
        return name

    def clean_code(self):
        code = (self.cleaned_data.get('code') or '').strip()
        if not code:
            raise forms.ValidationError('Debe ingresar el código de la delegación.')
        return code

    def clean_address(self):
        address = (self.cleaned_data.get('address') or '').strip()
        if not address:
            raise forms.ValidationError('Debe ingresar la dirección de la delegación.')
        return address

    def clean_commune(self):
        commune = (self.cleaned_data.get('commune') or '').strip()
        if not commune:
            raise forms.ValidationError('Debe ingresar la comuna de la delegación.')
        return commune


class PositionForm(forms.ModelForm):
    class Meta:
        model = Position
        fields = ['name', 'validity', 'default_role']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'validity': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'default_role': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['default_role'].queryset = Role.objects.filter(
            is_active=True,
            deleted_at__isnull=True,
        )

    def clean_name(self):
        name = (self.cleaned_data.get('name') or '').strip()
        if not name:
            raise forms.ValidationError('Debe ingresar el nombre del cargo.')
        return name


class RoleForm(forms.ModelForm):
    class Meta:
        model = Role
        fields = [
            'role_name',
            'description',
            'permissions',
            'authorized_scope',
            'is_active',
        ]
        widgets = {
            'role_name': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'permissions': forms.SelectMultiple(attrs={'class': 'form-select', 'size': 10}),
            'authorized_scope': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk and self.instance.role_name not in dict(
            self.fields['role_name'].choices
        ):
            self.fields['role_name'].choices = [
                *self.fields['role_name'].choices,
                (self.instance.role_name, self.instance.role_name),
            ]
        self.fields['permissions'].queryset = self.fields[
            'permissions'
        ].queryset.select_related('content_type').order_by(
            'content_type__app_label',
            'codename',
        )


class FunctionaryUpdateForm(forms.ModelForm):
    email = forms.EmailField(
        required=False,
        label='Correo electrónico',
        widget=forms.EmailInput(attrs={'class': 'form-control'}),
    )
    roles = forms.ModelMultipleChoiceField(
        queryset=Role.objects.all(),
        required=False,
        label='Roles asignados',
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
    )

    class Meta:
        model = Functionary
        fields = ['names', 'lastnames', 'delegation', 'position', 'is_active']
        widgets = {
            'names': forms.TextInput(attrs={'class': 'form-control'}),
            'lastnames': forms.TextInput(attrs={'class': 'form-control'}),
            'delegation': forms.Select(attrs={'class': 'form-select'}),
            'position': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        delegations = Delegation.objects.filter(
            state='ACTIVO',
            deleted_at__isnull=True,
        )
        positions = Position.objects.filter(validity=True, deleted_at__isnull=True)
        if self.instance.pk:
            delegations = Delegation.objects.filter(
                models.Q(state='ACTIVO') | models.Q(pk=self.instance.delegation_id)
            )
            positions = Position.objects.filter(
                models.Q(validity=True) | models.Q(pk=self.instance.position_id)
            )
        self.fields['delegation'].queryset = delegations
        self.fields['position'].queryset = positions
        self.fields['roles'].queryset = Role.objects.filter(
            is_active=True,
            deleted_at__isnull=True,
        )
        if self.instance.pk:
            self.fields['roles'].initial = Role.objects.filter(
                functionaryrole__functionary=self.instance,
                is_active=True,
            )
            if self.instance.user:
                self.fields['email'].initial = self.instance.user.email

    def clean_names(self):
        names = (self.cleaned_data.get('names') or '').strip()
        if not names:
            raise forms.ValidationError('Debe ingresar los nombres del funcionario.')
        return names

    def clean_lastnames(self):
        lastnames = (self.cleaned_data.get('lastnames') or '').strip()
        if not lastnames:
            raise forms.ValidationError('Debe ingresar los apellidos del funcionario.')
        return lastnames

    def clean_email(self):
        email = (self.cleaned_data.get('email') or '').strip()
        if self.instance.user and not email:
            raise forms.ValidationError('Debe ingresar el correo electrónico.')
        if email and User.objects.filter(email__iexact=email).exclude(
            pk=getattr(self.instance.user, 'pk', None)
        ).exists():
            raise forms.ValidationError(
                'Este correo ya está asociado a otra cuenta.'
            )
        return email

    @transaction.atomic
    def save(self, commit=True):
        if self.cleaned_data.get('is_active'):
            self.instance.deleted_at = None
        functionary = super().save(commit=commit)
        if commit:
            selected_roles = self.cleaned_data.get('roles')
            FunctionaryRole.objects.filter(functionary=functionary).exclude(
                role__in=selected_roles
            ).delete()
            for role in selected_roles:
                FunctionaryRole.objects.get_or_create(
                    functionary=functionary,
                    role=role,
                )
            if functionary.user:
                functionary.user.email = self.cleaned_data.get('email', '')
                functionary.user.is_active = functionary.is_active
                functionary.user.first_name = functionary.names
                functionary.user.last_name = functionary.lastnames
                functionary.user.save(
                    update_fields=[
                        'email',
                        'is_active',
                        'first_name',
                        'last_name',
                    ]
                )
        return functionary


class FunctionaryRoleForm(forms.ModelForm):
    class Meta:
        model = FunctionaryRole
        fields = ['functionary', 'role']
        widgets = {
            'functionary': forms.Select(attrs={'class': 'form-select'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['functionary'].queryset = Functionary.objects.filter(
            is_active=True,
            deleted_at__isnull=True,
        )
        self.fields['role'].queryset = Role.objects.filter(
            is_active=True,
            deleted_at__isnull=True,
        )

    def clean(self):
        cleaned_data = super().clean()
        functionary = cleaned_data.get('functionary')
        role = cleaned_data.get('role')
        if (
            functionary
            and role
            and FunctionaryRole.objects.filter(
                functionary=functionary,
                role=role,
            ).exclude(pk=self.instance.pk).exists()
        ):
            self.add_error('role', 'Este funcionario ya tiene asignado ese rol.')
        return cleaned_data


class FunctionaryCustomForm(forms.ModelForm):
    # Campos para la cuenta de acceso Django
    username = forms.CharField(
        max_length=150,
        label="Nombre de Usuario",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Ej: jperez"})
    )
    email = forms.EmailField(
        label="Correo Electrónico",
        widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "ejemplo@laserena.cl"})
    )
    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "••••••••"})
    )

    # Selección múltiple de roles
    roles = forms.ModelMultipleChoiceField(
        queryset=Role.objects.all(),
        widget=forms.CheckboxSelectMultiple(attrs={"class": "form-check-input"}),
        required=False,
        label="Roles Asignados"
    )

    class Meta:
        model = Functionary
        fields = ["names", "lastnames", "delegation", "position"]
        widgets = {
            "names": forms.TextInput(attrs={"class": "form-control"}),
            "lastnames": forms.TextInput(attrs={"class": "form-control"}),
            "delegation": forms.Select(attrs={"class": "form-select"}),
            "position": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['delegation'].queryset = Delegation.objects.filter(
            state='ACTIVO',
            deleted_at__isnull=True,
        )
        self.fields['position'].queryset = Position.objects.filter(
            validity=True,
            deleted_at__isnull=True,
        )
        self.fields['roles'].queryset = Role.objects.filter(
            is_active=True,
            deleted_at__isnull=True,
        )

    def clean_username(self):
        username = (self.cleaned_data.get("username") or "").strip()
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("El nombre de usuario ya está registrado.")
        return username

    def clean_names(self):
        names = (self.cleaned_data.get("names") or "").strip()
        if not names:
            raise forms.ValidationError("Debe ingresar los nombres del funcionario.")
        return names

    def clean_lastnames(self):
        lastnames = (self.cleaned_data.get("lastnames") or "").strip()
        if not lastnames:
            raise forms.ValidationError("Debe ingresar los apellidos del funcionario.")
        return lastnames

    def clean_password(self):
        password = self.cleaned_data.get("password")
        try:
            validate_password(password)
        except ValidationError as error:
            raise forms.ValidationError(error.messages) from error
        return password

    def clean_email(self):
        email = (self.cleaned_data.get('email') or '').strip()
        if not email:
            raise forms.ValidationError("Debe ingresar un correo electrónico.")
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Este correo ya está registrado.")
        return email

    @transaction.atomic
    def save(self, commit=True):
        # 1. Crear el usuario en auth_user
        user = User.objects.create_user(
            username=self.cleaned_data["username"],
            email=self.cleaned_data["email"],
            password=self.cleaned_data["password"],
            first_name=self.cleaned_data["names"],
            last_name=self.cleaned_data["lastnames"],
        )

        # 2. Asociar al modelo Functionary
        functionary = super().save(commit=False)
        functionary.user = user

        if commit:
            functionary.save()
            # 3. Guardar las relaciones en FunctionaryRole
            selected_roles = self.cleaned_data.get("roles")
            if selected_roles:
                for role in selected_roles:
                    FunctionaryRole.objects.get_or_create(
                        functionary=functionary,
                        role=role,
                    )

        return functionary