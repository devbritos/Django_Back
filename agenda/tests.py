from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from personal.models import Delegation, Functionary, Position

from .models import Commitment


class CommitmentDelegationScopeTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        user_model = get_user_model()
        cls.user = user_model.objects.create_user(
            username="commitment-scope-user",
            password="test-password",
        )
        cls.admin = user_model.objects.create_superuser(
            username="commitment-scope-admin",
            email="commitment-admin@example.com",
            password="test-password",
        )
        first_delegation = Delegation.objects.create(
            name="Compromisos Uno", state="ACTIVO", field="URBANO"
        )
        cls.second_delegation = Delegation.objects.create(
            name="Compromisos Dos", state="ACTIVO", field="RURAL"
        )
        position = Position.objects.create(name="Inspector", validity=True)
        first_functionary = Functionary.objects.create(
            user=cls.user,
            names="Funcionario",
            lastnames="Uno",
            delegation=first_delegation,
            position=position,
        )
        second_functionary = Functionary.objects.create(
            names="Funcionario",
            lastnames="Dos",
            delegation=cls.second_delegation,
            position=position,
        )
        Commitment.objects.create(
            origin="Origen",
            applic_name="Compromiso propio",
            territory="Territorio",
            commitment_date=date(2026, 10, 21),
            functionary=first_functionary,
        )
        Commitment.objects.create(
            origin="Origen",
            applic_name="Compromiso ajeno",
            territory="Territorio",
            commitment_date=date(2026, 10, 21),
            functionary=second_functionary,
        )

    def test_commitment_list_only_shows_the_users_delegation(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("agenda:commitment_list"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["commitments"]), 1)
        self.assertEqual(
            response.context["commitments"][0].applic_name,
            "Compromiso propio",
        )
        self.assertContains(response, "data-modal-form")
        self.assertContains(response, "data-swal-confirm")

    def test_staff_selection_filters_commitment_list(self):
        self.client.force_login(self.admin)
        session = self.client.session
        session["selected_delegation_id"] = self.second_delegation.pk
        session.save()

        response = self.client.get(reverse("agenda:commitment_list"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["commitments"]), 1)
        self.assertEqual(
            response.context["commitments"][0].applic_name,
            "Compromiso ajeno",
        )

    def test_commitment_create_form_scopes_functionary_choices(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("agenda:commitment_create"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            list(
                response.context["form"]
                .fields["functionary"]
                .queryset.values_list("user__username", flat=True)
            ),
            [self.user.username],
        )
