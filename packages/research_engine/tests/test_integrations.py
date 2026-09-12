"""Entegrasyon sözleşme testleri — Resend ve Sentry.

Korunan değer: Dış servis entegrasyonlarının **doğru sözleşmeyle** çağrıldığını
ve hata durumunda ürün akışını çökertmediğini doğrular. Gerçek ağ çağrısı YAPILMAZ
(`requests.post` monkeypatch edilir).

Gerçek uçtan uca doğrulama için `RESEND_API_KEY` ve `SENTRY_DSN` gerekir; bu testler
anahtar olmadan da entegrasyon kod yolunu korur.
"""
from __future__ import annotations

import pathlib

import pytest

from packages.research_engine import email_service


class _FakeResponse:
    def __init__(self, status_code: int = 200, text: str = "ok"):
        self.status_code = status_code
        self.text = text


def test_resend_payload_contract(monkeypatch):
    """Resend çağrısı doğru endpoint, header ve gövdeyle yapılmalı."""
    captured: dict = {}

    def fake_post(url, headers=None, json=None, timeout=None):
        captured.update({"url": url, "headers": headers, "json": json})
        return _FakeResponse(200)

    monkeypatch.setenv("RESEND_API_KEY", "re_test_key")
    monkeypatch.setenv("RESEND_FROM", "Clarere <hiclarere@clarere.com>")
    monkeypatch.setattr(email_service.requests, "post", fake_post)

    ok = email_service.send_email("hedef@example.com", "Konu", "<p>gövde</p>", text_body="gövde")

    assert ok is True
    assert captured["url"] == "https://api.resend.com/emails"
    assert captured["headers"]["Authorization"] == "Bearer re_test_key"
    assert captured["json"]["from"] == "Clarere <hiclarere@clarere.com>"
    assert captured["json"]["to"] == ["hedef@example.com"]
    assert captured["json"]["subject"] == "Konu"
    assert captured["json"]["html"] == "<p>gövde</p>"
    assert captured["json"]["text"] == "gövde"


def test_resend_failure_is_fail_safe(monkeypatch):
    """Resend 4xx dönerse istisna fırlatılmamalı, False dönmeli."""
    monkeypatch.setenv("RESEND_API_KEY", "re_test_key")
    monkeypatch.setattr(
        email_service.requests, "post", lambda *a, **k: _FakeResponse(401, "unauthorized")
    )

    assert email_service.send_email("hedef@example.com", "Konu", "<p>x</p>") is False


def test_resend_network_error_is_fail_safe(monkeypatch):
    """Ağ hatası ürün akışını çökertmemeli."""
    monkeypatch.setenv("RESEND_API_KEY", "re_test_key")

    def boom(*args, **kwargs):
        raise ConnectionError("ağ yok")

    monkeypatch.setattr(email_service.requests, "post", boom)

    assert email_service.send_email("hedef@example.com", "Konu", "<p>x</p>") is False


def test_contact_notification_targets_and_replies(monkeypatch):
    """İletişim formu bildirimi yapılandırılmış adrese gider, yanıt adresi kullanıcı olur."""
    captured: dict = {}

    def fake_post(url, headers=None, json=None, timeout=None):
        captured.update(json)
        return _FakeResponse(200)

    monkeypatch.setenv("RESEND_API_KEY", "re_test_key")
    monkeypatch.setenv("CONTACT_NOTIFY_EMAIL", "hiclarere@clarere.com")
    monkeypatch.setattr(email_service.requests, "post", fake_post)

    ok = email_service.notify_contact_form("Ali", "ali@example.com", "Merhaba")

    assert ok is True
    assert captured["to"] == ["hiclarere@clarere.com"]
    assert captured["reply_to"] == "ali@example.com"
    # HTML kaçışı uygulanmalı
    assert "Ali" in captured["html"]


def test_contact_notification_escapes_html(monkeypatch):
    """Kullanıcı girdisi HTML'e kaçışsız gömülmemeli (XSS/enjeksiyon koruması)."""
    captured: dict = {}

    def fake_post(url, headers=None, json=None, timeout=None):
        captured.update(json)
        return _FakeResponse(200)

    monkeypatch.setenv("RESEND_API_KEY", "re_test_key")
    monkeypatch.setattr(email_service.requests, "post", fake_post)

    email_service.notify_contact_form("<script>alert(1)</script>", "x@example.com", "<b>kötü</b>")

    assert "<script>" not in captured["html"]
    assert "&lt;script&gt;" in captured["html"]


def test_sentry_is_env_gated_and_pii_disabled():
    """Sentry yalnızca SENTRY_DSN varsa başlatılmalı ve kişisel veri göndermemeli."""
    source = pathlib.Path("apps/backend/main.py").read_text(encoding="utf-8")

    assert 'os.getenv("SENTRY_DSN")' in source, "Sentry env ile kapılı olmalı"
    assert "send_default_pii=False" in source, "KVKK: kişisel veri Sentry'ye gitmemeli"
    assert "FastApiIntegration" in source
