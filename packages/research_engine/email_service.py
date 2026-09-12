"""İşlemsel e-posta gönderimi — Resend API (opsiyonel).

`RESEND_API_KEY` tanımlı değilse tüm fonksiyonlar sessizce `False` döner; hiçbir
ürün akışı e-posta yüzünden çökmez (fail-safe).

Gerekli ortam değişkenleri:
    RESEND_API_KEY        Resend API anahtarı
    RESEND_FROM           Gönderen (ör. "Clarere <hiclarere@clarere.com>")
    CONTACT_NOTIFY_EMAIL  İletişim formu bildirimlerinin gideceği adres
"""
from __future__ import annotations

import html
import logging
import os

import requests

logger = logging.getLogger(__name__)

_RESEND_ENDPOINT = "https://api.resend.com/emails"
_DEFAULT_FROM = "Clarere <hiclarere@clarere.com>"
_DEFAULT_NOTIFY = "hiclarere@clarere.com"


def is_configured() -> bool:
    """E-posta gönderimi yapılandırılmış mı?"""
    return bool((os.getenv("RESEND_API_KEY") or "").strip())


def send_email(
    to: str | list[str],
    subject: str,
    html_body: str,
    text_body: str | None = None,
    reply_to: str | None = None,
) -> bool:
    """Resend üzerinden e-posta gönderir. Başarılıysa True.

    Hata durumunda istisna FIRLATMAZ — loglar ve False döner.
    """
    api_key = (os.getenv("RESEND_API_KEY") or "").strip()
    if not api_key:
        logger.debug("RESEND_API_KEY yok — e-posta atlandı: %s", subject)
        return False

    recipients = [to] if isinstance(to, str) else list(to)
    payload: dict = {
        "from": os.getenv("RESEND_FROM", _DEFAULT_FROM),
        "to": recipients,
        "subject": subject,
        "html": html_body,
    }
    if text_body:
        payload["text"] = text_body
    if reply_to:
        payload["reply_to"] = reply_to

    try:
        resp = requests.post(
            _RESEND_ENDPOINT,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json=payload,
            timeout=15,
        )
        if resp.status_code >= 400:
            logger.error("Resend gönderim hatası (%s): %s", resp.status_code, resp.text[:300])
            return False
        logger.info("E-posta gönderildi: %s", subject)
        return True
    except Exception:
        logger.warning("Resend isteği başarısız: %s", subject, exc_info=True)
        return False


def notify_contact_form(name: str, email: str, message: str) -> bool:
    """İletişim formu gönderimini hiclarere@clarere.com adresine bildirir."""
    target = os.getenv("CONTACT_NOTIFY_EMAIL", _DEFAULT_NOTIFY)
    subject = f"Clarere iletişim formu — {name}"

    safe_name = html.escape(name)
    safe_email = html.escape(email)
    safe_message = html.escape(message).replace("\n", "<br>")

    html_body = (
        "<h2>Yeni iletişim formu mesajı</h2>"
        f"<p><strong>Ad:</strong> {safe_name}</p>"
        f"<p><strong>E-posta:</strong> {safe_email}</p>"
        f"<p><strong>Mesaj:</strong></p><p>{safe_message}</p>"
    )
    text_body = f"Ad: {name}\nE-posta: {email}\n\n{message}"

    return send_email(target, subject, html_body, text_body=text_body, reply_to=email)
