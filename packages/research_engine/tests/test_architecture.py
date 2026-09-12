"""GRUP 11 — Domain İzolasyonu (Mimari Kural) testleri.

Korunan değer: `packages/research_engine` framework-agnostic kalmalı. FastAPI'ye veya
`apps/` katmanına bağlanırsa taşınabilirlik ve test edilebilirlik kaybolur.

Bu testler statiktir: hızlı, DB gerektirmez.
"""
from __future__ import annotations

import ast
import importlib
import pathlib

PKG = pathlib.Path("packages/research_engine")

# app/main/router katmanı FastAPI kullanabilir; domain kullanamaz
_ALLOWED_FASTAPI_DIRS = {"routers"}


def _py_files(exclude_routers: bool) -> list[pathlib.Path]:
    # tests/ klasörü domain'in tüketicisidir; tarama dışıdır
    files = [
        f for f in PKG.rglob("*.py")
        if "__pycache__" not in f.parts and "tests" not in f.parts
    ]
    if exclude_routers:
        files = [f for f in files if not (_ALLOWED_FASTAPI_DIRS & set(f.parts))]
    return files


def _top_level_imports(path: pathlib.Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    return imported


def test_11_1_research_engine_does_not_import_apps():
    """Domain katmanı `apps` paketine bağımlı olmamalı (tek yönlü bağımlılık)."""
    offenders: list[str] = []
    for path in _py_files(exclude_routers=False):
        text = path.read_text(encoding="utf-8")
        if "from apps" in text or "import apps" in text:
            offenders.append(str(path))

    assert offenders == [], f"research_engine apps'e bağımlı: {offenders}"


def test_11_2_no_fastapi_dependency_outside_routers():
    """Domain katmanı FastAPI'ye bağımlı olmamalı (routers/ hariç)."""
    offenders: list[str] = []
    for path in _py_files(exclude_routers=True):
        text = path.read_text(encoding="utf-8")
        if "from fastapi" in text or "import fastapi" in text:
            offenders.append(str(path))

    assert offenders == [], f"domain katmanında fastapi importu: {offenders}"


def test_11_3_models_py_is_pure_data():
    """models.py yalnızca saf veri sözleşmeleri içermeli — DB/HTTP importu olmamalı."""
    imported = _top_level_imports(PKG / "models.py")
    forbidden = {"psycopg2", "requests", "fastapi", "openai", "redis", "celery"}

    assert not (imported & forbidden), f"models.py saf değil: {imported & forbidden}"


def test_11_4_core_modules_import_without_circular_dependency():
    """Çekirdek modüller tek tek sorunsuz import edilmeli (dairesel import yok)."""
    for name in (
        "models",
        "plan_config",
        "quality",
        "matrix",
        "analytics",
        "workflow",
        "database",
        "providers",
        "pricing_table",
        "paddle_config",
        "paddle_webhooks",
        "research_runner",
    ):
        module = importlib.import_module(f"packages.research_engine.{name}")
        assert module is not None


def test_11_5_plan_config_has_no_heavy_dependencies():
    """plan_config.py yalnızca stdlib kullanmalı (SSOT hafif kalmalı)."""
    imported = _top_level_imports(PKG / "plan_config.py")
    non_stdlib = {i for i in imported if i not in {"__future__"}}

    assert non_stdlib == set(), f"plan_config stdlib dışına bağımlı: {non_stdlib}"
