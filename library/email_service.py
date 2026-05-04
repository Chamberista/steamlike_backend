import requests
from django.conf import settings


MAILEROO_API_URL = "https://smtp.maileroo.com/api/v2/emails"
TIMEOUT_SECONDS = 10


class ExternalServiceUnavailable(Exception):
    """503 — no se pudo contactar con Maileroo (timeout / red)."""


class ExternalServiceError(Exception):
    """502 — Maileroo respondió con error o respuesta inválida."""


class EmailService:
    def __init__(self, api_url: str = MAILEROO_API_URL):
        self._api_url = api_url
        self._token = settings.MAILEROO_TOKEN
        self._from = settings.MAILEROO_FROM_ADDRESS

    def send_email(self, to: str, subject: str, text: str, html: str | None = None) -> dict:
        """
        Envía un email mediante Maileroo.

        Raises:
            ExternalServiceUnavailable: timeout o fallo de red → equivalente a 503.
            ExternalServiceError: respuesta de error o inválida de Maileroo → equivalente a 502.
        """
        payload = {
            "from": {"address": self._from},
            "to": [{"address": to}],
            "subject": subject,
            "plain": text,
        }
        if html:
            payload["html"] = html

        headers = {
            "X-Api-Key": self._token,
            "Accept": "application/json",
        }

        try:
            response = requests.post(
                self._api_url,
                json=payload,
                headers=headers,
                timeout=TIMEOUT_SECONDS,
            )
        except requests.exceptions.Timeout:
            raise ExternalServiceUnavailable("Maileroo: timeout al conectar")
        except requests.exceptions.ConnectionError as exc:
            raise ExternalServiceUnavailable(f"Maileroo: error de red — {exc}")

        try:
            body = response.json()
        except ValueError:
            raise ExternalServiceError("Maileroo: respuesta no es JSON válido")

        if not response.ok:
            detail = body.get("message") or response.text[:200]
            raise ExternalServiceError(f"Maileroo respondió {response.status_code}: {detail}")

        if not body.get("success", False):
            raise ExternalServiceError(f"Maileroo indicó fallo: {body.get('message', 'sin detalle')}")

        return body
