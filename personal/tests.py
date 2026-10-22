from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth.models import Permission, User
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse

from .forms import FunctionaryCustomForm, FunctionaryUpdateForm
from .models import (
    Delegation,
    Functionary,
    FunctionaryRole,
    Position,
    Role,
)


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


class FunctionaryRolePermissionTests(TestCase):
    def test_active_role_grants_its_configured_django_permissions(self):
        user = User.objects.create_user(username='usuario_rbac')
        delegation = Delegation.objects.create(name='Delegación RBAC', field='URBANO')
        position = Position.objects.create(name='Cargo RBAC')
        functionary = Functionary.objects.create(
            user=user,
            delegation=delegation,
            position=position,
            names='Usuario',
            lastnames='RBAC',
        )
        role = Role.objects.create(
            role_name=Role.READONLY,
            authorized_scope='DELEGATION',
        )
        permission = Permission.objects.get(
            content_type__app_label='activities',
            codename='view_activity',
        )
        role.permissions.add(permission)
        FunctionaryRole.objects.create(functionary=functionary, role=role)

        self.assertTrue(user.has_perm('activities.view_activity'))

        role.is_active = False
        role.save(update_fields=['is_active'])
        user = User.objects.get(pk=user.pk)
        self.assertFalse(user.has_perm('activities.view_activity'))


class RoleCatalogTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            username='admin_roles',
            email='admin_roles@example.com',
            password='test-password',
        )
        self.client.force_login(self.admin)

    def test_admin_can_create_update_and_deactivate_roles(self):
        response = self.client.get(reverse('personal:role_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse('personal:role_create'))
        self.assertContains(response, 'Roles y permisos')

        response = self.client.post(
            reverse('personal:role_create'),
            {
                'role_name': Role.READONLY,
                'description': 'Acceso de consulta',
                'authorized_scope': 'DELEGATION',
                'is_active': 'on',
            },
        )
        self.assertRedirects(response, reverse('personal:role_list'))
        role = Role.objects.get(role_name=Role.READONLY)
        self.assertEqual(role.description, 'Acceso de consulta')

        response = self.client.post(
            reverse('personal:role_update', args=[role.pk]),
            {
                'role_name': Role.READONLY,
                'description': 'Consulta de la delegación asignada',
                'authorized_scope': 'GLOBAL',
                'is_active': 'on',
            },
        )
        self.assertRedirects(response, reverse('personal:role_list'))
        role.refresh_from_db()
        self.assertEqual(
            role.description,
            'Consulta de la delegación asignada',
        )
        self.assertEqual(role.authorized_scope, 'GLOBAL')

        response = self.client.post(
            reverse('personal:role_delete', args=[role.pk]),
        )
        self.assertRedirects(response, reverse('personal:role_list'))
        role.refresh_from_db()
        self.assertFalse(role.is_active)

    def test_role_edit_form_preselects_current_role_and_permissions(self):
        role = Role.objects.create(
            role_name=Role.READONLY,
            description='Solo consulta',
            authorized_scope='DELEGATION',
        )
        permission = Permission.objects.get(
            content_type__app_label='activities',
            codename='view_activity',
        )
        role.permissions.add(permission)

        response = self.client.get(
            reverse('personal:role_update', args=[role.pk]),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context['form']['role_name'].value(),
            Role.READONLY,
        )
        self.assertEqual(
            response.context['form']['authorized_scope'].value(),
            'DELEGATION',
        )
        self.assertEqual(
            response.context['form']['permissions'].value(),
            [permission.pk],
        )
        self.assertRegex(
            response.content.decode(),
            r'<option value="READONLY" selected>',
        )

    def test_role_edit_keeps_legacy_role_selected(self):
        role = Role.objects.create(role_name='Administrador')

        response = self.client.get(
            reverse('personal:role_update', args=[role.pk]),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context['form']['role_name'].value(),
            'Administrador',
        )
        self.assertRegex(
            response.content.decode(),
            r'<option value="Administrador" selected>',
        )
