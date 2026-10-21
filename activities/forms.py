import re
from django import forms
from django.utils import timezone
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
            'enters_pipe',
        ]
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control', 'required': True}),
            'measuring': forms.Select(attrs={'class': 'form-select', 'required': True}),
            'application': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Ej: Atención de vecinos por junta de agua',
                    'required': True,
                }
            ),
            'taken_action': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 3,
                    'placeholder': 'Describa brevemente la solución o gestión realizada...',
                    'required': True,
                }
            ),
            'quantity': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'min': 1,
                    'value': 1,
                    'required': True,
                }
            ),
            'name_contact': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Nombre del beneficiario o contacto',
                    'required': True,
                }
            ),
            'telephone_contact': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': '+56 9 1234 5678',
                    'required': True,
                }
            ),
            'enters_pipe': forms.CheckboxInput(
                attrs={'class': 'form-check-input'}
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
            'enters_pipe': '¿Ingresa al Tubo de Trabajo?',
        }
        help_texts = {
            'quantity': 'Indica cuántas personas o atenciones representa este registro (mínimo 1).'
        }

    def clean_application(self):
        application = (self.cleaned_data.get('application') or '').strip()
        if not application:
            raise forms.ValidationError('Debe describir la solicitud o requerimiento.')
        return application

    def clean_taken_action(self):
        taken_action = (self.cleaned_data.get('taken_action') or '').strip()
        if not taken_action:
            raise forms.ValidationError('Debe indicar la acción realizada.')
        return taken_action

    def clean_name_contact(self):
        name = (self.cleaned_data.get('name_contact') or '').strip()
        if not name:
            raise forms.ValidationError('Debe ingresar el nombre de contacto.')
        return name

    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        if quantity is None or quantity < 1:
            raise forms.ValidationError('La cantidad debe ser mayor o igual a 1.')
        return quantity

    def clean_telephone_contact(self):
        telephone = (self.cleaned_data.get('telephone_contact') or '').strip()
        if not telephone:
            raise forms.ValidationError('Debe ingresar un teléfono de contacto.')
        if not re.fullmatch(r'^[+0-9()\s-]{8,20}$', telephone):
            raise forms.ValidationError('El teléfono no tiene un formato válido.')
        return telephone

    def clean_date(self):
        date_value = self.cleaned_data.get('date')
        if date_value and date_value > timezone.localdate():
            raise forms.ValidationError('La fecha no puede ser futura.')
        return date_value


class EvidenceForm(forms.ModelForm):
    class Meta:
        model = Evidence
        fields = [
            'name',
            'author',
            'date_evidence',
            'file',
            'metadata',
            'activity',
            'functionary',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'author': forms.TextInput(attrs={'class': 'form-control'}),
            'date_evidence': forms.DateInput(
                attrs={'type': 'date', 'class': 'form-control'}
            ),
            'file': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'metadata': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'activity': forms.Select(attrs={'class': 'form-select'}),
            'functionary': forms.Select(attrs={'class': 'form-select'}),
        }

    def clean_name(self):
        name = (self.cleaned_data.get('name') or '').strip()
        if not name:
            raise forms.ValidationError('Debe ingresar el nombre de la evidencia.')
        return name

    def clean_author(self):
        author = (self.cleaned_data.get('author') or '').strip()
        if not author:
            raise forms.ValidationError('Debe ingresar el autor de la evidencia.')
        return author

    def clean_date_evidence(self):
        evidence_date = self.cleaned_data.get('date_evidence')
        if evidence_date and evidence_date > timezone.localdate():
            raise forms.ValidationError('La fecha de la evidencia no puede ser futura.')
        return evidence_date

    def clean_metadata(self):
        metadata = (self.cleaned_data.get('metadata') or '').strip()
        if not metadata:
            raise forms.ValidationError('Debe ingresar información adicional de la evidencia.')
        return metadata


class EvidenceValidationForm(forms.ModelForm):
    """Formulario aparte, solo para que el verificador apruebe/rechace."""
    class Meta:
        model = Evidence
        fields = ['validity_state', 'observations_validity']
        widgets = {
            'validity_state': forms.Select(attrs={'class': 'form-select'}),
            'observations_validity': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def clean(self):
        cleaned_data = super().clean()
        if (
            cleaned_data.get('validity_state') == Evidence.Validity.REJECTED
            and not (cleaned_data.get('observations_validity') or '').strip()
        ):
            self.add_error(
                'observations_validity',
                'Debe indicar el motivo cuando rechaza una evidencia.',
            )
        return cleaned_data