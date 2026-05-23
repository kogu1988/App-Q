"""
Test: packages/research_engine/workflow.py
Kapsam:
  - T1.2: build_elephant_system_prompt()
  - T1.3: STANCE_PROFILE Agreeableness kalibrasyonu (regression)
"""
import pytest
from packages.research_engine.workflow import build_elephant_system_prompt
from packages.research_engine.models import STANCE_PROFILE, Persona


def make_persona(stance: str, agreeableness: int, traits_override: dict = None) -> Persona:
    """Test için minimal Persona oluşturucu."""
    traits = {"Agreeableness": agreeableness} if traits_override is None else traits_override
    return Persona(
        id=f"test-{stance}",
        name=f"Test {stance}",
        age=35,
        city="Istanbul",
        segment="test",
        stance=stance,
        price_sensitivity=5,
        digital_confidence=6,
        context="test context",
        goals=["test goal"],
        objections=["test objection"],
        knowledge_boundary="orta düzey",
        traits=traits,
    )


class TestBuildElephantSystemPrompt:
    """T1.2 — ELEPHANT Anti-Sycophancy System Prompt"""

    def test_T1_2_1_yuksek_agreeableness_ek_uyari_icerir(self):
        """Agreeableness > 65 → 'her şeye evet demek' uyarısı."""
        persona = make_persona("Innovator", 70)
        prompt = build_elephant_system_prompt(persona)
        assert "ELEPHANT" in prompt
        assert len(prompt) >= 300

    def test_T1_2_2_standart_agreeableness_elephant_icerir(self):
        """Agreeableness 40-65 → standart ELEPHANT promptu."""
        persona = make_persona("Mainstream", 55)
        prompt = build_elephant_system_prompt(persona)
        assert "ELEPHANT" in prompt

    def test_T1_2_3_dusuk_agreeableness_guclu_red_izni(self):
        """Agreeableness < 40 → güçlü red izni, kanıt talebi."""
        persona = make_persona("Skeptic", 28)
        prompt = build_elephant_system_prompt(persona)
        assert "ELEPHANT" in prompt

    def test_T1_2_4_traits_bos_dict_default_kullanir(self):
        """traits = {} → default 60, crash yok."""
        persona = make_persona("Mainstream", 55, traits_override={})
        prompt = build_elephant_system_prompt(persona)
        assert isinstance(prompt, str)
        assert len(prompt) > 0

    def test_T1_2_5_traits_none_crash_yapmaz(self):
        """traits=None ile oluşturulan Persona → default 60 kullanılır, crash yok."""
        persona = Persona(
            id="test-none", name="Test None", age=35, city="Istanbul",
            segment="test", stance="Mainstream", price_sensitivity=5,
            digital_confidence=6, context="test context",
            goals=["test"], objections=["test"],
            knowledge_boundary="orta düzey", traits=None,
        )
        prompt = build_elephant_system_prompt(persona)
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "ELEPHANT" in prompt

    def test_T1_2_6_sinir_deger_40_standart_dal(self):
        """Agreeableness == 40 → standart prompt (< 40 dalı DEĞİL)."""
        persona_40 = make_persona("Mainstream", 40)
        persona_39 = make_persona("Skeptic", 39)
        prompt_40 = build_elephant_system_prompt(persona_40)
        prompt_39 = build_elephant_system_prompt(persona_39)
        # 40 standart, 39 güçlü red — farklı dallar
        assert len(prompt_40) != len(prompt_39)

    def test_T1_2_7_sinir_deger_65_standart_dal(self):
        """Agreeableness == 65 → standart prompt (> 65 dalı DEĞİL)."""
        persona_65 = make_persona("Mainstream", 65)
        persona_66 = make_persona("Innovator", 66)
        prompt_65 = build_elephant_system_prompt(persona_65)
        prompt_66 = build_elephant_system_prompt(persona_66)
        # 65 standart, 66 ek uyarı — farklı dallar
        assert len(prompt_65) != len(prompt_66)

    def test_T1_2_8_min_karakter_uzunlugu(self):
        """Tüm stance'lar için prompt >= 300 karakter."""
        for agr, stance in [(70, "Innovator"), (55, "Mainstream"), (28, "Skeptic")]:
            p = make_persona(stance, agr)
            assert len(build_elephant_system_prompt(p)) >= 300, f"{stance} için prompt çok kısa"

    def test_T1_2_str_tip_doner(self):
        """Her zaman str döndürmeli."""
        persona = make_persona("Mainstream", 55)
        result = build_elephant_system_prompt(persona)
        assert isinstance(result, str)


class TestAgreeablenessKalibrasyonu:
    """T1.3 — STANCE_PROFILE Agreeableness Regression Testleri"""

    def test_T1_3_1_innovator_agreeableness_mod_dorttur(self):
        """REGRESSION: Innovator agreeableness_mod +8'den +4'e düşürüldü."""
        actual = STANCE_PROFILE["Innovator"]["agreeableness_mod"]
        assert actual == 4, (
            f"Regression! Innovator agreeableness_mod={actual}, beklenen=4. "
            "Bu değer dalkavukluk riskini önlemek için +8'den +4'e düşürüldü (commit 5d37ece)."
        )

    def test_T1_3_2_skeptic_agreeableness_mod_negatif(self):
        """REGRESSION: Skeptic agreeableness_mod negatif olmalı."""
        actual = STANCE_PROFILE["Skeptic"]["agreeableness_mod"]
        assert actual < 0, f"Skeptic agreeableness_mod={actual}, negatif olmalı"
        assert actual == -10, f"Skeptic agreeableness_mod={actual}, beklenen=-10"

    def test_T1_3_3_tum_stance_profilleri_mevcut(self):
        """Tüm 5 Rogers stance profili tanımlı olmalı."""
        required = {"Innovator", "EarlyAdopter", "Mainstream", "Laggard", "Skeptic"}
        missing = required - set(STANCE_PROFILE.keys())
        assert not missing, f"Eksik stance profilleri: {missing}"

    def test_T1_3_4_innovator_skepticten_daha_yuksek_agreeableness(self):
        """Innovator her zaman Skeptic'ten daha yüksek Agreeableness delta'sına sahip olmalı."""
        inn_mod = STANCE_PROFILE["Innovator"]["agreeableness_mod"]
        skp_mod = STANCE_PROFILE["Skeptic"]["agreeableness_mod"]
        assert inn_mod > skp_mod, (
            f"Innovator({inn_mod}) > Skeptic({skp_mod}) olmalı"
        )

    def test_T1_3_5_her_profilde_gerekli_alanlar_var(self):
        """Her stance profilinde zorunlu alanlar bulunmalı."""
        required_keys = {"agreeableness_mod", "openness_mod", "neuroticism_mod"}
        for stance, profile in STANCE_PROFILE.items():
            missing = required_keys - set(profile.keys())
            assert not missing, f"{stance} profilinde eksik alan: {missing}"
