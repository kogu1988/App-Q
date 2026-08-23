"""
Test: fine-tuning veri export'u (ShareGPT JSONL formatı) — Sprint Enterprise.

export_finetuning_data() beğenilmiş curated soruları Unsloth/Axolotl uyumlu
ShareGPT formatında dışa aktarır. Bu testler DB'ye dokunmadan mock ile çalışır.
"""
import json
from unittest.mock import patch

from packages.research_engine.db_vectors import export_finetuning_data


def test_export_filters_liked_only():
    """is_liked=False kayıtlar dışlanmalı."""
    mock = [
        {"id": 1, "question": "Q1", "research_category": "A", "purpose_context": "p1", "is_liked": True},
        {"id": 2, "question": "Q2", "research_category": "B", "purpose_context": "p2", "is_liked": False},
        {"id": 3, "question": "Q3", "research_category": "C", "purpose_context": None, "is_liked": True},
    ]
    with patch("packages.research_engine.db_vectors.get_question_collection", return_value=mock):
        out = export_finetuning_data(liked_only=True)
        lines = [json.loads(l) for l in out.split("\n") if l.strip()]
        assert len(lines) == 2


def test_export_sharegpt_shape():
    """Her kayıt human→gpt konuşma çifti içermeli."""
    mock = [{"id": 1, "question": "Soru?", "research_category": "Kategori", "purpose_context": "Amaç", "is_liked": True}]
    with patch("packages.research_engine.db_vectors.get_question_collection", return_value=mock):
        rec = json.loads(export_finetuning_data(liked_only=True))
        conv = rec["conversations"]
        assert conv[0]["from"] == "human"
        assert conv[1]["from"] == "gpt"
        assert conv[1]["value"] == "Soru?"


def test_export_purpose_fallback():
    """Boş category/purpose varsayılanlara düşmeli."""
    mock = [{"id": 1, "question": "Soru?", "research_category": None, "purpose_context": None, "is_liked": True}]
    with patch("packages.research_engine.db_vectors.get_question_collection", return_value=mock):
        rec = json.loads(export_finetuning_data(liked_only=True))
        instruction = rec["conversations"][0]["value"]
        assert "Genel" in instruction and "Hedef kitle içgörüsü toplamak" in instruction


def test_export_empty_returns_empty_string():
    """Hiç kayıt yoksa boş string dönmeli (endpoint 404 tetikler)."""
    with patch("packages.research_engine.db_vectors.get_question_collection", return_value=[]):
        assert export_finetuning_data(liked_only=True) == ""
