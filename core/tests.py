from django.test import TestCase
from django.contrib.auth.models import User
from django.test import override_settings


@override_settings(DEBUG=False)
class ErrorPageTests(TestCase):
    def test_not_found_uses_custom_page_and_back_button(self):
        response = self.client.get('/this-page-does-not-exist/')

        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, '404.html')
        self.assertContains(response, 'Página no encontrada', status_code=404)
        self.assertContains(response, 'Volver a la página anterior', status_code=404)
        self.assertContains(response, 'sweetalert2', status_code=404)

    def test_forbidden_uses_custom_page_and_back_button(self):
        user = User.objects.create_user(username='unauthorized_user')
        self.client.force_login(user)

        response = self.client.get('/activities/evidencias/1/validar/')

        self.assertEqual(response.status_code, 403)
        self.assertTemplateUsed(response, '403.html')
        self.assertContains(response, 'Acceso denegado', status_code=403)
        self.assertContains(response, 'Volver a la página anterior', status_code=403)
        self.assertContains(response, 'sweetalert2', status_code=403)
