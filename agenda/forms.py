from django import forms
from .models import Commitment


class CommitmentForm(forms.ModelForm):
    class Meta:
        model = Commitment
        fields = [
            'origin', 'applic_name', 'territory', 'commitment_date',
            'support', 'state', 'observation', 'functionary', 'measuring',
        ]
        widgets = {
            'origin': forms.TextInput(attrs={'class': 'form-control'}),
            'applic_name': forms.TextInput(attrs={'class': 'form-control'}),
            'territory': forms.TextInput(attrs={'class': 'form-control'}),
            'commitment_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'support': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.Select(attrs={'class': 'form-select'}),
            'observation': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'functionary': forms.Select(attrs={'class': 'form-select'}),
            'measuring': forms.Select(attrs={'class': 'form-select'}),
        }