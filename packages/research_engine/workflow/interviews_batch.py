"""Mulakat yurutumu (batch) + tur yenileme (R8-3)."""
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

from .interviews import classify_question
from .planning import _format_ab_question, generate_interview_script


def _skipped_interview(persona: Persona, script: list[InterviewQuestion]) -> PersonaInterview:
    """Süre bütçesi aşıldığında kalan personalar için boş mülakat üretir (P0-5)."""
    turns = [
        InterviewTurn(
            question=sq.question,
            answer="[Yanıt alınamadı]",
            tags=sq.tags or classify_question(sq.question),
            model_id=None,
            quality_flags=["timeout"],
        )
        for sq in script
    ]
    return PersonaInterview(
        persona=persona,
        turns=turns,
        consistency_notes=[
            "Süre bütçesi (RESEARCH_DEADLINE_SECONDS) aşıldı — mülakat çalıştırılmadı."
        ],
    )

def run_interviews_batch(
    brief: ResearchBrief,
    personas: list[Persona],
    model: ResearchModel,
    interview_script: list[InterviewQuestion] | None = None,
) -> list[PersonaInterview]:
    """
    Batch interview: her persona için TÜM soruları tek bir API çağrısında JSON array olarak alır.
    Soru başına ayrı çağrı yapmaz — maliyet ve süre avantajı sağlar.
    """
    interviews: list[PersonaInterview] = []
    script = interview_script or generate_interview_script(brief)

    # ── Süre bütçesi (P0-5): aşılırsa kalan personalar atlanır ──
    import time as _time
    _deadline: float | None = None
    try:
        _deadline_seconds = float(os.getenv("RESEARCH_DEADLINE_SECONDS", "300"))
        if _deadline_seconds > 0:
            _deadline = _time.monotonic() + _deadline_seconds
    except (TypeError, ValueError):
        _deadline = None

    try:
        config = get_system_config()
        db_prompt = config.get("persona_interview_prompt")
    except Exception:
        logger.warning("system_config fetch failed (batch), using default persona prompt", exc_info=True)
        db_prompt = None

    # Soru listesini numaralı formata çevir (AB_TEST hariç — kişiye özel aşağıda)
    non_ab_questions = [sq for sq in script if sq.label != "AB_TEST"]
    has_ab = any(sq.label == "AB_TEST" for sq in script) and brief.variant_a and brief.variant_b

    for persona_idx, persona in enumerate(personas):
        # Süre bütçesi aşıldıysa: kullanıcıyı daha fazla bekletme, kalanları boş mülakatla doldur.
        if _deadline is not None and _time.monotonic() > _deadline:
            logger.warning(
                "Araştırma süre bütçesi aşıldı — %d persona atlanıyor (indeks %d).",
                len(personas) - persona_idx, persona_idx,
            )
            for skipped in personas[persona_idx:]:
                interviews.append(_skipped_interview(skipped, script))
            break

        system_prompt = db_prompt if db_prompt else build_elephant_system_prompt(persona, brief.hypothesis_blind)

        # Sprint 5 — A/B soru metnini kişiye özel randomize et (batch için)
        ab_question_text: str | None = None
        ab_mapping: str | None = None
        if has_ab:
            ab_question_text, ab_mapping = _format_ab_question(brief, persona_idx)

        # Soru bloğunu kişiye özel oluştur (AB sorusu varsa ekle)
        questions_block = ""
        for i, sq in enumerate(non_ab_questions, start=1):
            questions_block += f"{i}. [{sq.label}] {sq.question}\n"
        if ab_question_text:
            ab_num = len(non_ab_questions) + 1
            questions_block += f"{ab_num}. [AB_TEST] {ab_question_text}\n"

        turkey_context = get_turkey_behavior_context(persona, script[0])

        # ── Hypothesis-Blind Context (Grounded Simulation §4.3) ──
        if brief.hypothesis_blind:
            product_desc = brief.idea or f"{brief.category} kategorisinde bir ürün"
            research_context_block = (
                f"[BAĞLAM]\n"
                f"Şu ürün/hizmet hakkında görüşlerin sorulacak:\n"
                f"{product_desc}\n\n"
                f"Sana sorulan soruları kendi deneyimlerine ve alışkanlıklarına göre yanıtla.\n"
                f"Bu ürün hakkında ne düşündüğünü bilmek istiyoruz; doğru/yanlış cevap yok.\n\n"
            )
        else:
            research_context_block = (
                f"[ARAŞTIRMA KONUSU]\n"
                f"{brief.idea}\n\n"
            )

        prompt = (
            f"[KİMLİĞİN]\n"
            f"{persona.name}, {persona.age} yaş, {persona.city} — {persona.segment}\n"
            f"Ekonomik Grup: {persona.ses_group} | Tutum: {persona.stance}\n"
            f"Fiyat Hassasiyeti: {persona.price_sensitivity}/10 | Dijital Özgüven: {persona.digital_confidence}/10\n"
            f"Katılımcı Tipi: {persona.respondent_type} | Yerleşim: {persona.settlement_type}\n"
            f"Bağlam: {persona.context}\n"
            f"Hedeflerin: {', '.join(persona.goals) if persona.goals else 'Belirtilmedi'}\n"
            f"İtirazların: {', '.join(persona.objections) if persona.objections else 'Belirtilmedi'}\n"
            f"{turkey_context}\n\n"
            f"{research_context_block}"
            f"[SORULAR]\n"
            f"{questions_block}\n"
            f"[GÖREV]\n"
            f"Yukarıdaki kimliğe girerek her soruyu 2-4 cümle ile yanıtla.\n"
            f"- Birinci tekil şahıs kullan, Türkiye gerçeklerine bağlı kal (TL, taksit, KVKK).\n"
            f"- Dürüst ol; ürünü beğenmek zorunda değilsin.\n"
            f"- ÖZGÜNLÜK: Kendi hayatına özgü SOMUT detaylar ver (kendi durumun, kendi olayın, kendi rakamların).\n"
            f"  Başka katılımcıların kullanabileceği klişe örnekleri tekrar etme; jenerik ifadelerden kaçın.\n"
            f"- ROLDE KAL: Yapay zeka/asistan olduğunu asla ima etme, ürünü pazarlama diliyle övme;\n"
            f"  gerçek bir kullanıcı gibi kendi deneyiminden konuş.\n"
            f"- ZORUNLU: Yanıtını şu JSON dizisi olarak ver, başka hiçbir metin ekleme:\n"
            f'[{{"label": "SORU_ETIKETI", "answer": "..."}}, ...]\n'
        )

        # Batch interview — retry loop (DeepSeek JSON mode may rarely return empty)
        answers: dict[str, str] = {}
        batch_attempt = 0
        max_batch_attempts = 3
        expected_labels = {sq.label.upper() for sq in script}
        
        for batch_attempt in range(max_batch_attempts):
            missing_labels = expected_labels - set(answers.keys())
            if not missing_labels:
                break

            current_prompt = prompt
            if batch_attempt > 0:
                # Retry: sadece eksik soruları hedefle
                missing_block = "\n".join(f"{i}. [{lbl}] ..." for i, lbl in enumerate(sorted(missing_labels), 1))
                current_prompt = prompt + (
                    f"\n\n[UYARI: BAZI SORULARA CEVAP VERILMEDI]\n"
                    f"Su etiketli sorulara MUTLAKA cevap ver: {sorted(missing_labels)}\n"
                    "- Asistan/yapay zeka oldugunu asla belli etme.\n"
                    "- Tum sorulari birinci tekil sahis olarak, 2-4 cumleyle cevapla.\n"
                    "- Turkiye gerceklerine bagli kal: TL, taksit, KVKK, kargo.\n"
                    "- Eger skeptik bir karaktersen urunu elestirmekten ve reddetmekten cekinme.\n"
                )
            
            raw = model.generate(system_prompt, current_prompt)

            if not raw or raw.strip() == "":
                logger.warning(f"Batch empty response for {persona.name} (attempt {batch_attempt+1}), retrying...")
                continue

            try:
                clean = re.sub(r'```(?:json)?\s*|```', '', raw)
                match = re.search(r'\[.*\]', clean, re.DOTALL)
                if match:
                    parsed = json.loads(match.group(0))
                    for item in parsed:
                        lbl = item.get("label", "").upper()
                        ans = item.get("answer", "")
                        if lbl and ans and lbl not in answers:
                            answers[lbl] = ans
            except (json.JSONDecodeError, Exception) as e:
                logger.warning(f"Batch parse failed for {persona.name} (attempt {batch_attempt+1}): {e}")

            still_missing = expected_labels - set(answers.keys())
            if still_missing:
                logger.warning(f"Batch partial answers for {persona.name} (attempt {batch_attempt+1}): missing {sorted(still_missing)}, raw[:150]={raw[:150]}")

        # ── Bilimsel Kalite Kontrolü (Grounded Simulation §5) ──
        turns: list[InterviewTurn] = []
        answers_list: list[str] = []  # Echo detection için sıralı cevaplar
        total_flags = 0
        critical_failures = 0
        
        for sq in script:
            # Sprint 5 — A/B sorusu için kişiye özel metni kullan
            sq_question = ab_question_text if (sq.label == "AB_TEST" and ab_question_text) else sq.question
            ans = answers.get(sq.label.upper(), "[Yanıt alınamadı]")
            quality_flags = list(judge_answer_quality(persona, sq_question, ans))
            
            # ── Intra-Persona Echo Detection (Jaccard, god_doc.md §5.3) ──
            if len(answers_list) >= 1:
                # Son cevapla şimdiki cevap arasında echo kontrolü
                if detect_echo(ans, answers_list[-1]):
                    quality_flags.append("echo_detected")
            answers_list.append(ans)
            
            # ── Acquiescence Detection (god_doc.md §5.1) ──
            from ..quality import detect_acquiescence
            if persona.stance in {"Skeptic", "Laggard"}:
                if detect_acquiescence(persona.stance, [ans]):
                    quality_flags.append("acquiescence_bias")
            
            total_flags += len(quality_flags)
            if any(f in {"meta_tone", "visible_reasoning", "sycophancy_detected"} for f in quality_flags):
                critical_failures += 1

            turns.append(InterviewTurn(
                question=sq_question,
                answer=ans,
                tags=sq.tags or classify_question(sq_question),
                model_id=getattr(model, "last_model_id", None),
                quality_flags=quality_flags,
            ))
        
        # ── Batch Quality Score (Grounded Simulation §5 EWMA eşdeğeri) ──
        answered_count = len([t for t in turns if t.answer != "[Yanıt alınamadı]"])
        total_questions = len(script)
        flag_rate = total_flags / max(total_questions, 1)
        
        # Kalite skoru: 1.0 = mükemmel, <0.5 = zayıf
        quality_score = max(0.0, 1.0 - (flag_rate * 0.5) - (critical_failures * 0.15))

        consistency_notes = [
            f"Persona stance: {persona.stance}",
            f"Bilgi sınırı: {persona.knowledge_boundary}",
            f"Batch interview — {answered_count}/{total_questions} yanıt alındı",
            f"Kalite skoru: {quality_score:.2f} | Flag sayısı: {total_flags} | Kritik hata: {critical_failures}",
        ]
        if ab_mapping:
            consistency_notes.append(ab_mapping)
        
        # Stance uyumluluk notu (Grounded Simulation §4.3)
        if persona.stance == "Skeptic":
            has_objection = any(
                any(kw in t.answer.lower() for kw in ["güvenmiyorum", "şüphe", "risk", "pahalı", "kanıt", "itiraz", "emin değilim"])
                for t in turns
            )
            if not has_objection:
                consistency_notes.append("UYARI: Skeptic persona yeterince itiraz üretmedi — stance uyumsuzluğu.")

        interviews.append(PersonaInterview(
            persona=persona,
            turns=turns,
            consistency_notes=consistency_notes,
        ))

    # ── P2-1: Cross-persona echo (kişiler arası yankı) düzeltmesi ──
    # Farklı personalar aynı klişe örneği (ör. aynı evcil hayvan adı) ürettiyse,
    # yankılanan personaları 'kaçın' listesiyle 1 kez yeniden üret.
    try:
        from ..quality import detect_cross_persona_echo

        echo = detect_cross_persona_echo(interviews)
        echoing = echo.get("echoing_persona_ids") or []
        shared = echo.get("shared_tokens") or []
        if echoing and shared:
            logger.warning(
                "Cross-persona echo: %d persona, ortak ornekler=%s",
                len(echoing), shared[:6],
            )
            by_id = {iv.persona.id: iv for iv in interviews}
            regenerated = 0
            for pid in echoing[:3]:
                if _deadline is not None and _time.monotonic() > _deadline:
                    logger.warning("Sure butcesi — kalan echo yeniden uretimi atlandi.")
                    break
                iv = by_id.get(pid)
                if iv is None:
                    continue
                sys_prompt = db_prompt if db_prompt else build_elephant_system_prompt(iv.persona, brief.hypothesis_blind)
                new_turns = _regen_persona_turns(brief, iv.persona, script, model, sys_prompt, shared)
                if new_turns:
                    iv.turns = new_turns
                    iv.consistency_notes.append("Cross-persona echo yeniden uretimi uygulandi.")
                    regenerated += 1
            logger.info("Cross-persona echo: %d persona yeniden uretildi", regenerated)
    except Exception:
        logger.warning("Cross-persona echo duzeltmesi atlandi", exc_info=True)

    return interviews

def _regen_persona_turns(
    brief: ResearchBrief,
    persona: Persona,
    script: list[InterviewQuestion],
    model: ResearchModel,
    system_prompt: str,
    avoid_terms: list[str],
) -> list[InterviewTurn]:
    """Cross-persona echo sonrası TEK persona için cevapları yeniden üretir.

    Diğer personaların kullandığı ortak örnek/klişeler 'kaçın' listesi olarak
    verilir; başarısız/eksik olursa boş liste döner (mevcut cevaplar korunur).
    """
    if not script:
        return []

    questions_block = "\n".join(
        f"{i}. [{sq.label}] {sq.question}" for i, sq in enumerate(script, 1)
    )
    avoid_block = ""
    if avoid_terms:
        avoid_block = (
            "[ÖZGÜNLÜK ZORUNLULUĞU]\n"
            "Aşağıdaki örnek/klişeler BAŞKA katılımcılar tarafından kullanıldı; SEN KULLANMA:\n"
            + "\n".join(f"- {t}" for t in avoid_terms[:12])
            + "\nKendi hayatına özgü, tamamen farklı isim/olay/rakam uydur.\n\n"
        )

    prompt = (
        f"[KİMLİĞİN]\n"
        f"{persona.name}, {persona.age} yaş, {persona.city} — {persona.segment}\n"
        f"Ekonomik Grup: {persona.ses_group} | Tutum: {persona.stance}\n"
        f"Fiyat Hassasiyeti: {persona.price_sensitivity}/10 | Dijital Özgüven: {persona.digital_confidence}/10\n"
        f"Bağlam: {persona.context}\n\n"
        f"{avoid_block}"
        f"[SORULAR]\n{questions_block}\n\n"
        f"[GÖREV]\nHer soruyu 2-4 cümleyle, birinci tekil şahıs olarak yanıtla. "
        f"Asistan gibi konuşma, ürünü pazarlama diliyle övme; kendi deneyiminden konuş. "
        f"Sadece şu JSON dizisini döndür:\n"
        f'[{{"label": "SORU_ETIKETI", "answer": "..."}}, ...]\n'
    )

    try:
        raw = model.generate(system_prompt, prompt)
    except Exception:
        logger.warning("Echo yeniden uretimi basarisiz", exc_info=True)
        return []
    if not raw:
        return []

    clean = re.sub(r'```(?:json)?\s*|```', '', raw)
    match = re.search(r'\[.*\]', clean, re.DOTALL)
    if not match:
        return []
    try:
        parsed = json.loads(match.group(0))
    except Exception:
        return []

    by_label: dict[str, str] = {}
    for item in parsed:
        lbl = str(item.get("label", "")).upper()
        ans = item.get("answer") or ""
        if lbl and ans:
            by_label[lbl] = ans

    turns: list[InterviewTurn] = []
    for sq in script:
        ans = by_label.get(sq.label.upper())
        if not ans:
            return []  # eksik → mevcut cevapları koru
        flags = list(judge_answer_quality(persona, sq.question, ans))
        turns.append(InterviewTurn(
            question=sq.question,
            answer=ans,
            tags=sq.tags or classify_question(sq.question),
            model_id=getattr(model, "last_model_id", None),
            quality_flags=flags,
        ))
    return turns
