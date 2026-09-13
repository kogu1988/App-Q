from __future__ import annotations
import json
from datetime import datetime
from .database import get_db

def save_persona_to_pool(persona_dict: dict, embedding: list[float] = None) -> None:
    with get_db() as (conn, cur):
        cur.execute(
            """
            INSERT INTO personas_pool (
                id, name, age, city, segment, stance, price_sensitivity, digital_confidence, 
                context, goals, objections, knowledge_boundary, country_code, origin_country, 
                role_title, bio, attributes, traits, created_at, embedding,
                created_by, is_global, b2b_role, industry, company_size, b2b_company_type, b2b_decision_maker,
                ses_group, respondent_type, settlement_type
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                usage_count = personas_pool.usage_count + 1
            """,
            (
                persona_dict.get("id"),
                persona_dict.get("name"),
                persona_dict.get("age"),
                persona_dict.get("city"),
                persona_dict.get("segment"),
                persona_dict.get("stance"),
                persona_dict.get("price_sensitivity"),
                persona_dict.get("digital_confidence"),
                persona_dict.get("context"),
                json.dumps(persona_dict.get("goals", []), ensure_ascii=False),
                json.dumps(persona_dict.get("objections", []), ensure_ascii=False),
                persona_dict.get("knowledge_boundary"),
                persona_dict.get("country_code"),
                persona_dict.get("origin_country"),
                persona_dict.get("role_title"),
                persona_dict.get("bio"),
                json.dumps(persona_dict.get("attributes", {}), ensure_ascii=False),
                json.dumps(persona_dict.get("traits", {}), ensure_ascii=False),
                datetime.now().isoformat(timespec="seconds"),
                embedding,
                persona_dict.get("created_by"),
                persona_dict.get("is_global", True),
                persona_dict.get("b2b_role"),
                persona_dict.get("industry"),
                persona_dict.get("company_size"),
                persona_dict.get("b2b_company_type"),
                persona_dict.get("b2b_decision_maker", False),
                persona_dict.get("ses_group", "C1"),
                persona_dict.get("respondent_type", "potential_customer"),
                persona_dict.get("settlement_type", "kentsel")
            )
        )

def get_personas_from_pool_by_role(role_title: str, limit: int = 5) -> list[dict]:
    with get_db() as (conn, cur):
        cur.execute("SELECT * FROM personas_pool WHERE role_title = %s ORDER BY created_at DESC LIMIT %s", (role_title, limit))
        rows = cur.fetchall()
        personas = []
        for row in rows:
            persona = dict(row)
            try:
                persona["goals"] = json.loads(persona["goals"]) if persona["goals"] else []
                persona["objections"] = json.loads(persona["objections"]) if persona["objections"] else []
                persona["attributes"] = json.loads(persona["attributes"]) if persona["attributes"] else {}
                persona["traits"] = json.loads(persona["traits"]) if persona["traits"] else {}
                
                # Parse big_five_vector into a dictionary
                big_five_vector = persona.get("big_five_vector")
                if big_five_vector:
                    if isinstance(big_five_vector, str):
                        try:
                            # Postgres vector returns string like '[0.5, 0.2, ...]'
                            vector_vals = json.loads(big_five_vector)
                        except (json.JSONDecodeError, TypeError, ValueError):
                            vector_vals = [0.5, 0.5, 0.5, 0.5, 0.5]
                    else:
                        vector_vals = list(big_five_vector)
                        
                    if len(vector_vals) >= 5:
                        persona["big_five"] = {
                            "openness": int(vector_vals[0] * 100),
                            "conscientiousness": int(vector_vals[1] * 100),
                            "extroversion": int(vector_vals[2] * 100),
                            "agreeableness": int(vector_vals[3] * 100),
                            "neuroticism": int(vector_vals[4] * 100)
                        }
                else:
                    import random
                    # Fallback random values if missing in DB
                    persona["big_five"] = {
                        "openness": random.randint(40, 90),
                        "conscientiousness": random.randint(40, 90),
                        "extroversion": random.randint(30, 80),
                        "agreeableness": random.randint(40, 80),
                        "neuroticism": random.randint(20, 70)
                    }

                # Remove vector objects for standard JSON serialization
                if "embedding" in persona:
                    del persona["embedding"]
                if "big_five_vector" in persona:
                    del persona["big_five_vector"]
            except Exception as e:
                print(f"Error parsing persona {persona.get('id')}: {e}")
            personas.append(persona)
        return personas

def get_similar_personas(embedding: list[float], limit: int = 5) -> list[dict]:
    with get_db() as (conn, cur):
        cur.execute(
            """
            SELECT *, embedding <=> %s::vector AS distance
            FROM personas_pool
            WHERE embedding IS NOT NULL
            ORDER BY distance ASC
            LIMIT %s
            """,
            (embedding, limit)
        )
        rows = cur.fetchall()
        personas = []
        for row in rows:
            persona = dict(row)
            try:
                persona["goals"] = json.loads(persona["goals"]) if persona["goals"] else []
                persona["objections"] = json.loads(persona["objections"]) if persona["objections"] else []
                persona["attributes"] = json.loads(persona["attributes"]) if persona["attributes"] else {}
                persona["traits"] = json.loads(persona["traits"]) if persona["traits"] else {}
                if "embedding" in persona:
                    del persona["embedding"]
            except json.JSONDecodeError:
                pass
            personas.append(persona)
        return personas

def get_personas_pool() -> list[dict]:
    with get_db() as (conn, cur):
        # We explicitly omit 'embedding' and 'big_five_vector' to prevent FastAPI serialization crashes
        # Or we can just delete them from the dict
        cur.execute("SELECT * FROM personas_pool ORDER BY created_at DESC")
        personas = []
        for row in cur.fetchall():
            p = dict(row)
            if "embedding" in p:
                del p["embedding"]
            if "big_five_vector" in p:
                del p["big_five_vector"]
            personas.append(p)
        return personas

def delete_persona_from_pool(persona_id: str) -> bool:
    with get_db() as (conn, cur):
        cur.execute("DELETE FROM personas_pool WHERE id = %s", (persona_id,))
        return cur.rowcount > 0

def add_to_question_collection(question: str, study_id: str, research_title: str, research_category: str, purpose_context: str, is_liked: int = 1, embedding: list[float] = None) -> None:
    with get_db() as (conn, cur):
        cur.execute(
            """
            INSERT INTO curated_questions (question, study_id, research_title, research_category, purpose_context, is_liked, created_at, embedding)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                question,
                study_id,
                research_title,
                research_category,
                purpose_context,
                bool(is_liked),
                datetime.now().isoformat(timespec="seconds"),
                embedding
            )
        )

def get_question_collection() -> list[dict]:
    with get_db() as (conn, cur):
        cur.execute("SELECT id, question, study_id, research_title, research_category, purpose_context, is_liked, created_at FROM curated_questions ORDER BY id DESC")
        rows = cur.fetchall()
        return [dict(row) for row in rows]

def get_similar_questions(embedding: list[float], limit: int = 3) -> list[dict]:
    with get_db() as (conn, cur):
        cur.execute(
            """
            SELECT id, question, study_id, research_title, research_category, purpose_context, is_liked, created_at, 
                   embedding <=> %s::vector AS distance
            FROM curated_questions
            WHERE embedding IS NOT NULL AND is_liked = TRUE
            ORDER BY distance ASC
            LIMIT %s
            """,
            (embedding, limit)
        )
        return [dict(row) for row in cur.fetchall()]

def update_question_liked_status(question_id: int, is_liked: bool) -> None:
    with get_db() as (conn, cur):
        cur.execute("UPDATE curated_questions SET is_liked = %s WHERE id = %s", (True if is_liked else False, question_id))

def update_question_purpose(question_id: int, purpose_context: str) -> None:
    with get_db() as (conn, cur):
        cur.execute("UPDATE curated_questions SET purpose_context = %s WHERE id = %s", (purpose_context, question_id))

def delete_from_question_collection(question_id: int) -> None:
    with get_db() as (conn, cur):
        cur.execute("DELETE FROM curated_questions WHERE id = %s", (question_id,))

def export_finetuning_data(liked_only: bool = True) -> str:
    """Curated soruları ShareGPT/JSONL formatında fine-tuning verisi olarak dışa aktarır.

    Her satır bir ShareGPT kaydı içerir (Unsloth/Axolotl uyumlu):
      {"conversations": [{"from": "human", "value": "<talimat>"}, {"from": "gpt", "value": "<soru>"}]}
    """
    questions = get_question_collection()
    if liked_only:
        questions = [q for q in questions if q.get("is_liked")]
    lines: list[str] = []
    for q in questions:
        category = q.get("research_category") or "Genel"
        purpose = q.get("purpose_context") or "Hedef kitle içgörüsü toplamak"
        instruction = (
            f"Bir pazar araştırması mülakat sorusu yaz. "
            f"Kategori: {category}. Amaç: {purpose}."
        )
        record = {
            "conversations": [
                {"from": "human", "value": instruction},
                {"from": "gpt", "value": q.get("question", "")},
            ]
        }
        lines.append(json.dumps(record, ensure_ascii=False))
    return "\n".join(lines)

def cluster_atomic_codes(codes: list[dict], threshold: float = 0.15) -> list[list[dict]]:
    """
    Clusters atomic codes using PostgreSQL pgvector cosine distance.
    Returns a list of clusters, where each cluster is a list of code dictionaries.
    """
    if not codes:
        return []
        
    # Check if we have embeddings
    valid_codes = [c for c in codes if c.get("semantic_embedding")]
    if not valid_codes:
        return [[c] for c in codes]

    import uuid
    for c in valid_codes:
        if "id" not in c:
            c["id"] = str(uuid.uuid4())

    clusters = []
    unassigned = {c["id"]: c for c in valid_codes}

    with get_db() as (conn, cur):
        dim = len(valid_codes[0]["semantic_embedding"])
        
        # Create temp table for pgvector distance calculation
        cur.execute(f"CREATE TEMP TABLE temp_atomic_codes (id VARCHAR, embedding vector({dim})) ON COMMIT DROP")
        
        # Insert
        for c in valid_codes:
            cur.execute("INSERT INTO temp_atomic_codes (id, embedding) VALUES (%s, %s)", (c["id"], c["semantic_embedding"]))
            
        while unassigned:
            # Pop a code to start a new cluster
            centroid_id, centroid_code = unassigned.popitem()
            cluster = [centroid_code]
            
            # Query pgvector for semantic neighbors
            cur.execute(
                """
                SELECT id, embedding <=> %s::vector AS distance
                FROM temp_atomic_codes
                WHERE id != %s AND embedding <=> %s::vector < %s
                """,
                (centroid_code["semantic_embedding"], centroid_id, centroid_code["semantic_embedding"], threshold)
            )
            
            rows = cur.fetchall()
            for row in rows:
                neighbor_id = row["id"]
                if neighbor_id in unassigned:
                    cluster.append(unassigned.pop(neighbor_id))
            
            clusters.append(cluster)

    return clusters
