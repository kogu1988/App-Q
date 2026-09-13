"""Router import sozlesmesi testleri.

Korunan deger: Router modulleri, `packages.research_engine.database`'tan
YALNIZCA gercekten var olan isimleri import etmeli. Yanlis modulden yapilan
bir import, modul yuklenirken degil endpoint cagrildiginda patlar ve
fark edilmesi zor olur (gecmis ornek: `get_personas_pool`).
"""
from __future__ import annotations

import ast
import pathlib

import pytest

ROUTER_DIR = pathlib.Path("apps/backend/routers")

TARGET_MODULES = {
    "packages.research_engine.database",
    "packages.research_engine.db_vectors",
    "packages.research_engine.db_org",
    "packages.research_engine.db_auth",
}


def _router_files() -> list[pathlib.Path]:
    files = sorted(ROUTER_DIR.glob("*.py"))
    client_dir = ROUTER_DIR / "client"
    if client_dir.is_dir():
        files.extend(sorted(client_dir.glob("*.py")))
    return files


def _imported_names(tree: ast.AST) -> list[tuple[str, str]]:
    """(modul, isim) ciftlerini topla — fonksiyon icindeki import'lar dahil."""
    pairs: list[tuple[str, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module in TARGET_MODULES:
            for alias in node.names:
                pairs.append((node.module, alias.name))
    return pairs


def test_router_imports_resolve_on_target_modules():
    """Her router import'u hedef modulde gercekten tanimli olmali."""
    import importlib

    missing: list[str] = []
    for path in _router_files():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for module_name, name in _imported_names(tree):
            module = importlib.import_module(module_name)
            if not hasattr(module, name):
                missing.append(f"{path}: {module_name}.{name}")

    assert not missing, "Gecersiz router import'lari:\n" + "\n".join(missing)


def test_client_package_keeps_public_router():
    """main.py tek `client.router` bekler; paket donusumu bunu bozmamali."""
    from apps.backend.routers import client

    assert hasattr(client, "router"), "client.router bulunamadi"
    assert hasattr(client, "limiter"), "client.limiter (rate limit) bulunamadi"


@pytest.mark.parametrize("name", ["get_me", "get_studies", "research_chat", "intake_chat", "synthesize"])
def test_client_shim_reexports_route_handlers(name: str):
    """Testlerin/dis modullerin import ettigi isimler shim'den erisilebilmeli."""
    from apps.backend.routers import client

    assert callable(getattr(client, name, None)), f"client.{name} disa verilmemis"
