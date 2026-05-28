import os
import hashlib
from typing import Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .database import get_db

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
# god_doc.md §5: nomic-embed-text (768-dim) — all-minilm (384-dim) yerini alıyor
# ai_semantic_cache tablosu temizlendi — yeni vektörler 768-boyutlu olacak
EMBEDDING_MODEL = "nomic-embed-text"

# Module-level session singleton — avoids a new TCP handshake per embedding call.
# HTTPAdapter with retry: 3 attempts, exponential backoff (0.5, 1.0, 2.0 s).
_session: Optional[requests.Session] = None


def _get_session() -> requests.Session:
    global _session
    if _session is None:
        retry = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[502, 503, 504],
            allowed_methods=["POST"],
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry, pool_connections=4, pool_maxsize=8)
        _session = requests.Session()
        _session.mount("http://", adapter)
        _session.mount("https://", adapter)
        _session.headers.update({"Content-Type": "application/json"})
    return _session


def get_embedding(text: str) -> Optional[list[float]]:
    """Gets a 384-dimensional embedding for the given text using Ollama."""
    url = f"{OLLAMA_BASE_URL.rstrip('/')}/api/embeddings"
    payload = {"model": EMBEDDING_MODEL, "prompt": text}

    try:
        resp = _get_session().post(url, json=payload, timeout=10)
        resp.raise_for_status()
        return resp.json().get("embedding")
    except requests.exceptions.Timeout:
        print("[Caching] Embedding timeout — Ollama may be busy.")
        return None
    except requests.exceptions.ConnectionError as e:
        print(f"[Caching] Embedding connection error: {e}")
        return None
    except requests.exceptions.HTTPError as e:
        print(f"[Caching] Embedding HTTP error {resp.status_code}: {e}")
        return None
    except Exception as e:
        print(f"[Caching] Unexpected embedding error: {e}")
        return None


def check_semantic_cache(prompt: str, system: str = "", threshold: float = 0.15) -> Optional[str]:
    """
    Checks the semantic cache for a similar prompt.
    If the cosine distance is below the threshold, returns the cached LLM response.
    Threshold 0.15: nomic-embed-text (768-dim) daha sıkı mesafeler üretir —
    all-minilm için kullanılan 0.09 değerinden daha yüksek eşik gerekir.
    """
    full_prompt = f"{system}\n\n{prompt}".strip()
    prompt_hash = hashlib.sha256(full_prompt.encode("utf-8")).hexdigest()

    # Fast path: exact hash match (zero cost, zero latency)
    with get_db() as (conn, cur):
        cur.execute("SELECT llm_response FROM ai_semantic_cache WHERE prompt_hash = %s", (prompt_hash,))
        row = cur.fetchone()
        if row:
            print("[Caching] EXACT MATCH found in cache!")
            return row["llm_response"]

    # Semantic match via pgvector HNSW index
    embedding = get_embedding(prompt)
    if not embedding:
        return None

    with get_db() as (conn, cur):
        cur.execute(
            """
            SELECT llm_response, prompt_embedding <=> %s::vector AS distance
            FROM ai_semantic_cache
            ORDER BY distance ASC
            LIMIT 1
            """,
            (embedding,),
        )
        row = cur.fetchone()

        if row and row["distance"] is not None:
            if row["distance"] < threshold:
                print(f"[Caching] SEMANTIC MATCH found! (Distance: {row['distance']:.4f})")
                return row["llm_response"]
            else:
                print(f"[Caching] Closest distance {row['distance']:.4f} > threshold {threshold}. Cache miss.")

    return None


def save_to_semantic_cache(
    prompt: str, response: str, system: str = "", query_type: str = "general"
) -> None:
    """Saves the prompt and LLM response to the semantic cache."""
    full_prompt = f"{system}\n\n{prompt}".strip()
    prompt_hash = hashlib.sha256(full_prompt.encode("utf-8")).hexdigest()

    embedding = get_embedding(prompt)
    if not embedding:
        print("[Caching] Failed to generate embedding — skipping cache save.")
        return

    with get_db() as (conn, cur):
        try:
            cur.execute(
                """
                INSERT INTO ai_semantic_cache (query_type, prompt_hash, prompt_embedding, llm_response)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (prompt_hash) DO NOTHING
                """,
                (query_type, prompt_hash, embedding, response),
            )
        except Exception as e:
            print(f"[Caching] Failed to save to cache DB: {e}")
