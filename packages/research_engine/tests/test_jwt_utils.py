"""Test: JWT (HS256) üretim ve doğrulama."""
import time

from packages.research_engine.jwt_utils import (
    create_token,
    extract_username,
    verify_token,
)

SECRET = "test-secret"


def test_roundtrip_extracts_username():
    token = create_token("alice", SECRET)
    assert extract_username(token, SECRET) == "alice"


def test_verify_returns_payload():
    payload = verify_token(create_token("bob", SECRET, expires_in=60), SECRET)
    assert payload is not None
    assert payload["sub"] == "bob"
    assert "exp" in payload and "iat" in payload


def test_wrong_secret_rejected():
    token = create_token("alice", SECRET)
    assert verify_token(token, "other-secret") is None


def test_tampered_token_rejected():
    token = create_token("alice", SECRET)
    header, payload, sig = token.split(".")
    tampered = f"{header}.{payload[:-1]}x.{sig}"
    assert verify_token(tampered, SECRET) is None


def test_expired_token_rejected():
    token = create_token("alice", SECRET, expires_in=-1)
    assert verify_token(token, SECRET) is None


def test_malformed_token_rejected():
    assert verify_token("not.a.jwt", SECRET) is None
    assert verify_token("", SECRET) is None


def test_expiry_is_absolute():
    token = create_token("alice", SECRET, expires_in=3600)
    payload = verify_token(token, SECRET)
    assert payload["exp"] > int(time.time())
