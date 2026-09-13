"""enrich_themes_narrative — async 'Research Studio' tematik rapor zenginleştirmesi."""
from __future__ import annotations

import json

from packages.research_engine.analytics import enrich_themes_narrative

_THEMES = [
    {"title": "Fiyat hassasiyeti", "prevalence": 50.0, "evidence_chain": [{"quote": "Aylık 300 lira yüksek"}]},
]


class _FakeModel:
    def __init__(self, payload: str) -> None:
        self._payload = payload

    def generate(self, system: str, prompt: str, response_format=None, max_tokens=None) -> str:
        return self._payload


class _BoomModel:
    def generate(self, *args, **kwargs) -> str:
        raise RuntimeError("boom")


def test_returns_narrative_and_recommendations():
    model = _FakeModel(json.dumps({"yonetici_anlatimi": "Anlatım metni.", "stratejik_oneriler": ["A", "B"]}))

    narrative, recs = enrich_themes_narrative(_THEMES, model)

    assert narrative == "Anlatım metni."
    assert recs == ["A", "B"]


def test_graceful_degradation_on_model_error():
    narrative, recs = enrich_themes_narrative(_THEMES, _BoomModel())

    assert (narrative, recs) == ("", [])


def test_non_dict_json_returns_empty():
    narrative, recs = enrich_themes_narrative(_THEMES, _FakeModel('["liste"]'))

    assert (narrative, recs) == ("", [])
