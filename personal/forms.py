from django import forms
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
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
        fields = ['name', 'state', 'field']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.Select(attrs={'class': 'form-select'}),
            'field': forms.Select(attrs={'class': 'form-select'}),
        }

    def clean_name(self):
        name = (self.cleaned_data.get('name') or '').strip()
        if not name:
            raise forms.ValidationError('Debe ingresar el nombre de la delegación.')
        return name


class PositionForm(forms.ModelForm):
    class Meta:
        model = Position
        fields = ['name', 'validity', 'default_role']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'validity': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'default_role': forms.Select(attrs={'class': 'form-select'}),
        }

    def clean_name(self):
        name = (self.cleaned_data.get('name') or '').strip()
        if not name:
            raise forms.ValidationError('Debe ingresar el nombre del cargo.')
        return name


class RoleForm(forms.ModelForm):
    class Meta:
        model = Role
        fields = ['role_name']
        widgets = {'role_name': forms.Select(attrs={'class': 'form-select'})}


class FunctionaryUpdateForm(forms.ModelForm):
    class Meta:
        model = Functionary
        fields = ['names', 'lastnames', 'delegation', 'position']
        widgets = {
            'names': forms.TextInput(attrs={'class': 'form-control'}),
            'lastnames': forms.TextInput(attrs={'class': 'form-control'}),
            'delegation': forms.Select(attrs={'class': 'form-select'}),
            'position': forms.Select(attrs={'class': 'form-select'}),
        }

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


class FunctionaryRoleForm(forms.ModelForm):
    class Meta:
        model = FunctionaryRole
        fields = ['functionary', 'role']
        widgets = {
            'functionary': forms.Select(attrs={'class': 'form-select'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
        }

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
        return email

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