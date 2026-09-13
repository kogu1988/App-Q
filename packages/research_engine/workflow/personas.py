"""Persona uretimi ve bio zenginlestirme (R8-2)."""
from __future__ import annotations

import json
import logging
import os
import random
import re
import uuid
from collections.abc import Generator
from dataclasses import replace
from typing import Any, Dict, List, Optional

from packages.research_engine.nodes.culture import (
    HOFSTEDE_TURKEY,
    HOFSTEDE_TURKEY_PROMPT,
    SES_PROFILES,
    TUAD_SES_QUOTA,
    apply_ses_quota,
    get_turkey_behavior_context,
)

# Import modular components for clean structure and delegation
from packages.research_engine.nodes.memory import (
    calculate_act_r_memory_prompt,
    summarize_turns_if_needed,
)
from packages.research_engine.nodes.probe import (
    generate_probe_question,
    jaccard_similarity,
    should_probe,
)
from packages.research_engine.nodes.sycophancy import (
    build_elephant_system_prompt,
    handle_zero_sum_bet,
    judge_answer_quality,
)

from ..database import get_system_config, log_audit
from ..models import (
    DEFAULT_STANCE_COHORT,
    STANCE_PROFILE,
    ClarifyingQuestion,
    InterviewQuestion,
    InterviewTurn,
    PanelRole,
    Persona,
    PersonaInterview,
    ResearchBrief,
    ResearchModel,
    ResearchPlan,
    RespondentType,
)
from ..quality import calculate_ewma, calculate_turn_quality, detect_echo

logger = logging.getLogger(__name__)

from ._constants import DEFAULT_TRAIT_ORDER


def persona_traits(seed: int, stance: str, price_sensitivity: int, digital_confidence: int) -> dict[str, int]:
    """Big Five domain skorlarını Rogers Diffusion stance profiliyle kalibre eder.
    Agreeableness prensibi:
      base=60 + stance_modifier + küçük varyasyon (+/-6)
      modifier büyüklüğü (min 4, max 10) > max varyasyon (6) olduğu için
      Skeptic her zaman Mainstream'den düşük Agreeableness puanına sahip olur.
    Openness prensibi:
      Stance modifier birincil sürücüdür (Innovator +12 ... Laggard -8);
      digital_confidence ikincil etki olarak merkezlenmiş şekilde (dc-5)*3 eklenir.
    """
    profile = STANCE_PROFILE.get(stance, STANCE_PROFILE["Mainstream"])
    var = (seed * 7 % 13) - 6

    agreeableness = 60 + profile["agreeableness_mod"] + var

    # Openness: stance baskın; digital_confidence merkezlenmiş ikincil etki
    openness = 52 + (digital_confidence - 5) * 3 + ((seed * 3 % 12) - 6) + profile["openness_mod"]
    conscientiousness = 62 + (seed * 7 % 28)
    extraversion = 42 + (seed * 5 % 35)
    neuroticism = min(88, max(25, price_sensitivity * 7 + (seed * 4 % 18)))

    neuroticism = min(100, max(1, neuroticism + profile["neuroticism_mod"]))

    return {
        "Openness":          min(92, max(20, openness)),
        "Conscientiousness": min(100, max(1, conscientiousness)),
        "Extraversion":      min(100, max(1, extraversion)),
        "Agreeableness":     min(100, max(1, agreeableness)),
        "Neuroticism":       min(100, max(1, neuroticism)),
    }

def neo_facets_from_traits(traits: dict[str, int], stance: str) -> dict[str, int]:
    """Big Five domain skorlarından NEO-PI-R facet yaklaşımsalı üret."""
    profile = STANCE_PROFILE.get(stance, STANCE_PROFILE["Mainstream"])
    evidence_mod = profile["evidence_need"]
    facets: dict[str, int] = {}
    
    o = traits.get("Openness", 60)
    facets["O1_Fantasy"] = min(100, o + 5)
    facets["O2_Aesthetics"] = min(100, o - 3)
    facets["O3_Feelings"] = min(100, o + evidence_mod * 2)
    facets["O4_Actions"] = min(100, o - evidence_mod * 3)
    facets["O5_Ideas"] = min(100, o + 8)
    facets["O6_Values"] = min(100, o - 5)
    
    n = traits.get("Neuroticism", 50)
    facets["N1_Anxiety"] = min(100, n + evidence_mod * 2)
    facets["N2_Anger"] = min(100, n - 5)
    facets["N3_Depression"] = min(100, n - 10)
    facets["N4_SelfConsciousness"] = min(100, n + 3)
    facets["N5_Impulsiveness"] = min(100, max(1, 60 - n + evidence_mod))
    facets["N6_Vulnerability"] = min(100, n + evidence_mod)
    
    return {k: max(1, v) for k, v in facets.items()}

def persona_attributes(
    segment: str,
    stance: str,
    price_sensitivity: int,
    digital_confidence: int,
) -> dict[str, str]:
    return {
        "Hobbies": "Mobil uygulama denemek, kısa video içerikleri izlemek, hafta sonu şehir içi keşifler",
        "Origin country": "Türkiye",
        "Current workflow": "Notlar, Excel/Google Sheets, WhatsApp grupları ve birkaç parçalı SaaS aracı",
        "Decision trigger": "Somut zaman veya para tasarrufu görürse denemeye yaklaşır",
        "Buying friction": "Gizli ücret, uzun kurulum, belirsiz veri kullanımı ve kanıtlanmamış vaatler",
        "Price posture": "Çok hassas" if price_sensitivity >= 8 else "Kanıt görürse ödeme yapabilir",
        "Digital confidence": "Yüksek" if digital_confidence >= 8 else "Orta",
        "Segment role": segment,
        "Research stance": stance,
    }

def generate_personas(
    brief: ResearchBrief,
    panel_roles: list[PanelRole] | None = None,
    model: ResearchModel | None = None,
    panel_size: int = 5,
) -> list[Persona]:
    if panel_roles:
        return generate_personas_from_roles(brief, panel_roles, model)

    market = brief.market or "Türkiye"
    from collections import Counter

    from ..matrix import allocate_cohort_matrix

    panel_size = max(1, int(panel_size))
    allocations = allocate_cohort_matrix(panel_size)

    # Stance diversity garantisi: N >= 5 ise 5 Rogers duruşunun tamamı bulunmalı.
    stances_present = set(a["stance"] for a in allocations)
    target_stances = ["Innovator", "EarlyAdopter", "Mainstream", "Laggard", "Skeptic"]
    if len(stances_present) < 5 and len(allocations) >= len(target_stances):
        counts = Counter(a["stance"] for a in allocations)
        for target in target_stances:
            if counts.get(target, 0) > 0:
                continue
            donor = max(counts.items(), key=lambda kv: kv[1])[0]
            if donor != target and counts[donor] > 1:
                for a in allocations:
                    if a["stance"] == donor:
                        a["stance"] = target
                        break
                counts[donor] -= 1
                counts[target] = counts.get(target, 0) + 1
    elif len(stances_present) < 5:
        # Küçük panellerde de en az 3 farklı duruş ve Skeptic korunur.
        for i, target in enumerate(target_stances):
            if i < len(allocations):
                allocations[i]["stance"] = target
    
    personas: list[Persona] = []
    
    SES_SEGMENTS = {
        "AB": ["Üst Düzey Yönetici", "Beyaz Yaka Profesyonel", "Girişimci"],
        "C1": ["Orta Düzey Uzman", "KOBİ Çalışanı", "Serbest Çalışan"],
        "C2": ["Esnaf", "Teknisyen", "Mavi Yaka Ustabaşı"],
        "DE": ["Öğrenci", "Emekli", "Yarı Zamanlı Çalışan"],
    }
    # 10 kişilik standart panele kadar isim/şehir/bağlam havuzu (fazlası modülo ile).
    NAMES = [
        "Ahmet", "Ayşe", "Mehmet", "Zeynep", "Mustafa",
        "Elif", "Emre", "Selin", "Burak", "Deniz",
    ]
    CITIES = [
        "İstanbul", "Ankara", "İzmir", "Bursa", "Antalya",
        "Adana", "Konya", "Gaziantep", "Kayseri", "Eskişehir",
    ]
    CONTEXTS = [
        f"{market} pazarında yeni ürünleri denemeye açık.",
        f"{market} pazarında fiyat-performans odaklı.",
        f"{market} pazarında güvenilir çözümler arıyor.",
        f"{market} pazarında mevcut alternatifleri değerlendiriyor.",
        f"{market} pazarında yeniliklere temkinli yaklaşıyor.",
        f"{market} pazarında satın alma öncesi kanıt ve referans arıyor.",
        f"{market} pazarında dijital araçlara mesafeli yaklaşıyor.",
        f"{market} pazarında hızlı sonuç ve kolay kurulum bekliyor.",
        f"{market} pazarında maliyet baskısıyla karar veriyor.",
        f"{market} pazarında deneyimini çevresiyle paylaşan bir profil.",
    ]
    
    for idx, alloc in enumerate(allocations):
        stance = alloc["stance"]
        ses = alloc.get("ses_group", "C1")
        ps = 3 + (idx % 7)
        dc = 4 + (idx % 6)
        tr = persona_traits(idx + 1, stance, ps, dc)
        segment = SES_SEGMENTS.get(ses, SES_SEGMENTS["C1"])[idx % 3]
        
        personas.append(Persona(
            id=f"p{idx + 1}",
            name=NAMES[idx % len(NAMES)],
            age=25 + (idx * 7) % 30,
            city=CITIES[idx % len(CITIES)],
            segment=segment,
            role_title=segment,
            stance=stance,
            price_sensitivity=ps,
            digital_confidence=dc,
            context=CONTEXTS[idx % len(CONTEXTS)],
            goals=["Ürünün faydasını değerlendirmek", "Fiyat-performans dengesini anlamak"],
            objections=["Değer önerisinin belirsizliği", "Alternatiflerin varlığı"],
            knowledge_boundary="Kendi deneyim ve alışkanlıkları hakkında konuşabilir.",
            bio=f"{segment} olarak {market} pazarında {stance} tutumuna sahip.",
            attributes=persona_attributes(segment, stance, ps, dc),
            traits=tr,
            big_five=tr,
            ses_group=ses,
            diffusion_stage=STANCE_PROFILE.get(stance, {}).get("tr_description", ""),
            neo_facets=neo_facets_from_traits(tr, stance),
        ))
    
    return personas

def enrich_persona_bios(
    personas: list[Persona],
    brief: ResearchBrief,
    model: ResearchModel | None = None,
    max_len: int = 700,
) -> list[Persona]:
    """Persona biyografilerini, deterministik alanlara bağlı kalarak LLM ile doğallaştırır.

    Anti-halüsinasyon: yalnızca verilen attribute'lardan yararlanır; yeni sayı, marka,
    kurum veya olay uydurması yasaklanır. LLM erişilemezse ya da çıktı geçersizse
    mevcut (şablon) biyografi korunur — akış asla çökmez.
    """
    if not personas or model is None:
        return personas
    try:
        market = brief.market or "Türkiye"
        catalog = []
        for p in personas:
            attrs = p.attributes or {}
            bf = p.big_five or {}
            bf_parts = [
                f"{label} {(bf.get(key) if bf.get(key) is not None else '?')}"
                for key, label in (
                    ("Openness", "Açıklık"),
                    ("Conscientiousness", "Sorumluluk"),
                    ("Extraversion", "Dışadönüklük"),
                    ("Agreeableness", "Uyumluluk"),
                    ("Neuroticism", "Duygusal dengesizlik"),
                )
            ]
            catalog.append(
                f"- id: {p.id}\n"
                f"  isim: {p.name}\n"
                f"  yaş: {p.age}\n"
                f"  şehir: {p.city}\n"
                f"  rol/segment: {p.role_title or p.segment}\n"
                f"  SES: {p.ses_group or 'C1'}\n"
                f"  Rogers duruşu: {p.stance}\n"
                f"  Rogers aşaması: {p.diffusion_stage or ''}\n"
                f"  Big Five (0-100, bilimsel atama — değiştirilemez): {', '.join(bf_parts)}\n"
                f"  fiyat hassasiyeti (0-10): {p.price_sensitivity}\n"
                f"  dijital güven (0-10): {p.digital_confidence}\n"
                f"  mevcut iş akışı: {attrs.get('Current workflow', '')}\n"
                f"  karar tetikleyicisi: {attrs.get('Decision trigger', '')}\n"
                f"  satın alma sürtünmesi: {attrs.get('Buying friction', '')}\n"
                f"  hobiler: {attrs.get('Hobbies', '')}"
            )
        system = (
            "Sen Clarere için persona biyografisi yazarsın. Verilen psikometrik profile (Big Five / Rogers) "
            f"SADIK kalarak, {market} pazarına özgü, doğal ve akıcı üçüncü şahıs biyografiler yaz. "
            "Verilmeyen sayı, marka, kurum, iş yeri veya olay uydurma. Yalnızca geçerli JSON döndür."
        )
        prompt = (
            f"Kategori: {brief.category or 'genel'}\n"
            f"Ürün fikri: {(brief.idea or '')[:400]}\n"
            f"Hedef kullanıcı: {', '.join(brief.target_users or [])[:300]}\n\n"
            "Aşağıdaki personaların her biri için 2-3 cümlelik, doğal akan, üçüncü şahıs bir biyografi yaz.\n"
            "Kurallar:\n"
            "- Yalnızca verilen alanları kullan; yeni sayı, isim, marka veya kurum uydurma.\n"
            "- Big Five / Rogers atamaları bilimseldir ve DEĞİŞTİRİLEMEZ. Biyografiyi bu profile göre kur; çeliştirme.\n"
            "- Psikometrik skorları sayı olarak yazma; bunları davranış ve tutum diline çevir "
            "(ör. Openness yüksek → yeni çözümleri denemeye istekli; Neuroticism yüksek → fiyat/risk kaygısı; "
            "Agreeableness düşük → şüpheci, itiraz etmeye hazır; Openness düşük → kanıtlanmış çözüm tercihi).\n"
            "- Rogers duruşunu doğal biçimde yansıt (Innovator → öncü, Skeptic → temkinli/kanıt arayan).\n"
            f"- {market} pazarı bağlamını koru (şehir, SES, TL).\n"
            "- Cümleler yarım kalmasın; üç nokta (...) kullanma.\n"
            "- Fiyat hassasiyeti yüksekse maliyet kaygısını, dijital güven düşükse adaptasyon zorluğunu yansıt.\n\n"
            "Personalar:\n" + "\n".join(catalog) + "\n\n"
            'Yalnızca şu formatta JSON döndür: {"bios": {"<id>": "<biyografi>"}}'
        )
        response_text = model.generate(system, prompt, response_format="json")
        parsed = json.loads(response_text)
        bios = parsed.get("bios", parsed) if isinstance(parsed, dict) else {}
        if not isinstance(bios, dict):
            return personas
        enriched: list[Persona] = []
        updated = 0
        for p in personas:
            candidate = bios.get(p.id)
            if isinstance(candidate, str):
                text = candidate.strip()
                if 60 <= len(text) <= max_len and "..." not in text and "…" not in text:
                    enriched.append(replace(p, bio=text))
                    updated += 1
                    continue
            enriched.append(p)
        logger.debug("Persona biyografileri doğallaştırıldı: %s/%s", updated, len(personas))
        return enriched
    except Exception:
        logger.debug("Persona biyografi zenginleştirme başarısız; şablon bio korundu.", exc_info=True)
    return personas

def generate_personas_from_roles(brief: ResearchBrief, panel_roles: list[PanelRole], model: ResearchModel | None = None) -> list[Persona]:
    from packages.research_engine.db_vectors import get_personas_from_pool_by_role
    from packages.research_engine.matrix import allocate_cohort_matrix

    market = brief.market or "Türkiye"
    personas: list[Persona] = []
    
    total_needed = 0
    role_needs = []
    for role in panel_roles:
        if role.count <= 0:
            continue
        pooled_data = get_personas_from_pool_by_role(role.role, limit=role.count)
        needed = role.count - len(pooled_data)
        role_needs.append({"role": role, "pooled": pooled_data, "needed": needed})
        total_needed += needed

    matrix_allocations = allocate_cohort_matrix(total_needed)

    for item in role_needs:
        role = item["role"]
        pooled_data = item["pooled"]
        needed_count = item["needed"]
        
        for data in pooled_data:
            personas.append(
                Persona(
                    id=data["id"],
                    name=data["name"],
                    age=data["age"],
                    city=data["city"],
                    segment=data["segment"],
                    role_title=data["role_title"],
                    stance=data["stance"],
                    price_sensitivity=data["price_sensitivity"],
                    digital_confidence=data["digital_confidence"],
                    context=data["context"],
                    goals=data["goals"],
                    objections=data["objections"],
                    knowledge_boundary=data["knowledge_boundary"],
                    country_code=data["country_code"],
                    origin_country=data["origin_country"],
                    bio=data["bio"],
                    attributes=data["attributes"],
                    traits=data["traits"],
                    big_five=data.get("big_five", {})
                )
            )
            
        if needed_count > 0:
            # Embedding tabanli persona eslestirme devre disi (Enterprise'ta geri gelecek)
            # Dogrudan yeni persona uret
            loaded_ids = {p.id for p in personas}
            
            # Fallback: fresh persona generation
            while needed_count > 0:
                index = len(personas)
                fallback_stance = DEFAULT_STANCE_COHORT[index % len(DEFAULT_STANCE_COHORT)]
                new_id = f"p_{uuid.uuid4().hex[:8]}"
                fallback_traits = persona_traits(index, fallback_stance, 6, 7)
                p = Persona(
                    id=new_id,
                    name=f"Kullanıcı {index}",
                    age=30 + (index % 15),
                    city="İstanbul",
                    segment=role.role,
                    role_title=role.role,
                    stance=fallback_stance,
                    price_sensitivity=6,
                    digital_confidence=7,
                    context=f"{market} pazarında {role.role} rolünü temsil eder.",
                    goals=["Ürünün faydasını anlamak"],
                    objections=["Değer önerisinin belirsizliği"],
                    knowledge_boundary="Kendi rolü hakkında konuşabilir.",
                    bio=f"{role.role} rolünde Türkiye pazarı katılımcısı.",
                    attributes=persona_attributes(role.role, fallback_stance, 6, 7),
                    traits=fallback_traits,
                    diffusion_stage=STANCE_PROFILE.get(fallback_stance, {}).get("tr_description", ""),
                    neo_facets=neo_facets_from_traits(fallback_traits, fallback_stance),
                )
                personas.append(p)
                needed_count -= 1
            
    return personas
