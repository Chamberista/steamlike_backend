import requests
from django.conf import settings


MAILEROO_API_URL = "https://smtp.maileroo.com/send"
TIMEOUT_SECONDS = 10


class ExternalServiceUnavailable(Exception):
    """503 — no se pudo contactar con Maileroo (timeout / red)."""


class ExternalServiceError(Exception):
    """502 — Maileroo respondió con error o respuesta inválida."""


class EmailService:
    def __init__(self):
        self._token = settings.MAILEROO_TOKEN
        self._from = settings.MAILEROO_FROM_ADDRESS

    def send_email(self, to: str, subject: str, text: str, html: str | None = None) -> dict:
        payload = {
            "from": self._from,
            "to": to,
            "subject": subject,
            "plain_body": text,
        }
        if html:
            payload["html_body"] = html

        headers = {"X-API-Key": self._token}

        try:
            response = requests.post(
                MAILEROO_API_URL,
                data=payload,
                headers=headers,
                timeout=TIMEOUT_SECONDS,
            )
        except requests.exceptions.Timeout:
            raise ExternalServiceUnavailable("Maileroo: timeout al conectar")
        except requests.exceptions.ConnectionError as exc:
            raise ExternalServiceUnavailable(f"Maileroo: error de red — {exc}")

        if not response.ok:
            raise ExternalServiceError(
                f"Maileroo respondió {response.status_code}: {response.text[:200]}"
            )

        try:
            return response.json()
        except ValueError:
            raise ExternalServiceError("Maileroo: respuesta no es JSON válido")
