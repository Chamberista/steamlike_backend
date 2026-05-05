import os
import requests


MAILEROO_URL = "https://smtp.maileroo.com/api/v2/emails"


class ExternalServiceUnavailable(Exception):
    """503 — no se pudo contactar con Maileroo (timeout / red)."""


class ExternalServiceError(Exception):
    """502 — Maileroo respondió con error o respuesta inválida."""


class EmailService:
    def send_email(self, to: str, subject: str, text: str, html: str | None = None) -> dict:
        headers = {
            "Authorization": f"Bearer {os.getenv('MAILEROO_TOKEN')}",
            "Content-Type": "application/json",
        }

        payload = {
            "from": {"address": os.getenv("MAILEROO_FROM_ADDRESS")},
            "to": [{"address": to}],
            "subject": subject,
            "plain": text,
        }
        if html:
            payload["html"] = html

        try:
            r = requests.post(MAILEROO_URL, headers=headers, json=payload, timeout=5)
        except requests.RequestException:
            raise ExternalServiceUnavailable("external_service_unavailable")

        if r.status_code >= 400:
            raise ExternalServiceError("external_service_error")

        return {"ok": True}
