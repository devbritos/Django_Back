from django import forms
from .models import Commitment

class CommitmentForm(forms.ModelForm):
    # Campo oculto opcional para vincular la actividad de origen (RF-07)
    activity_id = forms.IntegerField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = Commitment
        fields = [
            'origin', 'applic_name', 'territory', 'commitment_date',
            'support', 'state', 'observation', 'measuring',
        ]
        widgets = {
            'origin': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Ej: Dirigente junta de vecinos, Concejo, etc.'
            }),
            'applic_name': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Nombre de la persona o entidad solicitante'
            }),
            'territory': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Ej: Sector Las Compañías, Cuadrante 2'
            }),
            'commitment_date': forms.DateInput(attrs={
                'type': 'date', 
                'class': 'form-control'
            }),
            'support': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Ej: Oficio N° 102 / Correo'
            }),
            'state': forms.Select(attrs={
                'class': 'form-select'
            }),
            'observation': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3, 
                'placeholder': 'Detalle del compromiso y acuerdos alcanzados...'
            }),
            'measuring': forms.Select(attrs={
                'class': 'form-select'
            }),
        }
        labels = {
            'origin': 'Origen de la Solicitud',
            'applic_name': 'Nombre del Solicitante',
            'territory': 'Territorio / Sector',
            'commitment_date': 'Fecha Límite de Cumplimiento',
            'support': 'Respaldo / Medio',
            'state': 'Estado del Compromiso',
            'observation': 'Observación / Compromiso Adquirido',
            'measuring': 'Ítem a Medir Asociado',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Si es una creación nueva, establecer estado inicial por defecto
        if not self.instance.pk and 'state' in self.fields:
            self.fields['state'].initial = 'JOINED'