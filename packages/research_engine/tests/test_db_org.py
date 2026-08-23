"""Test: multi-user organizasyon CRUD (db_org) — mock DB."""
from contextlib import contextmanager
from unittest.mock import patch

from packages.research_engine.db_org import (
    add_organization_member,
    create_organization,
    get_user_org_id,
    get_user_organization,
    list_organization_members,
    list_organizations,
    remove_organization_member,
)


@contextmanager
def _fake_db(rows=None, rowcount=1):
    class Cur:
        def __init__(self):
            self.rowcount = rowcount

        def execute(self, sql, params=None):
            pass

        def fetchone(self):
            return rows[0] if rows else None

        def fetchall(self):
            return rows or []

    class Conn:
        def cursor(self, **kwargs):
            return Cur()

        def commit(self):
            pass

    yield Conn(), Cur()


def test_get_user_organization_found():
    row = {"id": "org1", "name": "Acme", "plan_type": "Enterprise", "created_at": "x", "member_role": "admin"}
    with patch("packages.research_engine.db_org.get_db", return_value=_fake_db([row])):
        org = get_user_organization("alice")
    assert org is not None
    assert org["id"] == "org1"
    assert org["member_role"] == "admin"


def test_get_user_organization_none():
    with patch("packages.research_engine.db_org.get_db", return_value=_fake_db([])):
        assert get_user_organization("nobody") is None


def test_remove_member_true_when_deleted():
    with patch("packages.research_engine.db_org.get_db", return_value=_fake_db(rowcount=1)):
        assert remove_organization_member("org1", "alice") is True


def test_crud_happy_path_no_raise():
    with patch("packages.research_engine.db_org.get_db", side_effect=lambda: _fake_db()):
        create_organization("org1", "Acme", "Enterprise", "alice")
        add_organization_member("org1", "bob", "member")
        list_organizations()
        list_organization_members("org1")
    assert True


def test_get_user_org_id_found():
    with patch("packages.research_engine.db_org.get_db", return_value=_fake_db([{"org_id": "org1"}])):
        assert get_user_org_id("alice") == "org1"


def test_get_user_org_id_none():
    with patch("packages.research_engine.db_org.get_db", return_value=_fake_db([])):
        assert get_user_org_id("nobody") is None
