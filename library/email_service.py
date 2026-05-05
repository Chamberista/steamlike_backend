import logging
import os
import requests


MAILEROO_URL = "https://smtp.maileroo.com/api/v2/emails"

# MAILEROO_URL = "https://httpstat.us/401" # 503 servicio no disponible

logger = logging.getLogger(__name__)


class ExternalServiceUnavailable(Exception):
    """503 — no se pudo contactar con Maileroo (timeout / red)."""


class ExternalServiceError(Exception):
    """502 — Maileroo respondió con error o respuesta inválida."""


class EmailService:
    def send_email(
        self,
        to: str,
        subject: str,
        text: str,
        html: str | None = None,
        action: str = "send_email",
        user: str | None = None,
    ) -> dict:
        log_ctx = {"action": action, "to": to}
        if user:
            log_ctx["user"] = user

        logger.info("intento de envío | %s", log_ctx)

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
        except requests.RequestException as exc:
            logger.error(
                "fallo por timeout/red | %s | error=%s",
                log_ctx,
                type(exc).__name__,
            )
            raise ExternalServiceUnavailable("external_service_unavailable")

        if r.status_code >= 400:
            logger.error(
                "fallo por respuesta del proveedor | %s | status=%s",
                log_ctx,
                r.status_code,
            )
            raise ExternalServiceError("external_service_error")

        logger.info("envío OK | %s | resultado=ok", log_ctx)
        return {"ok": True}
