from django.test import TestCase

from datetime import timedelta

from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone

from activities.models import Activity
from configuration.models import Measuring
from personal.models import Delegation, Functionary, Position

from .models import Commitment


class CommitmentActivityLinkTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='funcionario_compromiso',
            password='test-password',
        )
        delegation = Delegation.objects.create(
            name='Delegación compromiso',
            field='URBANO',
        )
        position = Position.objects.create(name='Cargo compromiso')
        self.functionary = Functionary.objects.create(
            user=self.user,
            delegation=delegation,
            position=position,
            names='Funcionario',
            lastnames='Compromiso',
        )
        self.measuring = Measuring.objects.create(
            service='Ítem del compromiso',
            measurable_item='Actividad asociada',
        )
        self.activity = Activity.objects.create(
            date=timezone.localdate(),
            application='Solicitud de origen',
            taken_action='Acción realizada',
            name_contact='Vecino solicitante',
            telephone_contact='12345678',
            functionary=self.functionary,
            measuring=self.measuring,
            enters_pipe=True,
        )
        self.client.force_login(self.user)

    def _commitment_data(self, **overrides):
        data = {
            'origin': 'Solicitud de origen',
            'applic_name': 'Vecino solicitante',
            'territory': 'Sector de prueba',
            'commitment_date': (
                timezone.localdate() + timedelta(days=10)
            ).isoformat(),
            'support': '',
            'state': Commitment.State.JOINED,
            'observation': 'Compromiso asociado a actividad.',
            'activity_id': str(self.activity.pk),
        }
        data.update(overrides)
        return data

    def test_commitment_created_from_activity_links_it_and_uses_its_measuring(self):
        create_url = reverse('agenda:commitment_create')
        response = self.client.get(
            create_url,
            {'activity_id': self.activity.pk},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context['form']['measuring'].value(),
            self.measuring.pk,
        )

        response = self.client.post(
            create_url,
            self._commitment_data(),
        )

        self.assertRedirects(response, reverse('agenda:commitment_list'))
        commitment = Commitment.objects.get()
        self.activity.refresh_from_db()
        self.assertEqual(self.activity.commitment, commitment)
        self.assertEqual(commitment.measuring, self.measuring)

    def test_cannot_link_another_functionarys_activity(self):
        other_user = User.objects.create_user(username='otro_funcionario')
        other_functionary = Functionary.objects.create(
            user=other_user,
            delegation=self.functionary.delegation,
            position=self.functionary.position,
            names='Otro',
            lastnames='Funcionario',
        )
        other_activity = Activity.objects.create(
            date=timezone.localdate(),
            application='Actividad ajena',
            taken_action='Acción ajena',
            name_contact='Contacto ajeno',
            telephone_contact='12345678',
            functionary=other_functionary,
            measuring=self.measuring,
            enters_pipe=True,
        )

        response = self.client.post(
            reverse('agenda:commitment_create'),
            self._commitment_data(activity_id=str(other_activity.pk)),
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Commitment.objects.exists())
        self.assertIn('__all__', response.context['form'].errors)
