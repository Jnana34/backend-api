# bot/utils.py
import uuid
import time
import psycopg2
import google.generativeai as genai
import json
import re
from django.conf import settings

DB_CONN = "dbname=shopfusion_db user=postgres password=Jnana34 host=localhost port=5433"
EMBED_MODEL = "models/text-embedding-004"
MODEL_NAME = "gemini-2.0-flash"
API_KEY = settings.GEMINI_API_KEY
genai.configure(api_key=API_KEY)   # replace with env var in production


def to_pgvector(embedding):
    return "[" + ",".join(str(x) for x in embedding) + "]"


def retrieve_schema(user_query: str, top_k: int = 5):
    emb = genai.embed_content(model=EMBED_MODEL, content=user_query)["embedding"]
    emb_str = to_pgvector(emb)

    conn = psycopg2.connect(DB_CONN)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT object_name, definition
        FROM bot_schemaembedding
        ORDER BY embedding <#> %s::vector
        LIMIT %s;
        """,
        (emb_str, top_k)
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def nl_to_sql_and_template(user_question: str):
    schema_hits = retrieve_schema(user_question)
    context = "\n".join([f"{n}: {d}" for n, d in schema_hits])

    prompt = f"""
    Your name is Sangmilli.
    You are a Postgres SQL generator and answer formatter.

    Relevant schema definitions:
    {context}

    User question: "{user_question}"

    Instructions:
    - If the question clearly relates to database content, return SQL + template.
    - If the question is general knowledge (not related to DB), return mode="direct".
    - Do not invent columns.
    - Output ONLY JSON.

    Example (DB question):
    {{
      "mode": "sql",
      "sql": "SELECT price FROM products_product WHERE name = 'Spiral Pillar';",
      "template": "The price of Spiral Pillar is {{rows}}."
    }}

    Example (general question):
    {{
      "mode": "direct",
      "answer": "The capital of France is Paris."
    }}
    """

    model = genai.GenerativeModel(MODEL_NAME)
    resp = model.generate_content(prompt)

    raw = resp.text.strip().replace("```json", "").replace("```", "").strip()
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        raise ValueError(f"❌ No valid JSON found:\n{raw}")

    return json.loads(match.group(0))


def run_sql(query: str):
    conn = psycopg2.connect(DB_CONN)
    cur = conn.cursor()
    cur.execute(query)
    try:
        rows = cur.fetchall()
    except psycopg2.ProgrammingError:
        rows = []
    cur.close()
    conn.close()
    return rows
