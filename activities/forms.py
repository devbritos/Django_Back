from django import forms
from .models import Activity, Evidence


class ActivityForm(forms.ModelForm):
    class Meta:
        model = Activity
        fields = [
            'date',
            'measuring',
            'application',
            'taken_action',
            'quantity',
            'name_contact',
            'telephone_contact',
        ]
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'measuring': forms.Select(attrs={'class': 'form-select'}),
            'application': forms.TextInput(
                attrs={
                    'class': 'form-control', 
                    'placeholder': 'Ej: Atención de vecinos por junta de agua'
                }
            ),
            'taken_action': forms.Textarea(
                attrs={
                    'class': 'form-control', 
                    'rows': 3, 
                    'placeholder': 'Describa brevemente la solución o gestión realizada...'
                }
            ),
            'quantity': forms.NumberInput(
                attrs={
                    'class': 'form-control', 
                    'min': 1,
                    'value': 1
                }
            ),
            'name_contact': forms.TextInput(
                attrs={
                    'class': 'form-control', 
                    'placeholder': 'Nombre del beneficiario o contacto'
                }
            ),
            'telephone_contact': forms.TextInput(
                attrs={
                    'class': 'form-control', 
                    'placeholder': '+56 9 1234 5678'
                }
            ),
        }
        labels = {
            'date': 'Fecha de Registro',
            'measuring': 'Ítem a Medir',
            'application': 'Solicitud / Requerimiento',
            'taken_action': 'Acción Realizada',
            'quantity': 'Cantidad / Personas Atendidas',
            'name_contact': 'Nombre de Contacto',
            'telephone_contact': 'Teléfono de Contacto',
        }
        help_texts = {
            'quantity': 'Indica cuántas personas o atenciones representa este registro (mínimo 1).'
        }

class EvidenceForm(forms.ModelForm):
    class Meta:
        model = Evidence
        fields = ['name', 'file', 'metadata', 'activity', 'functionary']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'file': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'metadata': forms.TextInput(attrs={'class': 'form-control'}),
            'activity': forms.Select(attrs={'class': 'form-select'}),
            'functionary': forms.Select(attrs={'class': 'form-select'}),
        }


class EvidenceValidationForm(forms.ModelForm):
    """Formulario aparte, solo para que el verificador apruebe/rechace."""
    class Meta:
        model = Evidence
        fields = ['validity_state', 'observations_validity']
        widgets = {
            'validity_state': forms.Select(attrs={'class': 'form-select'}),
            'observations_validity': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }