from django import forms

from .models import Goal, Measuring, Period


class MeasuringForm(forms.ModelForm):
    class Meta:
        model = Measuring
        fields = ['code', 'service', 'measurable_item', 'validity']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'service': forms.TextInput(attrs={'class': 'form-control'}),
            'measurable_item': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 3}
            ),
            'validity': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_code(self):
        code = (self.cleaned_data.get('code') or '').strip()
        if not code:
            raise forms.ValidationError('Debe ingresar el código del ítem.')
        return code

    def clean_service(self):
        service = (self.cleaned_data.get('service') or '').strip()
        if not service:
            raise forms.ValidationError('Debe ingresar el nombre del ítem.')
        return service


class GoalForm(forms.ModelForm):
    class Meta:
        model = Goal
        fields = [
            'position',
            'measuring',
            'period',
            'weight',
            'validity',
            'target_value',
            'unity',
        ]
        widgets = {
            'position': forms.Select(attrs={'class': 'form-select'}),
            'measuring': forms.Select(attrs={'class': 'form-select'}),
            'period': forms.Select(attrs={'class': 'form-select'}),
            'weight': forms.NumberInput(
                attrs={'class': 'form-control', 'min': '0', 'max': '100', 'step': '0.01'}
            ),
            'validity': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'target_value': forms.NumberInput(
                attrs={'class': 'form-control', 'min': '0.01', 'step': '0.01'}
            ),
            'unity': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'Ej: atenciones'}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['position'].queryset = self.fields['position'].queryset.filter(
            validity=True,
            deleted_at__isnull=True,
        )
        active_measuring = Measuring.objects.filter(
            validity=True,
            deleted_at__isnull=True,
        )
        if self.instance.pk:
            active_measuring = active_measuring | Measuring.objects.filter(
                pk=self.instance.measuring_id
            )
        self.fields['measuring'].queryset = active_measuring.distinct()
        self.fields['period'].queryset = self.fields['period'].queryset.filter(
            deleted_at__isnull=True,
        )

    def clean_weight(self):
        weight = self.cleaned_data.get('weight')
        if weight is None or weight < 0 or weight > 100:
            raise forms.ValidationError('El ponderador debe estar entre 0 y 100%.')
        return weight

    def clean_target_value(self):
        target = self.cleaned_data.get('target_value')
        if target is None or target <= 0:
            raise forms.ValidationError('La meta debe ser mayor que 0.')
        return target

    def clean_unity(self):
        unity = (self.cleaned_data.get('unity') or '').strip()
        if not unity:
            raise forms.ValidationError('Debe indicar la unidad de medida.')
        return unity


class PeriodForm(forms.ModelForm):
    class Meta:
        model = Period
        fields = [
            'start_date',
            'end_date',
            'status',
            'minimum_threshold',
            'maximum_computable_days',
            'version_parameter',
            'semaphore',
        ]
        widgets = {
            'start_date': forms.DateInput(
                attrs={'type': 'date', 'class': 'form-control'}
            ),
            'end_date': forms.DateInput(
                attrs={'type': 'date', 'class': 'form-control'}
            ),
            'status': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'minimum_threshold': forms.NumberInput(
                attrs={'class': 'form-control', 'min': 0}
            ),
            'maximum_computable_days': forms.NumberInput(
                attrs={'class': 'form-control', 'min': 1}
            ),
            'version_parameter': forms.TextInput(attrs={'class': 'form-control'}),
            'semaphore': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        maximum_days = cleaned_data.get('maximum_computable_days')
        minimum_threshold = cleaned_data.get('minimum_threshold')

        if minimum_threshold is not None and minimum_threshold < 0:
            self.add_error(
                'minimum_threshold',
                'El umbral mínimo no puede ser negativo.',
            )
        if maximum_days is not None and maximum_days < 1:
            self.add_error(
                'maximum_computable_days',
                'Debe permitir al menos un día computable.',
            )

        if start_date and end_date and end_date < start_date:
            self.add_error('end_date', 'La fecha de término no puede ser anterior a la de inicio.')
        elif start_date and end_date and maximum_days is not None:
            period_days = (end_date - start_date).days + 1
            if maximum_days > period_days:
                self.add_error(
                    'maximum_computable_days',
                    'Los días computables no pueden superar la duración del período.',
                )

        return cleaned_data

    def clean_version_parameter(self):
        value = (self.cleaned_data.get('version_parameter') or '').strip()
        if not value:
            raise forms.ValidationError('Debe indicar la versión del parámetro.')
        return value

    def clean_semaphore(self):
        value = (self.cleaned_data.get('semaphore') or '').strip()
        if not value:
            raise forms.ValidationError('Debe indicar el parámetro del semáforo.')
        return value

    def save(self, commit=True):
        period = super().save(commit=False)
        period.computable_days = (period.end_date - period.start_date).days + 1
        if commit:
            period.save()
            self.save_m2m()
        return period
