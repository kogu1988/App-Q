"""
Test: SemanticRouter — Mod 1 (nomic-embed) ve Mod 2 (Qwen 0.5B) routing doğrulaması

NOT: Bu testler Ollama çevrimiçi olduğunda tam çalışır.
Ollama çevrimdışıysa keyword fallback testleri yine de geçer.
"""
from packages.research_engine.nodes.router import (
    _keyword_fallback,
    _cosine_similarity,
    reset_template_cache,
    route,
    CONFIDENCE_THRESHOLD,
    ROUTE_TEMPLATES,
)


# ── Birim Testler: Yardımcı Fonksiyonlar ────────────────────────────────────

def test_cosine_similarity_identical():
    """Aynı vektörün kosinüs benzerliği 1.0 olmalı."""
    v = [1.0, 0.5, 0.3, 0.8]
    assert abs(_cosine_similarity(v, v) - 1.0) < 1e-6


def test_cosine_similarity_orthogonal():
    """Dik vektörlerin kosinüs benzerliği 0.0 olmalı."""
    a = [1.0, 0.0]
    b = [0.0, 1.0]
    assert abs(_cosine_similarity(a, b)) < 1e-6


def test_cosine_similarity_zero_vector():
    """Sıfır vektörü çöküş yaratmamalı."""
    a = [0.0, 0.0]
    b = [1.0, 0.5]
    result = _cosine_similarity(a, b)
    assert result == 0.0


def test_route_templates_not_empty():
    """Tüm route kategorilerinde en az bir şablon olmalı."""
    for route_name, templates in ROUTE_TEMPLATES.items():
        assert len(templates) >= 1, f"'{route_name}' kategorisi boş"


def test_confidence_threshold_range():
    """Güven eşiği 0.0-1.0 arasında olmalı."""
    assert 0.0 < CONFIDENCE_THRESHOLD < 1.0


# ── Keyword Fallback Testleri ────────────────────────────────────────────────

def test_keyword_fallback_orchestrator():
    """'defne' içeren sistem → orchestrator."""
    result = _keyword_fallback("Sen Defne'sin, araştırma mimarısın", "Merhaba")
    assert result == "orchestrator"


def test_keyword_fallback_intake():
    """'intake' içeren sistem → orchestrator."""
    result = _keyword_fallback("intake wizard aktif", "Brief al")
    assert result == "orchestrator"


def test_keyword_fallback_synthesis():
    """'sentez' içeren prompt → synthesis."""
    result = _keyword_fallback("Asistan", "Bu mülakatların sentezini yap")
    assert result == "synthesis"


def test_keyword_fallback_analiz():
    """'analiz' içeren prompt → synthesis."""
    result = _keyword_fallback("B2B analist rolündesin", "")
    assert result == "synthesis"


def test_keyword_fallback_persona_default():
    """Hiçbir keyword eşleşmiyorsa → persona (Trendyol)."""
    result = _keyword_fallback("Türk tüketici simülasyonu", "Bu ürün ne kadar?")
    assert result == "persona"


def test_keyword_fallback_empty_inputs():
    """Boş input çöküş yaratmamalı."""
    result = _keyword_fallback("", "")
    assert result == "persona"


# ── Entegrasyon Testi: route() Fonksiyonu ───────────────────────────────────

def test_route_returns_valid_category():
    """route() her zaman geçerli bir kategori döndürmeli (Ollama çevrimdışı bile)."""
    reset_template_cache()  # Önbelleği temizle
    valid = {"orchestrator", "synthesis", "persona"}
    result = route("Herhangi bir sistem", "Herhangi bir prompt")
    assert result in valid, f"Geçersiz route: {result}"


def test_route_keyword_strong_orchestrator():
    """Kuvvetli orchestrator sinyali → Mod 1 veya fallback orchestrator döndürmeli."""
    reset_template_cache()
    result = route(
        "Sen Defne'sin, araştırma mimarısın, intake aşamasındasın",
        "Kullanıcının araştırma hedefini anla ve brief oluştur"
    )
    assert result == "orchestrator"


def test_route_keyword_strong_synthesis():
    """Kuvvetli synthesis sinyali → synthesis döndürmeli."""
    reset_template_cache()
    result = route(
        "Sen B2B sentezleyici analistsin",
        "Rapor sentezi yap ve tematik analiz oluştur"
    )
    assert result == "synthesis"


def test_route_keyword_strong_persona():
    """Kuvvetli persona sinyali → persona döndürmeli."""
    reset_template_cache()
    result = route(
        "Sen bir Türk tüketicisin, roleplay yapıyorsun",
        "Bu ürünü satın alır mısın?"
    )
    assert result == "persona"


def test_route_ab_test_intent():
    """A/B test isteği → orchestrator (intake & brief aşaması)."""
    reset_template_cache()
    result = route(
        "Araştırma mimarı olarak brief al",
        "Reklam kopyas A vs B: hangisi daha iyi, karşılaştır"
    )
    assert result in {"orchestrator", "persona"}  # Mod 1 ile değişebilir, ikisi de kabul


def test_route_always_returns_string():
    """route() her durumda str döndürmeli, exception fırlatmamalı."""
    reset_template_cache()
    for system, prompt in [
        ("", ""),
        ("x" * 1000, "y" * 1000),
        ("türkçe karakterler: şğüıöç", "test"),
    ]:
        result = route(system, prompt)
        assert isinstance(result, str)
        assert result in {"orchestrator", "synthesis", "persona"}
