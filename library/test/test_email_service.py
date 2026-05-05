from unittest.mock import patch, MagicMock
from django.test import TestCase
import requests

from library.email_service import EmailService, ExternalServiceUnavailable, ExternalServiceError


class EmailServiceTest(TestCase):

    # --- Test 1: envío correcto ---
    @patch("library.email_service.requests.post")
    def test_send_email_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        result = EmailService().send_email(
            to="recipient@example.com",
            subject="Hola",
            text="Cuerpo del email",
        )

        self.assertTrue(result["ok"])
        mock_post.assert_called_once()

    # --- Test 2: 503 — timeout / error de red ---
    @patch("library.email_service.requests.post", side_effect=requests.RequestException)
    def test_send_email_network_error_raises_503(self, _mock):
        with self.assertRaises(ExternalServiceUnavailable):
            EmailService().send_email("x@x.com", "Sub", "Texto")

    # --- Test 3: 502 — Maileroo responde con error HTTP (token inválido) ---
    @patch("library.email_service.requests.post")
    def test_send_email_provider_error_raises_502(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_post.return_value = mock_response

        with self.assertRaises(ExternalServiceError):
            EmailService().send_email("x@x.com", "Sub", "Texto")
