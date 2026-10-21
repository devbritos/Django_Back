from django import forms
from django.contrib.auth.models import User
from .models import Functionary, FunctionaryRole, Role


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
        username = self.cleaned_data.get("username")
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("El nombre de usuario ya está registrado.")
        return username

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
                    FunctionaryRole.objects.create(functionary=functionary, role=role)

        return functionary