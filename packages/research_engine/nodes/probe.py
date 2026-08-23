"""
Adaptive Probe Engine — Sprint 3.

Algorithmic (non-LLM) heuristics to decide whether a follow-up probe
is warranted, and template-based generation of evidence-seeking probe
questions in Turkish.

Design principles:
- Probes ask for SPECIFIC evidence, not generic "why?"
- Maximum 1 probe per question, 3 total per interview
- If probe answer is too similar to original (Jaccard > 0.7), discard
"""

from __future__ import annotations

import re
import random


# ---------------------------------------------------------------------------
# Pricing keywords (Turkish)
# ---------------------------------------------------------------------------
PRICING_KEYWORDS: list[str] = [
    "pahalı", "ucuz", "fiyat", "tl", "lira", "bütçe", "ücret",
    "abonelik", "maliyet", "öde", "ödeme", "parası", "paraya",
    "taksit", "komisyon", "kargo",
]

TL_PATTERN = re.compile(r"\d{1,6}\s*(?:TL|₺|lira|türk lirası)", re.IGNORECASE)

OBJECTION_KEYWORDS: list[str] = [
    "güvenmiyorum", "itiraz", "şüphe", "risk", "emin değil",
    "düşünmüyorum", "gerek yok", "ihtiyaç", "alternatif",
    "rakip", "kullanıyorum", "memnunum", "değiştirmem",
]

ALTERNATIVE_KEYWORDS: list[str] = [
    "alternatif", "yerine", "onun", "başka", "farklı",
    "rakip", "diğer", "mevcut", "kullandığım", "kullanıyorum",
    "var zaten", "benzer",
]


# ---------------------------------------------------------------------------
# Probe templates — Turkish, evidence-seeking
# ---------------------------------------------------------------------------
PROBE_TEMPLATES: dict[str, list[str]] = {
    "pricing": [
        "Pahalı derken hangi alternatifle karşılaştırıyorsun? Rakam verir misin?",
        "Senin için hangi fiyat aralığı makul olurdu? TL olarak söyler misin?",
        "Bu fiyata değmesi için hangi özellik olmazsa olmaz?",
        "Daha önce benzer bir ürün için ne kadar ödemiştin?",
    ],
    "objection": [
        "Bu endişeni gidermek için ne yapılması gerekir?",
        "Daha önce benzer bir durumda ne yapmıştın? Somut bir örnek verir misin?",
        "Güvenmen için ne olması lazım? Deneme süresi, referans, garanti?",
        "Hangi koşulda fikrin değişirdi?",
    ],
    "generic": [
        "Somut bir örnek verebilir misin? En son ne zaman böyle bir şey yaşadın?",
        "Bu konuda yaşadığın bir olayı kısaca anlatır mısın?",
        "Biraz daha açar mısın? Ne demek istediğini tam anlayamadım.",
        "Peki bu senin için neden önemli? Günlük hayatında nasıl etkiliyor?",
    ],
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def should_probe(answer: str, question_label: str = "") -> bool:
    """
    Determine if the answer warrants a follow-up probe.

    Returns True if the answer is:
    - Too short (< 30 chars)
    - Generic/vague (no specific details)
    - Contains ambiguous pricing signals
    - Contains interesting objections worth exploring
    - Merely "evet", "hayır", "belki"

    This is purely algorithmic — no LLM call.
    """
    stripped = answer.strip()

    # 1. Too short — no meaningful content to work with
    if len(stripped) < 30:
        return True

    # 2. One-word / minimal answers
    lower = stripped.lower()
    bare_responses = {"evet", "hayır", "belki", "evet.", "hayır.", "belki.",
                      "bilmiyorum", "bilmem", "yok", "var"}
    if lower.rstrip(".") in bare_responses:
        return True

    # 3. Pricing keywords present but no specific TL amount
    has_pricing_kw = any(kw in lower for kw in PRICING_KEYWORDS)
    has_tl_amount = bool(TL_PATTERN.search(stripped))
    if has_pricing_kw and not has_tl_amount:
        return True

    # 4. Objection keywords present but no alternative mentioned
    has_objection_kw = any(kw in lower for kw in OBJECTION_KEYWORDS)
    has_alternative_kw = any(kw in lower for kw in ALTERNATIVE_KEYWORDS)
    if has_objection_kw and not has_alternative_kw:
        return True

    return False


def generate_probe_question(
    answer: str,
    original_question: str,
    persona_stance: str = "",
) -> str:
    """
    Generate an evidence-seeking probe question based on the answer.

    Uses template-based selection (no LLM) to produce specific follow-ups
    like:
    - "Pahalı derken hangi alternatifle karşılaştırıyorsunuz?"
    - "Hangi özellik olmazsa olmaz sizin için?"
    - "Daha önce benzer bir ürün kullandınız mı? Deneyiminiz nasıldı?"

    Categorises answers into pricing, objection, or generic, then picks
    a template from the matching pool.
    """
    lower = answer.lower()

    # Determine category
    has_pricing = any(kw in lower for kw in PRICING_KEYWORDS)
    has_objection = any(kw in lower for kw in OBJECTION_KEYWORDS)

    if has_pricing:
        category = "pricing"
    elif has_objection:
        category = "objection"
    else:
        category = "generic"

    templates = PROBE_TEMPLATES.get(category, PROBE_TEMPLATES["generic"])
    chosen = random.choice(templates)

    # Adjust for Skeptic/Laggard stances — more direct challenge
    if persona_stance in {"Skeptic", "Laggard"}:
        # Templates are already evidence-seeking; no softening needed for skeptics
        pass

    return chosen


def jaccard_similarity(text_a: str, text_b: str) -> float:
    """
    Compute Jaccard similarity coefficient between two strings.

    Returns a float in [0.0, 1.0].  Values > 0.7 indicate the probe
    answer is too similar to the original and should be discarded.
    """
    if not text_a or not text_b:
        return 0.0

    def tokenize(text: str) -> set[str]:
        return set(re.findall(r"\w+", text.lower()))

    set_a = tokenize(text_a)
    set_b = tokenize(text_b)

    union = set_a | set_b
    if not union:
        return 0.0

    intersection = set_a & set_b
    return len(intersection) / len(union)
