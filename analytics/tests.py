from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from agenda.models import Commitment
from activities.models import Activity
from configuration.models import Goal, Measuring, Period
from personal.models import Delegation, Functionary, Position


class AdminDashboardDelegationScopeTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = get_user_model().objects.create_superuser(
            username="dashboard-scope-admin",
            email="dashboard-admin@example.com",
            password="test-password",
        )
        position = Position.objects.create(name="Inspector", validity=True)
        for suffix, field in (("Uno", "URBANO"), ("Dos", "RURAL")):
            delegation = Delegation.objects.create(
                name=f"Dashboard {suffix}",
                state="ACTIVO",
                field=field,
            )
            functionary = Functionary.objects.create(
                names="Funcionario",
                lastnames=suffix,
                delegation=delegation,
                position=position,
            )
            Commitment.objects.create(
                origin="Origen",
                applic_name=f"Compromiso {suffix}",
                territory="Territorio",
                commitment_date=date.today() + timedelta(days=1),
                state=Commitment.State.PENDING,
                functionary=functionary,
            )
        cls.selected_delegation = Delegation.objects.get(name="Dashboard Dos")

    def test_dashboard_totals_follow_staff_delegation_selection(self):
        self.client.force_login(self.admin)
        session = self.client.session
        session["selected_delegation_id"] = self.selected_delegation.pk
        session.save()

        response = self.client.get(reverse("admin_dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["total_funcionarios"], 1)
        self.assertEqual(response.context["total_delegaciones"], 1)
        self.assertEqual(response.context["compromisos_pendientes"], 1)

        session = self.client.session
        session.pop("selected_delegation_id")
        session.save()
        response = self.client.get(reverse("admin_dashboard"))

        self.assertEqual(response.context["total_funcionarios"], 2)
        self.assertEqual(response.context["total_delegaciones"], 2)
        self.assertEqual(response.context["compromisos_pendientes"], 2)


class DashboardRoutingTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        user_model = get_user_model()
        cls.staff = user_model.objects.create_user(
            username="routing-staff",
            password="test-password",
            is_staff=True,
        )
        cls.unlinked_user = user_model.objects.create_user(
            username="routing-unlinked",
            password="test-password",
        )
        delegation = Delegation.objects.create(
            name="Routing", state="ACTIVO", field="URBANO"
        )
        position = Position.objects.create(name="Inspector", validity=True)
        cls.functionary_user = user_model.objects.create_user(
            username="routing-functionary",
            password="test-password",
        )
        Functionary.objects.create(
            user=cls.functionary_user,
            names="Funcionario",
            lastnames="Vinculado",
            delegation=delegation,
            position=position,
        )

    def test_staff_is_redirected_from_functionary_dashboard_to_admin(self):
        self.client.force_login(self.staff)

        response = self.client.get(reverse("user_dashboard"))

        self.assertRedirects(response, reverse("admin_dashboard"))

    def test_unlinked_user_gets_no_functionary_page(self):
        self.client.force_login(self.unlinked_user)

        response = self.client.get(reverse("user_dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "analytics/no_functionary.html")
        self.assertContains(response, "Tu usuario no está vinculado")

    def test_functionary_user_gets_functionary_dashboard(self):
        self.client.force_login(self.functionary_user)

        response = self.client.get(reverse("dashboard_redirect"))

        self.assertRedirects(response, reverse("user_dashboard"))
        dashboard_response = self.client.get(reverse("user_dashboard"))
        self.assertEqual(dashboard_response.status_code, 200)
        self.assertTemplateUsed(dashboard_response, "analytics/user_dashboard.html")
        self.assertContains(dashboard_response, "Mi panel")
        self.assertContains(dashboard_response, "Semáforo de cumplimiento")
        self.assertContains(dashboard_response, "Ver actividades")
        self.assertNotContains(dashboard_response, "Funcionarios")
        self.assertNotContains(dashboard_response, "Delegaciones")

    def test_user_dashboard_shows_weighted_indicator_and_commitment_alerts(self):
        functionary = self.functionary_user.functionary
        today = date.today()
        period = Period.objects.create(
            start_date=today - timedelta(days=10),
            end_date=today + timedelta(days=10),
            computable_days=20,
            status=True,
            version_parameter="1",
            minimum_threshold=60,
            maximum_computable_days=20,
            semaphore="1",
        )
        measuring = Measuring.objects.create(
            service="Atención",
            measurable_item="Visitas",
            validity=True,
        )
        Goal.objects.create(
            target_value=2,
            weight=Decimal("60"),
            unity="visitas",
            validity=True,
            position=functionary.position,
            period=period,
            measuring=measuring,
        )
        Activity.objects.create(
            date=today,
            application="Atención vecinal",
            taken_action="Visita",
            name_contact="Contacto",
            telephone_contact="123",
            state_validity="APPROVED",
            functionary=functionary,
            measuring=measuring,
        )
        Commitment.objects.create(
            origin="Vecino",
            applic_name="Compromiso atrasado",
            territory="Centro",
            commitment_date=today - timedelta(days=1),
            state=Commitment.State.PENDING,
            functionary=functionary,
        )

        self.client.force_login(self.functionary_user)
        response = self.client.get(reverse("user_dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["compromisos_pendientes"], 1)
        self.assertEqual(response.context["compromisos_vencidos"], 1)
        self.assertEqual(response.context["indicador"]["items"][0]["avance"], 1)
        self.assertEqual(response.context["indicador"]["total_ponderado"], Decimal("30.00"))
        self.assertEqual(response.context["semaforos"]["verde"], 1)

    def test_admin_menu_is_visible_to_staff(self):
        self.client.force_login(self.staff)

        response = self.client.get(reverse("admin_dashboard"))

        self.assertContains(response, "Funcionarios")
        self.assertContains(response, "Delegaciones")
