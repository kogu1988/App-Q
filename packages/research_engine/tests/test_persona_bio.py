"""Persona biyografisi doğallaştırma (enrich_persona_bios) regresyon testleri."""
import json

from packages.research_engine.workflow import enrich_persona_bios, generate_personas
from packages.research_engine.tests.helpers import make_brief


class _FakeModel:
    """generate() çağrısını LLM olmadan taklit eder."""

    def __init__(self, payload=None, raise_exc: bool = False):
        self.payload = payload
        self.raise_exc = raise_exc
        self.last_system = ""
        self.last_prompt = ""

    def generate(self, system, prompt, response_format=None, max_tokens=None):
        self.last_system = system
        self.last_prompt = prompt
        if self.raise_exc:
            raise RuntimeError("llm down")
        return json.dumps(self.payload)


def test_enrich_persona_bios_replaces_template_bios():
    personas = generate_personas(make_brief())
    payload = {
        "bios": {
            p.id: (
                f"{p.name}, {p.city}'de yaşayan bir {p.role_title or p.segment}. "
                f"Mevcut iş akışını dağınık araçlarla yürütüyor ve somut tasarruf gördüğünde yeni çözümlere yaklaşıyor."
            )
            for p in personas
        }
    }

    enriched = enrich_persona_bios(personas, make_brief(), _FakeModel(payload))

    for p in enriched:
        assert p.bio == payload["bios"][p.id]
        assert "..." not in p.bio and "…" not in p.bio


def test_enrich_persona_bios_rejects_missing_id_and_keeps_template():
    personas = generate_personas(make_brief())
    originals = {p.id: p.bio for p in personas}
    # Yalnızca tek persona için bio döner; diğerleri şablon kalmalı.
    target = personas[0]
    payload = {"bios": {target.id: "Kısa ve geçerli bir biyografi cümlesi burada yer alır ve yeterince uzundur."}}

    enriched = enrich_persona_bios(personas, make_brief(), _FakeModel(payload))

    assert enriched[0].bio == payload["bios"][target.id]
    for p in enriched[1:]:
        assert p.bio == originals[p.id], "veri gelmeyen persona şablon bio'sunu korumalı"


def test_enrich_persona_bios_rejects_ellipsis_and_short_text():
    personas = generate_personas(make_brief())
    originals = {p.id: p.bio for p in personas}
    payload = {"bios": {p.id: "Kısa..." if i % 2 == 0 else "kısa" for i, p in enumerate(personas)}}

    enriched = enrich_persona_bios(personas, make_brief(), _FakeModel(payload))

    for p in enriched:
        assert p.bio == originals[p.id]


def test_enrich_persona_bios_is_failsafe_on_llm_error():
    personas = generate_personas(make_brief())
    originals = {p.id: p.bio for p in personas}

    enriched = enrich_persona_bios(personas, make_brief(), _FakeModel(raise_exc=True))

    for p in enriched:
        assert p.bio == originals[p.id]


def test_enrich_persona_bios_noop_without_model():
    personas = generate_personas(make_brief())
    originals = [p.bio for p in personas]

    enriched = enrich_persona_bios(personas, make_brief(), None)

    assert [p.bio for p in enriched] == originals


def test_enrich_persona_bios_preserves_scientific_fields():
    """Biyografi zenginleştirmesi hiçbir bilimsel atamayı DEĞİŞTİRMEMELİ."""
    personas = generate_personas(make_brief())
    baseline = {
        p.id: {
            "stance": p.stance,
            "ses_group": p.ses_group,
            "big_five": dict(p.big_five),
            "traits": dict(p.traits),
            "neo_facets": dict(p.neo_facets),
            "diffusion_stage": p.diffusion_stage,
            "price_sensitivity": p.price_sensitivity,
            "digital_confidence": p.digital_confidence,
            "attributes": dict(p.attributes),
            "age": p.age,
            "city": p.city,
        }
        for p in personas
    }
    payload = {p.id: "Davranış odaklı, doğal ve yeterince uzun bir persona biyografisi cümlesi." for p in personas}

    enriched = enrich_persona_bios(personas, make_brief(), _FakeModel({"bios": payload}))

    for p in enriched:
        b = baseline[p.id]
        assert p.stance == b["stance"]
        assert p.ses_group == b["ses_group"]
        assert p.big_five == b["big_five"]
        assert p.traits == b["traits"]
        assert p.neo_facets == b["neo_facets"]
        assert p.diffusion_stage == b["diffusion_stage"]
        assert p.price_sensitivity == b["price_sensitivity"]
        assert p.digital_confidence == b["digital_confidence"]
        assert p.attributes == b["attributes"]
        assert p.age == b["age"] and p.city == b["city"]


def test_enrich_persona_bios_prompt_is_psychometrically_grounded():
    """Prompt, Big Five / Rogers kısıtlarını ve sayı yazmama kuralını içermeli."""
    personas = generate_personas(make_brief())
    fake = _FakeModel({"bios": {}})

    enrich_persona_bios(personas, make_brief(), fake)

    prompt = fake.last_prompt + fake.last_system
    for marker in [
        "Big Five",
        "Açıklık",
        "Sorumluluk",
        "Dışadönüklük",
        "Uyumluluk",
        "Duygusal dengesizlik",
        "Rogers duruşu",
        "DEĞİŞTİRİLEMEZ",
        "sayı olarak yazma",
    ]:
        assert marker in prompt, f"prompt eksik: {marker}"
