from datetime import date

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from configuration.models import Measuring
from personal.models import Delegation, Functionary, Position

from .models import Activity, Evidence


class ActivityDelegationScopeTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        user_model = get_user_model()
        cls.user = user_model.objects.create_user(
            username="activity-scope-user",
            password="test-password",
        )
        cls.admin = user_model.objects.create_superuser(
            username="activity-scope-admin",
            email="activity-admin@example.com",
            password="test-password",
        )
        first_delegation = Delegation.objects.create(
            name="Actividad Uno", state="ACTIVO", field="URBANO"
        )
        cls.second_delegation = Delegation.objects.create(
            name="Actividad Dos", state="ACTIVO", field="RURAL"
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
        measuring = Measuring.objects.create(
            service="Atención",
            measurable_item="Visitas",
            validity=True,
        )
        Activity.objects.create(
            date=date(2026, 10, 20),
            application="Actividad propia",
            taken_action="Acción",
            name_contact="Contacto",
            telephone_contact="123",
            functionary=first_functionary,
            measuring=measuring,
        )
        Activity.objects.create(
            date=date(2026, 10, 20),
            application="Actividad ajena",
            taken_action="Acción",
            name_contact="Contacto",
            telephone_contact="123",
            functionary=second_functionary,
            measuring=measuring,
        )

    def test_activity_list_only_shows_the_users_delegation(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("activities:activity_list"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["activities"]), 1)
        self.assertEqual(
            response.context["activities"][0].application,
            "Actividad propia",
        )
        self.assertContains(response, "data-modal-form")
        self.assertContains(response, "data-swal-confirm")

    def test_staff_selection_filters_activity_list(self):
        self.client.force_login(self.admin)
        session = self.client.session
        session["selected_delegation_id"] = self.second_delegation.pk
        session.save()

        response = self.client.get(reverse("activities:activity_list"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["activities"]), 1)
        self.assertEqual(
            response.context["activities"][0].application,
            "Actividad ajena",
        )

    def test_evidence_create_form_scopes_functionary_and_activity_choices(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("activities:evidence_create"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            list(response.context["form"].fields["functionary"].queryset.values_list(
                "user__username", flat=True
            )),
            [self.user.username],
        )
        self.assertEqual(
            list(response.context["form"].fields["activity"].queryset.values_list(
                "application", flat=True
            )),
            ["Actividad propia"],
        )

    def test_evidence_create_form_saves_required_fields_and_file(self):
        self.client.force_login(self.user)
        functionary = self.user.functionary
        activity = Activity.objects.get(application="Actividad propia")

        response = self.client.post(
            reverse("activities:evidence_create"),
            {
                "name": "Registro de atención",
                "author": "Funcionario Uno",
                "date_evidence": "2026-10-20",
                "metadata": "Registro de la visita",
                "activity": activity.pk,
                "functionary": functionary.pk,
                "file": SimpleUploadedFile(
                    "evidencia.txt", b"contenido de prueba", content_type="text/plain"
                ),
            },
        )

        self.assertRedirects(response, reverse("activities:evidence_list"))
        self.assertTrue(
            Evidence.objects.filter(
                name="Registro de atención",
                activity=activity,
                functionary=functionary,
            ).exists()
        )

    def test_activity_update_reports_success(self):
        self.client.force_login(self.user)
        activity = Activity.objects.get(application="Actividad propia")

        response = self.client.post(
            reverse("activities:activity_update", args=[activity.pk]),
            {
                "date": activity.date.isoformat(),
                "application": "Actividad actualizada",
                "taken_action": activity.taken_action,
                "name_contact": activity.name_contact,
                "telephone_contact": activity.telephone_contact,
                "functionary": activity.functionary_id,
                "measuring": activity.measuring_id,
                "commitment": "",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Actividad actualizada correctamente.")
