from unittest.mock import patch, MagicMock
from django.test import TestCase, override_settings
import requests

from library.email_service import EmailService, ExternalServiceUnavailable, ExternalServiceError

SETTINGS = {
    "MAILEROO_TOKEN": "fake-token",
    "MAILEROO_FROM_ADDRESS": "test@example.com",
}


@override_settings(**SETTINGS)
class EmailServiceTest(TestCase):

    def _service(self):
        return EmailService()

    # --- Test 1: envío correcto ---
    @patch("library.email_service.requests.post")
    def test_send_email_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "success": True,
            "message": "The email has been scheduled for delivery.",
            "data": {"reference_id": "abc123"},
        }
        mock_post.return_value = mock_response

        result = self._service().send_email(
            to="recipient@example.com",
            subject="Hola",
            text="Cuerpo del email",
        )

        self.assertTrue(result["success"])
        mock_post.assert_called_once()

    # --- Test 2: 503 — timeout de red ---
    @patch("library.email_service.requests.post", side_effect=requests.exceptions.Timeout)
    def test_send_email_timeout_raises_503(self, _mock):
        with self.assertRaises(ExternalServiceUnavailable):
            self._service().send_email("x@x.com", "Sub", "Texto")

    # --- Test 3: 503 — error de conexión ---
    @patch("library.email_service.requests.post", side_effect=requests.exceptions.ConnectionError)
    def test_send_email_connection_error_raises_503(self, _mock):
        with self.assertRaises(ExternalServiceUnavailable):
            self._service().send_email("x@x.com", "Sub", "Texto")

    # --- Test 4: 502 — Maileroo responde con error HTTP (token inválido) ---
    @patch("library.email_service.requests.post")
    def test_send_email_provider_error_raises_502(self, mock_post):
        mock_response = MagicMock()
        mock_response.ok = False
        mock_response.status_code = 401
        mock_response.json.return_value = {"message": "Unauthorized"}
        mock_post.return_value = mock_response

        with self.assertRaises(ExternalServiceError):
            self._service().send_email("x@x.com", "Sub", "Texto")

    # --- Test 5: 502 — respuesta no es JSON válido ---
    @patch("library.email_service.requests.post")
    def test_send_email_invalid_json_raises_502(self, mock_post):
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.side_effect = ValueError("no json")
        mock_post.return_value = mock_response

        with self.assertRaises(ExternalServiceError):
            self._service().send_email("x@x.com", "Sub", "Texto")
