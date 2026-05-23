import json
import os
import urllib.request
import urllib.error
import hashlib
from typing import Optional
from .database import get_db

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
EMBEDDING_MODEL = "all-minilm"

def get_embedding(text: str) -> Optional[list[float]]:
    """Gets a 384-dimensional embedding for the given text using Ollama."""
    url = f"{OLLAMA_BASE_URL.rstrip('/')}/api/embeddings"
    payload = {
        "model": EMBEDDING_MODEL,
        "prompt": text
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
            return data.get("embedding")
    except urllib.error.URLError as e:
        error_msg = e.read().decode('utf-8') if hasattr(e, 'read') else str(e)
        print(f"[Caching] Embedding error: {e} - Response: {error_msg}")
        return None
    except TimeoutError as e:
        print(f"[Caching] Embedding timeout: {e}")
        return None

def check_semantic_cache(prompt: str, system: str = "", threshold: float = 0.09) -> Optional[str]:

    """
    Checks the semantic cache for a similar prompt.
    If the cosine distance is below the threshold, returns the cached LLM response.
    """
    full_prompt = f"{system}\n\n{prompt}".strip()
    prompt_hash = hashlib.sha256(full_prompt.encode("utf-8")).hexdigest()
    
    # First, try exact match by hash (zero cost, zero latency)
    with get_db() as (conn, cur):
        cur.execute("SELECT llm_response FROM ai_semantic_cache WHERE prompt_hash = %s", (prompt_hash,))
        row = cur.fetchone()
        if row:
            print("[Caching] EXACT MATCH found in cache!")
            return row["llm_response"]
            
    # If no exact match, try semantic match using ONLY the user's prompt (to avoid tokenizer limits)
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
            (embedding,)
        )
        row = cur.fetchone()
        
        if row and row["distance"] is not None:
            if row["distance"] < threshold:
                print(f"[Caching] SEMANTIC MATCH found in cache! (Distance: {row['distance']:.4f})")
                return row["llm_response"]
            else:
                print(f"[Caching] Semantic match rejected. Closest distance: {row['distance']:.4f} (Threshold: {threshold})")
            
    return None

def save_to_semantic_cache(prompt: str, response: str, system: str = "", query_type: str = "general") -> None:
    """Saves the prompt and LLM response to the semantic cache."""
    full_prompt = f"{system}\n\n{prompt}".strip()
    prompt_hash = hashlib.sha256(full_prompt.encode("utf-8")).hexdigest()
    
    # Embed ONLY the user prompt to stay within tokenizer limits
    embedding = get_embedding(prompt)
    if not embedding:
        print("[Caching] Failed to generate embedding. Skipping cache save.")
        return
        
    with get_db() as (conn, cur):
        try:
            cur.execute(
                """
                INSERT INTO ai_semantic_cache (query_type, prompt_hash, prompt_embedding, llm_response)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (prompt_hash) DO NOTHING
                """,
                (query_type, prompt_hash, embedding, response)
            )
        except Exception as e:
            print(f"[Caching] Failed to save to cache DB: {e}")
