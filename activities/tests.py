from django.test import TestCase
from datetime import timedelta

from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone

from agenda.models import Commitment
from configuration.models import Measuring
from personal.models import Delegation, Functionary, Position

from .models import Activity, Evidence


class StaffEvidenceAccessTests(TestCase):
    def setUp(self):
        self.staff_user = User.objects.create_user(
            username='sgr_admin',
            password='test-password',
            is_staff=True,
        )
        self.owner_user = User.objects.create_user(
            username='functionary_user',
            password='test-password',
        )
        delegation = Delegation.objects.create(name='Delegación de prueba', field='URBANO')
        position = Position.objects.create(name='Cargo de prueba')
        self.functionary = Functionary.objects.create(
            user=self.owner_user,
            delegation=delegation,
            position=position,
            names='Funcionario',
            lastnames='Prueba',
        )
        measuring = Measuring.objects.create(
            service='Servicio de prueba',
            measurable_item='Atenciones',
        )
        self.activity = Activity.objects.create(
            date=timezone.localdate(),
            application='Solicitud de prueba de otro usuario',
            taken_action='Acción realizada',
            name_contact='Contacto de prueba',
            telephone_contact='12345678',
            functionary=self.functionary,
            measuring=measuring,
        )
        self.evidence = Evidence.objects.create(
            name='Evidencia de prueba',
            author='Funcionario de prueba',
            date_evidence=timezone.localdate(),
            metadata='Detalle de prueba',
            file='evidences/test.pdf',
            activity=self.activity,
            functionary=self.functionary,
        )
        self.commitment = Commitment.objects.create(
            origin='Solicitud de prueba',
            applic_name='Solicitante de prueba',
            territory='Sector de prueba',
            commitment_date=timezone.localdate() + timedelta(days=5),
            functionary=self.functionary,
        )
        self.client.force_login(self.staff_user)

    def test_staff_can_view_other_users_activities_and_evidences(self):
        activities_response = self.client.get(reverse('activities:activity_list'))
        evidences_response = self.client.get(reverse('activities:evidence_list'))
        activity_edit_response = self.client.get(
            reverse('activities:activity_update', args=[self.activity.pk])
        )

        self.assertEqual(activities_response.status_code, 200)
        self.assertContains(activities_response, self.activity.application)
        self.assertContains(activities_response, 'Actividades')
        self.assertContains(activities_response, 'Tubo de Trabajo')
        self.assertContains(activities_response, 'Evidencias')
        self.assertEqual(activity_edit_response.status_code, 200)
        self.assertEqual(evidences_response.status_code, 200)
        self.assertContains(evidences_response, self.evidence.name)
        self.assertContains(evidences_response, 'Validar')

    def test_staff_can_approve_other_users_evidence(self):
        response = self.client.post(
            reverse('activities:evidence_validate', args=[self.evidence.pk]),
            {
                'validity_state': Evidence.Validity.APPROVED,
                'observations_validity': '',
            },
        )

        self.assertRedirects(response, reverse('activities:evidence_list'))
        self.evidence.refresh_from_db()
        self.assertEqual(self.evidence.validity_state, Evidence.Validity.APPROVED)
        self.assertEqual(self.evidence.date_validity, timezone.localdate())

    def test_staff_can_view_and_edit_other_users_commitments(self):
        list_response = self.client.get(reverse('agenda:commitment_list'))
        edit_response = self.client.get(
            reverse('agenda:commitment_update', args=[self.commitment.pk])
        )

        self.assertEqual(list_response.status_code, 200)
        self.assertContains(list_response, self.commitment.origin)
        self.assertEqual(edit_response.status_code, 200)
