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


# ── 11.6 Paket ayrımı sonrası import döngüsü kontrolü ──

def _module_name(path: pathlib.Path) -> str:
    """`packages/research_engine/a/b.py` -> `a.b` (paket __init__ -> `a`)."""
    rel = path.relative_to(PKG).with_suffix("")
    parts = [p for p in rel.parts if p != "__init__"]
    return ".".join(parts)


def _internal_relative_edges() -> dict[str, set[str]]:
    """Paket içi relative import kenarlarını çıkar (alt modül -> hedef modül).

    Yalnızca **modül seviyesindeki** import'lar dikkate alınır; fonksiyon içindeki
    tembel (lazy) import'lar döngü sayılmaz (ör. `...db_org`).
    """
    edges: dict[str, set[str]] = {}
    for path in _py_files(exclude_routers=False):
        module = _module_name(path)
        tree = ast.parse(path.read_text(encoding="utf-8"))
        targets: set[str] = set()
        for node in tree.body:
            if not isinstance(node, ast.ImportFrom) or not node.level:
                continue
            # level=1 -> aynı paket, level=2 -> bir üst paket ...
            parts = module.split(".")[:-1] if not path.name.startswith("__init__") else module.split(".")
            base = parts[: len(parts) - (node.level - 1)]
            if node.module:
                targets.add(".".join([*base, node.module]))
            else:
                # `from . import X` — X gercek alt modul olabilir
                for alias in node.names:
                    targets.add(".".join([*base, alias.name]))
        edges[module or "__init__"] = {t for t in targets if t}
    return edges


def test_11_6_no_circular_imports_after_package_split():
    """Refactor sonrası paketlerde döngüsel import olmamalı.

    `database/`, `analytics/`, `reporting/`, `workflow/` ve `routers/client/`
    paketlere bölündü; shim katmanı döngü yaratmamalı.
    """
    edges = _internal_relative_edges()
    known = set(edges)

    def resolve(target: str) -> str | None:
        if target in known:
            return target
        # Paket __init__ veya altında tanımlı bir isim (fonksiyon/sabit) olabilir
        prefix = target
        while "." in prefix:
            prefix = prefix.rsplit(".", 1)[0]
            if prefix in known:
                return prefix
        return target if target in known else None

    graph: dict[str, set[str]] = {m: set() for m in known}
    for module, targets in edges.items():
        for t in targets:
            resolved = resolve(t)
            if resolved and resolved != module:
                graph[module].add(resolved)

    visit: dict[str, int] = {}
    cycle: list[str] = []

    def dfs(node: str, stack: list[str]) -> bool:
        visit[node] = 1
        stack.append(node)
        for nxt in graph.get(node, ()):
            state = visit.get(nxt, 0)
            if state == 1:
                cycle.extend([*stack, nxt])
                return True
            if state == 0 and dfs(nxt, stack):
                return True
        stack.pop()
        visit[node] = 2
        return False

    for node in sorted(graph):
        if visit.get(node, 0) == 0 and dfs(node, []):
            break

    assert not cycle, "Döngüsel import: " + " -> ".join(cycle)
