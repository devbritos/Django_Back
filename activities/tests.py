from django.test import TestCase
from datetime import timedelta

from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone

from agenda.models import Commitment
from configuration.models import Goal, Measuring, Period
from personal.models import Delegation, Functionary, FunctionaryRole, Position, Role

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

    def test_evidence_upload_form_uses_spanish_labels_and_guidance(self):
        self.client.force_login(self.owner_user)

        response = self.client.get(reverse('activities:evidence_create'))

        self.assertEqual(response.status_code, 200)
        for label in (
            'Actividad relacionada',
            'Nombre de la evidencia',
            'Autor de la evidencia',
            'Fecha de la evidencia',
            'Archivo de respaldo',
            'Descripción o información adicional',
        ):
            self.assertContains(response, label)
        self.assertContains(response, 'Guardar evidencia')
        self.assertNotContains(response, '>Name<')
        self.assertNotContains(response, '>Author<')

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

    def test_activity_edit_does_not_change_original_activity_date(self):
        original_date = self.activity.date
        changed_date = original_date - timedelta(days=1)

        response = self.client.post(
            reverse('activities:activity_update', args=[self.activity.pk]),
            {
                'date': changed_date.isoformat(),
                'measuring': self.activity.measuring_id,
                'application': 'Solicitud editada',
                'taken_action': 'Acción editada',
                'quantity': self.activity.quantity,
                'name_contact': self.activity.name_contact,
                'telephone_contact': self.activity.telephone_contact,
                'enters_pipe': '',
            },
        )

        self.assertRedirects(response, reverse('activities:activity_list'))
        self.activity.refresh_from_db()
        self.assertEqual(self.activity.date, original_date)


class ActivityValidationAndTrafficLightTests(TestCase):
    def setUp(self):
        today = timezone.localdate()
        self.period = Period.objects.create(
            start_date=today - timedelta(days=10),
            end_date=today + timedelta(days=10),
            computable_days=21,
            status=True,
            version_parameter='1',
            minimum_threshold=0,
            maximum_computable_days=21,
            semaphore='SGR',
        )
        self.position = Position.objects.create(name='Cargo semáforo')
        self.delegation = Delegation.objects.create(
            name='Delegación semáforo',
            field='URBANO',
        )
        self.functionary_user = User.objects.create_user(
            username='responsable_semaforo',
            password='test-password',
        )
        self.functionary = Functionary.objects.create(
            user=self.functionary_user,
            delegation=self.delegation,
            position=self.position,
            names='Responsable',
            lastnames='Semáforo',
        )
        self.measuring = Measuring.objects.create(
            service='Actividad semáforo',
            measurable_item='Atenciones realizadas',
        )
        Goal.objects.create(
            target_value=4,
            weight=100,
            unity='atenciones',
            validity=True,
            position=self.position,
            period=self.period,
            measuring=self.measuring,
        )
        self.activity = Activity.objects.create(
            date=today,
            application='Actividad vinculada a compromiso',
            taken_action='Se realizó la gestión.',
            name_contact='Contacto semáforo',
            telephone_contact='12345678',
            quantity=2,
            functionary=self.functionary,
            measuring=self.measuring,
            state_validity='PENDING',
        )
        self.verifier = User.objects.create_user(
            username='verificador_semaforo',
            password='test-password',
        )
        self.verifier_role = Role.objects.create(role_name=Role.VERIFIER)
        verifier_functionary = Functionary.objects.create(
            user=self.verifier,
            delegation=self.delegation,
            position=self.position,
            names='Verificador',
            lastnames='Semáforo',
        )
        FunctionaryRole.objects.create(
            functionary=verifier_functionary,
            role=self.verifier_role,
        )
        self.admin = User.objects.create_superuser(
            username='admin_semaforo',
            email='admin_semaforo@example.com',
            password='test-password',
        )

    def test_repeated_activity_submission_creates_only_one_record(self):
        self.client.force_login(self.functionary_user)
        initial_count = Activity.objects.count()
        payload = {
            'date': timezone.localdate().isoformat(),
            'measuring': self.measuring.pk,
            'application': 'Solicitud enviada una sola vez',
            'taken_action': 'Gestión realizada',
            'quantity': 1,
            'name_contact': 'Contacto',
            'telephone_contact': '12345678',
            'submission_key': 'b1b14575-57e8-4d0a-8d5c-29b9d4708055',
        }

        first_response = self.client.post(
            reverse('activities:activity_create'),
            payload,
        )
        second_response = self.client.post(
            reverse('activities:activity_create'),
            payload,
        )

        self.assertRedirects(
            first_response,
            reverse('activities:activity_list'),
        )
        self.assertRedirects(
            second_response,
            reverse('activities:activity_list'),
        )
        self.assertEqual(Activity.objects.count(), initial_count + 1)

    def test_activity_advances_semaphore_only_after_validation(self):
        self.client.force_login(self.admin)

        pending_response = self.client.get(
            reverse('activities:traffic_light'),
        )
        self.assertEqual(
            pending_response.context['traffic_light_data'][0][
                'achieved_percentage'
            ],
            0,
        )

        self.client.force_login(self.verifier)
        validation_response = self.client.post(
            reverse('activities:activity_validate', args=[self.activity.pk]),
            {'state_validity': 'VALIDATED'},
        )
        self.assertRedirects(
            validation_response,
            reverse('activities:activity_list'),
        )
        self.activity.refresh_from_db()
        self.assertEqual(self.activity.state_validity, 'VALIDATED')

        self.client.force_login(self.admin)
        progress_response = self.client.get(
            reverse('activities:traffic_light'),
        )
        self.assertEqual(
            progress_response.context['traffic_light_data'][0][
                'achieved_percentage'
            ],
            50,
        )

    def test_functionary_can_view_only_their_own_traffic_light(self):
        self.client.force_login(self.functionary_user)

        response = self.client.get(reverse('activities:traffic_light'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [
                item['functionary'].pk
                for item in response.context['traffic_light_data']
            ],
            [self.functionary.pk],
        )

    def test_traffic_light_warns_when_validated_activity_has_no_matching_goal(self):
        self.activity.state_validity = 'VALIDATED'
        self.activity.save(update_fields=['state_validity'])
        mismatched_position = Position.objects.create(
            name='Cargo sin meta para este ítem',
        )
        self.functionary.position = mismatched_position
        self.functionary.save(update_fields=['position'])
        self.client.force_login(self.admin)

        response = self.client.get(reverse('activities:traffic_light'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['unmatched_validated_activity_count'], 1)
        self.assertContains(
            response,
            'actividad(es) validada(s) no se están contabilizando',
        )
        self.assertFalse(
            response.context['traffic_light_data'][0]['has_active_goals']
        )

    def test_functionary_cannot_validate_their_own_activity(self):
        FunctionaryRole.objects.create(
            functionary=self.functionary,
            role=self.verifier_role,
        )
        self.client.force_login(self.functionary_user)

        response = self.client.get(
            reverse('activities:activity_validate', args=[self.activity.pk]),
        )

        self.assertEqual(response.status_code, 404)

    def test_admin_functionary_can_validate_own_activity(self):
        admin_role = Role.objects.create(role_name=Role.ADMIN)
        FunctionaryRole.objects.create(
            functionary=self.functionary,
            role=admin_role,
        )
        self.client.force_login(self.functionary_user)

        list_response = self.client.get(reverse('activities:activity_list'))
        self.assertContains(
            list_response,
            reverse('activities:activity_validate', args=[self.activity.pk]),
        )

        response = self.client.post(
            reverse('activities:activity_validate', args=[self.activity.pk]),
            {'state_validity': 'VALIDATED'},
        )

        self.assertRedirects(response, reverse('activities:activity_list'))
        self.activity.refresh_from_db()
        self.assertEqual(self.activity.state_validity, 'VALIDATED')

    def test_validation_button_only_appears_on_pending_other_functionarys_activities(self):
        other_user = User.objects.create_user(username='otro_responsable')
        other_functionary = Functionary.objects.create(
            user=other_user,
            delegation=self.delegation,
            position=self.position,
            names='Otro',
            lastnames='Responsable',
        )
        pending_activity = Activity.objects.create(
            date=timezone.localdate(),
            application='Actividad pendiente de otro funcionario',
            taken_action='Acción pendiente.',
            name_contact='Contacto pendiente',
            telephone_contact='12345678',
            functionary=other_functionary,
            measuring=self.measuring,
            state_validity='PENDING',
        )
        validated_activity = Activity.objects.create(
            date=timezone.localdate(),
            application='Actividad ya validada de otro funcionario',
            taken_action='Acción ya validada.',
            name_contact='Contacto validado',
            telephone_contact='12345678',
            functionary=other_functionary,
            measuring=self.measuring,
            state_validity='VALIDATED',
        )
        self.client.force_login(self.verifier)

        response = self.client.get(reverse('activities:activity_list'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            reverse('activities:activity_validate', args=[pending_activity.pk]),
        )
        self.assertNotContains(
            response,
            reverse(
                'activities:activity_validate',
                args=[validated_activity.pk],
            ),
        )

    def test_already_validated_activity_cannot_be_validated_again(self):
        self.activity.state_validity = 'VALIDATED'
        self.activity.save(update_fields=['state_validity'])
        self.client.force_login(self.verifier)

        response = self.client.get(
            reverse('activities:activity_validate', args=[self.activity.pk]),
        )

        self.assertEqual(response.status_code, 404)
