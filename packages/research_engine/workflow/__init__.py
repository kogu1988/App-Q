"""Arastirma orkestrasyonu (refactor R8).

Eski workflow.py dosyasi sorumluluk bazinda pakete bolundu. Dis modullerin
ve testlerin import ettigi tum isimler (fonksiyonlar, sabitler ve eskiden
burada yeniden disa verilen node yardimcilari) buradan erisilebilir.
"""
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

from ._constants import (
    DEFAULT_QUESTIONS,
    DEFAULT_TRAIT_ORDER,
    RESPONDENT_QUESTION_FILTER,
)
from .interviews import classify_question, run_interviews
from .interviews_batch import (
    _regen_persona_turns,
    _skipped_interview,
    run_interviews_batch,
)
from .interviews_stream import run_interviews_stream
from .personas import (
    enrich_persona_bios,
    generate_personas,
    generate_personas_from_roles,
    neo_facets_from_traits,
    persona_attributes,
    persona_traits,
)
from .planning import (
    _format_ab_question,
    build_ab_comparison_question,
    build_research_plan,
    filter_questions_by_respondent,
    generate_interview_script,
)
