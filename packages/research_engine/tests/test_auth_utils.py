"""Test: parola hash'leme (PBKDF2) doğrulama."""
from packages.research_engine.auth_utils import hash_password, verify_password


def test_roundtrip_verifies_correct_password():
    stored = hash_password("guclu-sifre")
    assert verify_password("guclu-sifre", stored) is True


def test_wrong_password_rejected():
    stored = hash_password("guclu-sifre")
    assert verify_password("yanlis-sifre", stored) is False


def test_same_password_different_salt():
    h1 = hash_password("sifre")
    h2 = hash_password("sifre")
    assert h1 != h2  # tuzlar farklı olmalı
    assert verify_password("sifre", h1) is True
    assert verify_password("sifre", h2) is True


def test_malformed_hash_rejected():
    assert verify_password("sifre", "bozuk-hash") is False
    assert verify_password("sifre", "") is False


def test_wrong_algo_rejected():
    assert verify_password("sifre", "sha1$1000$abc$def") is False
