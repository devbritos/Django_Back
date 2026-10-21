from django.test import TestCase
from django.core.exceptions import ValidationError

from .forms import FunctionaryCustomForm, FunctionaryUpdateForm
from .models import Delegation, Functionary, Position


class FunctionaryNameValidationTests(TestCase):
    def setUp(self):
        self.delegation = Delegation.objects.create(
            name='Validación de nombres',
            field='URBANO',
        )
        self.position = Position.objects.create(name='Cargo de prueba')
        self.functionary = Functionary.objects.create(
            names='María José',
            lastnames='Pérez Soto',
            delegation=self.delegation,
            position=self.position,
        )

    def _create_form_data(self, **overrides):
        data = {
            'names': 'María José',
            'lastnames': 'Pérez Soto',
            'delegation': str(self.delegation.pk),
            'position': str(self.position.pk),
            'username': 'usuario_prueba',
            'email': 'usuario@example.com',
            'password': 'Safe-Test-Password-742!',
        }
        data.update(overrides)
        return data

    def _update_form_data(self, **overrides):
        data = {
            'names': 'María José',
            'lastnames': 'Pérez Soto',
            'delegation': str(self.delegation.pk),
            'position': str(self.position.pk),
        }
        data.update(overrides)
        return data

    def test_create_form_rejects_digits_in_names_and_lastnames(self):
        for field, value in (
            ('names', 'María2'),
            ('lastnames', 'Pérez2'),
        ):
            with self.subTest(field=field):
                form = FunctionaryCustomForm(
                    data=self._create_form_data(**{field: value})
                )
                self.assertFalse(form.is_valid())
                self.assertIn('no deben contener números', str(form.errors[field]))

    def test_update_form_rejects_digits_in_names_and_lastnames(self):
        for field, value in (
            ('names', 'María2'),
            ('lastnames', 'Pérez2'),
        ):
            with self.subTest(field=field):
                form = FunctionaryUpdateForm(
                    data=self._update_form_data(**{field: value}),
                    instance=self.functionary,
                )
                self.assertFalse(form.is_valid())
                self.assertIn('no deben contener números', str(form.errors[field]))

    def test_model_validation_rejects_digits_in_names_and_lastnames(self):
        for field, value in (
            ('names', 'María2'),
            ('lastnames', 'Pérez2'),
        ):
            with self.subTest(field=field):
                functionary = Functionary(
                    names='María José',
                    lastnames='Pérez Soto',
                    delegation=self.delegation,
                    position=self.position,
                )
                setattr(functionary, field, value)
                with self.assertRaises(ValidationError):
                    functionary.full_clean()

    def test_create_and_update_forms_accept_accents_and_hyphens(self):
        names = 'María-José'
        lastnames = 'Pérez-Soto'
        create_form = FunctionaryCustomForm(
            data=self._create_form_data(names=names, lastnames=lastnames)
        )
        update_form = FunctionaryUpdateForm(
            data=self._update_form_data(names=names, lastnames=lastnames),
            instance=self.functionary,
        )

        self.assertTrue(create_form.is_valid(), create_form.errors)
        self.assertTrue(update_form.is_valid(), update_form.errors)
