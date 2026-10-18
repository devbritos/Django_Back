from django import forms
from .models import Activity, Evidence


class ActivityForm(forms.ModelForm):
    class Meta:
        model = Activity
        fields = [
            'date', 'application', 'taken_action',
            'name_contact', 'telephone_contact',
            'functionary', 'measuring', 'commitment',
        ]
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'application': forms.TextInput(attrs={'class': 'form-control'}),
            'taken_action': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'name_contact': forms.TextInput(attrs={'class': 'form-control'}),
            'telephone_contact': forms.TextInput(attrs={'class': 'form-control'}),
            'functionary': forms.Select(attrs={'class': 'form-select'}),
            'measuring': forms.Select(attrs={'class': 'form-select'}),
            'commitment': forms.Select(attrs={'class': 'form-select'}),
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