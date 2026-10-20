from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory, SimpleTestCase, override_settings

from config import urls
from config.views import permission_denied


class ErrorPageTests(SimpleTestCase):
    @override_settings(DEBUG=False)
    def test_not_found_handler_renders_warning_with_404_status(self):
        response = self.client.get("/pagina-inexistente/")

        self.assertEqual(response.status_code, 404)
        self.assertContains(response, "Error 404", status_code=404)
        self.assertContains(response, "Volver a la página anterior", status_code=404)

    @override_settings(DEBUG=False)
    def test_permission_denied_handler_renders_warning_with_403_status(self):
        self.assertEqual(urls.handler403, "config.views.permission_denied")
        request = RequestFactory().get("/pagina-restringida/")
        request.user = AnonymousUser()

        response = permission_denied(request)

        self.assertEqual(response.status_code, 403)
        self.assertContains(response, "Error 403", status_code=403)
        self.assertContains(response, "Volver a la página anterior", status_code=403)
