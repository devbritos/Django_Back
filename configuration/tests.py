from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse

from .models import Measuring

# Create your tests here.


class MeasuringCatalogViewTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            username='admin_items',
            email='items@example.com',
            password='test-password',
        )
        self.client.force_login(self.admin)

    def test_measuring_list_searches_and_exports(self):
        Measuring.objects.create(
            code='IT-01',
            service='Atención vecinal',
            measurable_item='Descripción de prueba',
        )
        response = self.client.get(
            reverse('configuration:measuring_list'),
            {'q': 'VECINAL'},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Atención vecinal')

        export = self.client.get(
            reverse('configuration:measuring_list'),
            {'export': 'xlsx', 'q': 'vecinal'},
        )
        self.assertEqual(export.status_code, 200)
        self.assertEqual(
            export['Content-Type'],
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )

    def test_measuring_create_reports_success_only_after_save(self):
        response = self.client.post(
            reverse('configuration:measuring_create'),
            {
                'code': 'IT-02',
                'service': 'Nuevo ítem',
                'measurable_item': 'Descripción',
                'validity': 'on',
            },
        )
        self.assertRedirects(response, reverse('configuration:measuring_list'))
        self.assertTrue(Measuring.objects.filter(code='IT-02').exists())
