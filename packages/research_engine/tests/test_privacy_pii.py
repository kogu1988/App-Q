"""PII maskeleme dayanıklılığı + plan gate testleri (Claude denetimi bulgusu).

Korunan değerler:
- Regex katmanı (telefon/e-posta/TC) model olmadan HER planda çalışmalı.
- Yerel NER modeli (isim/lokasyon) yalnızca Enterprise özelliği olmalı.
- Model yoksa sistem ÇÖKMEMELİ (regex'e düşmeli); yalnızca PII_STRICT=true ise hata fırlatmalı.
"""
from __future__ import annotations

import asyncio

import pytest

from packages.research_engine.plan_config import has_feature
from packages.research_engine.privacy import LocalPIIScrubber, PrivacyFilterException


def _run(coro):
    return asyncio.run(coro)


SAMPLE = "Ben Ahmet Yılmaz, telefonum 0555 123 45 67 ve e-postam ahmet@example.com, TC 12345678901."


def test_regex_layer_masks_without_model():
    """NER kapalıyken telefon/e-posta/TC maskelenmeli; ağ çağrısı YAPILMAMALI."""
    scrubber = LocalPIIScrubber(enable_ner=False)
    out = _run(scrubber.sanitize_input(SAMPLE))

    assert "[B_PHONE_1]" in out.sanitized_text
    assert "[B_EMAIL_1]" in out.sanitized_text
    assert "[B_TC_1]" in out.sanitized_text
    assert "ahmet@example.com" not in out.sanitized_text
    # Geri dönüşüm sözlüğü tutulmalı
    assert out.context.mask_to_original["[B_EMAIL_1]"] == "ahmet@example.com"


def test_ner_unreachable_falls_back_to_regex(monkeypatch):
    """NER açık ama model erişilemezse (varsayılan mod) regex sonucu dönmeli, hata FIRLATMAMALI."""
    monkeypatch.setenv("PII_MODEL_URL", "http://127.0.0.1:9/v1/chat/completions")
    monkeypatch.setenv("PII_TIMEOUT", "1")
    monkeypatch.setenv("PII_STRICT", "false")

    scrubber = LocalPIIScrubber(enable_ner=True)
    out = _run(scrubber.sanitize_input(SAMPLE))

    assert "[B_PHONE_1]" in out.sanitized_text


def test_ner_unreachable_strict_raises(monkeypatch):
    """PII_STRICT=true ise model yoksa PrivacyFilterException fırlatılmalı (Enterprise modu)."""
    monkeypatch.setenv("PII_MODEL_URL", "http://127.0.0.1:9/v1/chat/completions")
    monkeypatch.setenv("PII_TIMEOUT", "1")
    monkeypatch.setenv("PII_STRICT", "true")

    scrubber = LocalPIIScrubber(enable_ner=True)
    with pytest.raises(PrivacyFilterException):
        _run(scrubber.sanitize_input(SAMPLE))


def test_local_pii_scrubbing_is_enterprise_only():
    """Yerel NER yalnızca Enterprise özelliği olmalı."""
    assert has_feature("Enterprise", "local_pii_scrubbing") is True
    for plan in ("Free", "Flex", "Starter", "Pro"):
        assert has_feature(plan, "local_pii_scrubbing") is False, plan
