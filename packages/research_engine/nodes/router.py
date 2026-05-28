"""
router.py — Semantic Routing Engine (god_doc.md §5)

Çift modlu yönlendirme:
  Mod 1: nomic-embed-text kosinüs benzerliği — hızlı, sıfır VRAM, <50ms
  Mod 2: Qwen 2.5 0.5B niyet ayrıştırması   — yalnızca Mod 1 belirsiz kaldığında
  Fallback: keyword eşleşmesi                — her zaman güvende

Route kategorileri:
  "orchestrator" → Kızagan E4B (intake, brief, Sokratik, A/B intent)
  "synthesis"    → Asure 12B   (rapor, sentez, tematik analiz)
  "persona"      → Trendyol 7B (mülakat, roleplay, tüketici simülasyonu)

ÖNEMLİ: Bu modül OLLAMA_LOCK dışında çalışır.
Routing kararı her zaman generate() çağrısından ÖNCE verilir.
"""
from __future__ import annotations

import json
import logging
import math
import os
import re
import urllib.request
from typing import Optional

logger = logging.getLogger(__name__)

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")


# ── Route Şablonları ──────────────────────────────────────────────────────────
# Her kategori için temsili Türkçe ifadeler.
# Gelecek intent kategorisi eklemek için sadece yeni anahtar + liste ekle.
ROUTE_TEMPLATES: dict[str, list[str]] = {
    "orchestrator": [
        "brief oluştur araştırma hedefi sokratik soru intake uzmanı",
        "defne wizardalways epistemik filtre araştırma mimarı",
        "ab test karşılaştır varyant hangisi daha iyi intent classification",
        "araştırma planı hipotez doğrulama problem tanımı",
    ],
    "synthesis": [
        "rapor yaz tematik analiz pazar sentezi yönetici özeti",
        "kanıt zinciri bariyer analizi stratejik öneri McKinsey",
        "brand health marka sağlık analiz ses crosstab bulgu",
        "sonuçları derle araştırma raporu özet çıkar",
    ],
    "persona": [
        "mülakat sorusu tüketici tepkisi ürün yorumu sepet kargo",
        "fiyat taksit marka beğenmedim satın alma kararı alışveriş",
        "roleplay karakter C2 SES persona simülasyon Türk tüketici",
        "bu ürün hakkında ne düşünürsün nasıl hissedersin tepki ver",
    ],
}

# Mod 1 güven eşiği — bu değerin altında Mod 2 tetiklenir
CONFIDENCE_THRESHOLD = 0.65

# Qwen 2.5 0.5B — deterministik routing için düşük temperature
QWEN_MODEL_ID = "qwen2.5:0.5b"
QWEN_TIMEOUT = 15  # saniye — routing hızlı olmalı


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """İki vektör arasındaki kosinüs benzerliğini hesaplar."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def _embed(text: str, base_url: str = OLLAMA_BASE_URL) -> Optional[list[float]]:
    """nomic-embed-text ile metin gömme (embedding).

    OLLAMA_LOCK dışında çalışır — CPU işlemi, VRAM yüklemez.
    """
    url = f"{base_url.rstrip('/')}/api/embeddings"
    payload = json.dumps({"model": "nomic-embed-text", "prompt": text}).encode("utf-8")
    try:
        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("embedding")
    except Exception as exc:
        logger.debug("nomic-embed-text çağrısı başarısız: %s", exc)
        return None


# ── Şablon Vektör Önbelleği (Lazy-init) ──────────────────────────────────────
_template_cache: dict[str, list[float]] | None = None


def _get_template_embeddings(base_url: str = OLLAMA_BASE_URL) -> dict[str, list[float]]:
    """Şablon metinlerini ilk çağrıda embed'ler ve önbellekler (thread-unsafe ama kabul edilebilir).

    Her şablon metni için ortalama embedding hesaplanır.
    """
    global _template_cache
    if _template_cache is not None:
        return _template_cache

    logger.info("SemanticRouter: Şablon vektörleri yükleniyor...")
    cache: dict[str, list[float]] = {}

    for route, templates in ROUTE_TEMPLATES.items():
        embeddings = []
        for tmpl in templates:
            vec = _embed(tmpl, base_url)
            if vec:
                embeddings.append(vec)

        if embeddings:
            # Şablonların ortalama vektörünü hesapla
            dim = len(embeddings[0])
            avg = [sum(e[i] for e in embeddings) / len(embeddings) for i in range(dim)]
            cache[route] = avg
            logger.debug("Route '%s' şablon vektörü hazır (%d template, dim=%d)", route, len(embeddings), dim)
        else:
            logger.warning("Route '%s' için embedding üretilemedi — bu route atlanıyor", route)

    _template_cache = cache
    logger.info("SemanticRouter: %d route şablonu yüklendi.", len(cache))
    return cache


# ── Mod 1: Embedding Tabanlı Hızlı Routing ───────────────────────────────────

def _mod1_route(text: str, base_url: str = OLLAMA_BASE_URL) -> tuple[str, float]:
    """Mod 1: nomic-embed-text kosinüs benzerliği ile route seç.

    Returns:
        (route_name, confidence_score)
        confidence = en yüksek kosinüs benzerliği (0.0 - 1.0)
    """
    templates = _get_template_embeddings(base_url)
    if not templates:
        return "persona", 0.0  # Şablon yoksa varsayılan

    query_vec = _embed(text, base_url)
    if not query_vec:
        return "persona", 0.0

    best_route = "persona"
    best_score = -1.0

    for route, tmpl_vec in templates.items():
        score = _cosine_similarity(query_vec, tmpl_vec)
        if score > best_score:
            best_score = score
            best_route = route

    logger.debug("Mod 1 → route='%s', confidence=%.3f", best_route, best_score)
    return best_route, best_score


# ── Mod 2: Qwen 0.5B Niyet Ayrıştırması ──────────────────────────────────────

def _qwen_decompose(text: str, base_url: str = OLLAMA_BASE_URL) -> list[str]:
    """Qwen 2.5 0.5B ile karmaşık girdiyi niyet ifadelerine parçalar.

    OLLAMA_LOCK dışında çalışır — routing çağrısı generate() öncesi yapılır.
    keep_alive: -1 ile Qwen kalıcı bellekte tutulur (soğuk başlatma yok).
    """
    system = (
        "Sen bir niyet ayrıştırıcısın. Kullanıcı girdisini maksimum 3 kısa niyet ifadesine böl.\n"
        "Her niyet ifadesi 5-10 kelime olmalı. JSON listesi döndür.\n"
        'Örnek: ["pazar araştırması ürün fikri", "fiyat hassasiyeti hedef kitle", "A/B test varyant"]\n'
        "SADECE JSON listesi döndür, açıklama yapma."
    )
    payload = json.dumps({
        "model": QWEN_MODEL_ID,
        "prompt": text,
        "system": system,
        "stream": False,
        "options": {
            "temperature": 0.1,
            "num_predict": 128,
            "num_ctx": 512,
        },
        "keep_alive": -1,
    }).encode("utf-8")

    try:
        url = f"{base_url.rstrip('/')}/api/generate"
        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=QWEN_TIMEOUT) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            response_text = data.get("response", "").strip()

        # JSON listesini çıkar
        match = re.search(r"\[.*?\]", response_text, re.DOTALL)
        if match:
            intents = json.loads(match.group())
            if isinstance(intents, list):
                logger.debug("Mod 2 niyet ayrıştırma → %s", intents)
                return [str(i) for i in intents[:3]]
    except Exception as exc:
        logger.debug("Mod 2 Qwen ayrıştırma başarısız: %s", exc)

    return []


def _mod2_route(text: str, base_url: str = OLLAMA_BASE_URL) -> tuple[str, float]:
    """Mod 2: Qwen ile ayrıştırılan intentler üzerinde Mod 1 uygula.

    Her intent ifadesi için Mod 1 çalıştırılır, oylama ile kazanan seçilir.
    """
    intents = _qwen_decompose(text, base_url)
    if not intents:
        return "persona", 0.0

    votes: dict[str, float] = {}
    for intent in intents:
        route, score = _mod1_route(intent, base_url)
        votes[route] = votes.get(route, 0.0) + score

    best_route = max(votes, key=lambda r: votes[r])
    best_score = votes[best_route] / len(intents)
    logger.debug("Mod 2 → route='%s', avg_score=%.3f, votes=%s", best_route, best_score, votes)
    return best_route, best_score


# ── Keyword Fallback ──────────────────────────────────────────────────────────

def _keyword_fallback(system: str, prompt: str) -> str:
    """Mevcut keyword eşleşme mantığı — Mod 1 ve Mod 2 başarısız olursa devreye girer."""
    text = (system + " " + prompt).lower()
    if any(kw in text for kw in ["defne", "araştırma mimarı", "intake", "brief"]):
        return "orchestrator"
    if any(kw in text for kw in ["sentez", "rapor sentezi", "b2b analist", "sentezleyici", "analiz"]):
        return "synthesis"
    return "persona"


# ── Ana Router ────────────────────────────────────────────────────────────────

def route(system: str, prompt: str, base_url: str = OLLAMA_BASE_URL) -> str:
    """Üç kademeli semantic routing kararı verir.

    1. Mod 1 (nomic-embed): hızlı, güvenilir
       → confidence ≥ CONFIDENCE_THRESHOLD ise karar ver
    2. Mod 2 (Qwen 0.5B): karmaşık girdiler için niyet ayrıştırma
       → confidence ≥ CONFIDENCE_THRESHOLD ise karar ver
    3. Keyword fallback: her zaman bir cevap üretir

    Args:
        system: LLM sistem promptu
        prompt: Kullanıcı girdisi
        base_url: Ollama sunucu adresi

    Returns:
        "orchestrator" | "synthesis" | "persona"
    """
    combined = f"{system} {prompt}".strip()

    # Mod 1
    try:
        route_m1, score_m1 = _mod1_route(combined, base_url)
        if score_m1 >= CONFIDENCE_THRESHOLD:
            logger.debug("SemanticRouter: Mod 1 karar verdi → '%s' (%.3f)", route_m1, score_m1)
            return route_m1
        logger.debug("SemanticRouter: Mod 1 belirsiz (%.3f < %.2f) → Mod 2", score_m1, CONFIDENCE_THRESHOLD)
    except Exception as exc:
        logger.warning("SemanticRouter: Mod 1 hatası: %s", exc)

    # Mod 2
    try:
        route_m2, score_m2 = _mod2_route(combined, base_url)
        if score_m2 >= CONFIDENCE_THRESHOLD:
            logger.debug("SemanticRouter: Mod 2 karar verdi → '%s' (%.3f)", route_m2, score_m2)
            return route_m2
        logger.debug("SemanticRouter: Mod 2 de belirsiz (%.3f) → Keyword fallback", score_m2)
    except Exception as exc:
        logger.warning("SemanticRouter: Mod 2 hatası: %s", exc)

    # Keyword fallback
    result = _keyword_fallback(system, prompt)
    logger.debug("SemanticRouter: Keyword fallback → '%s'", result)
    return result


def reset_template_cache() -> None:
    """Şablon önbelleğini sıfırlar (test veya hot-reload için)."""
    global _template_cache
    _template_cache = None
