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
                created_by, is_global, b2b_role, industry, company_size, b2b_company_type, b2b_decision_maker
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING
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
                persona_dict.get("b2b_decision_maker", False)
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
                # Remove vector object for standard JSON serialization
                if "embedding" in persona:
                    del persona["embedding"]
            except json.JSONDecodeError:
                pass
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
        cur.execute("SELECT * FROM personas_pool")
        return [dict(row) for row in cur.fetchall()]

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
