"""
GEMA-MED — USMLE Study Agent
FastAPI: auth propio + agente Claude/Groq + Telegram bot

Run:  python main.py
Web:  http://localhost:8000
Docs: http://localhost:8000/docs
"""

import os
import uuid
from collections import defaultdict
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
import json as _json

load_dotenv()

from auth import (
    hash_password, verify_password, create_token,
    get_current_user, get_optional_user,
)
from db import (
    init_db, get_progress, get_weakness_report,
    create_user, get_user_by_username, get_user_by_id,
    set_study_plan, get_study_plan, update_study_phase,
    get_week_detail, PLAN_TEMPLATES,
    submit_content_item, review_content_item,
    get_review_queue, get_content_audit_trail, get_pipeline_stats,
    get_question_stats,
)
from agent import run_agent, run_agent_stream

sessions: dict[str, list] = defaultdict(list)
FRONTEND = Path(__file__).parent / "frontend.html"
ADMIN    = Path(__file__).parent / "admin.html"

# Audit cache — resultado de la última auditoría de topics
_audit_cache: dict = {}


def _run_topic_audit(samples_per_topic: int = 20) -> dict:
    """Auditoría de calidad de topics — verifica que cada pool retorne contenido correcto."""
    from tools import get_usmle_question, TOPIC_KEYWORDS, _load_dataset
    from collections import Counter
    import random

    ds = _load_dataset()
    topic_sizes = Counter(q["topic"] for q in ds)
    results = {}

    for topic, kws in TOPIC_KEYWORDS.items():
        ok = 0
        for _ in range(samples_per_topic):
            q = get_usmle_question(topic=topic)
            if any(kw in q["question"].lower() for kw in kws):
                ok += 1
        pct = round(ok / samples_per_topic * 100, 1)
        pool_label = topic_sizes.get(topic, 0)
        pool_strict = sum(
            1 for q in ds
            if q["topic"] == topic
            and any(kw in q["question"].lower() for kw in kws)
        )
        results[topic] = {
            "accuracy": pct,
            "ok": ok,
            "samples": samples_per_topic,
            "pool_label": pool_label,
            "pool_strict": pool_strict,
            "status": "PASS" if pct >= 80 else "WARN" if pct >= 60 else "FAIL",
        }
        if pct < 80:
            print(f"[AUDIT] {topic}: {pct}% — BELOW THRESHOLD")

    failed = [t for t, r in results.items() if r["status"] == "FAIL"]
    warned = [t for t, r in results.items() if r["status"] == "WARN"]
    return {
        "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
        "topics": results,
        "summary": {
            "total": len(results),
            "pass": len([r for r in results.values() if r["status"] == "PASS"]),
            "warn": len(warned),
            "fail": len(failed),
            "failed_topics": failed,
            "warned_topics": warned,
        },
    }


async def _scheduled_audit_loop():
    """Corre auditoría cada 24h en background."""
    import asyncio
    global _audit_cache
    await asyncio.sleep(120)  # esperar 2 min después de startup (dataset cargando)
    while True:
        print("[AUDIT] Iniciando auditoría de topics...")
        try:
            result = await asyncio.to_thread(_run_topic_audit)
            _audit_cache = result
            s = result["summary"]
            print(f"[AUDIT] Completada — PASS:{s['pass']} WARN:{s['warn']} FAIL:{s['fail']}")
            if s["fail"] > 0:
                print(f"[AUDIT] PROBLEMAS: {s['failed_topics']}")
        except Exception as e:
            print(f"[AUDIT] Error: {e}")
        await asyncio.sleep(24 * 3600)  # repetir cada 24h


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    telegram_started = False
    if os.getenv("TELEGRAM_TOKEN"):
        try:
            from telegram_bot import start_telegram_bot
            await start_telegram_bot()
            telegram_started = True
        except ImportError:
            pass

    channels = ["Web (http://localhost:8000)", "REST API (/docs)"]
    if telegram_started: channels.append("Telegram")
    print(f"OK GEMA-MED listo — {', '.join(channels)}")

    import asyncio
    from tools import _load_dataset
    asyncio.create_task(asyncio.to_thread(_load_dataset))
    asyncio.create_task(_scheduled_audit_loop())
    print("Cargando banco de preguntas en background...")
    print("Auditoria de topics programada (cada 24h, primera en 2 min)")

    yield

    if telegram_started:
        from telegram_bot import stop_telegram_bot
        await stop_telegram_bot()


app = FastAPI(
    title="GEMA-MED — USMLE Tutor",
    description="Agente IA para USMLE Step 1/2/3 con plan de estudio estructurado.",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)


# ── Modelos Pydantic ──────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    username: str
    password: str
    display_name: str | None = None

class LoginRequest(BaseModel):
    username: str
    password: str

class PlanRequest(BaseModel):
    target_date:     str          # YYYY-MM-DD
    plan_type:       str = "12_week"
    daily_questions: int = 60
    language:        str = "bilingual"
    current_week:    int = 1

class ChatRequest(BaseModel):
    session_id: str | None = None
    message: str
    language: str | None = None   # "es" | "en" | "bilingual" (default)


# ── Auth endpoints ────────────────────────────────────────────────────────────

@app.post("/auth/register", tags=["auth"])
async def register(req: RegisterRequest):
    username = req.username.lower().strip()
    if len(username) < 3:
        raise HTTPException(400, "Username debe tener al menos 3 caracteres")
    if len(req.password) < 6:
        raise HTTPException(400, "Password debe tener al menos 6 caracteres")
    if get_user_by_username(username):
        raise HTTPException(409, "Username ya existe")

    pw_hash = hash_password(req.password)
    user = create_user(username, pw_hash, req.display_name)
    token = create_token(user["id"], user["username"], user["display_name"])
    return {"token": token, "user": user, "has_plan": False}


@app.post("/auth/login", tags=["auth"])
async def login(req: LoginRequest):
    user = get_user_by_username(req.username)
    if not user or not verify_password(req.password, user["password_hash"]):
        raise HTTPException(401, "Usuario o contraseña incorrectos")

    token = create_token(user["id"], user["username"], user.get("display_name", ""))
    plan  = get_study_plan(str(user["id"]))
    return {"token": token, "user": {"id": user["id"], "username": user["username"],
            "display_name": user.get("display_name")}, "has_plan": plan.get("has_plan", False)}


# ── Me endpoints ──────────────────────────────────────────────────────────────

@app.get("/me", tags=["me"])
async def me(user = Depends(get_current_user)):
    profile  = get_user_by_id(user["user_id"])
    plan     = get_study_plan(user["user_id"])
    progress = get_progress(user["user_id"])
    return {"user": profile, "plan": plan, "progress": progress}


@app.post("/me/plan", tags=["me"])
async def save_my_plan(req: PlanRequest, user = Depends(get_current_user)):
    plan = set_study_plan(
        user_id=user["user_id"],
        target_date=req.target_date,
        plan_type=req.plan_type,
        daily_questions=req.daily_questions,
        language=req.language,
        current_week=req.current_week,
    )
    return plan


@app.patch("/me/plan/week", tags=["me"])
async def advance_week(week: int, user = Depends(get_current_user)):
    return update_study_phase(user["user_id"], current_week=week)


@app.get("/me/progress", tags=["me"])
async def my_progress(user = Depends(get_current_user)):
    return {
        "progress": get_progress(user["user_id"]),
        "weakness": get_weakness_report(user["user_id"]),
        "plan":     get_study_plan(user["user_id"]),
    }


# ── Plan templates (público — para el formulario del frontend) ────────────────

@app.get("/plan-templates", tags=["plans"])
def plan_templates():
    from db import TWELVE_WEEK_PLAN, SIX_WEEK_PLAN
    return {
        "12_week": {"label": "12 semanas — Estándar", "weeks": TWELVE_WEEK_PLAN},
        "6_week":  {"label": "6 semanas — Intensivo",  "weeks": SIX_WEEK_PLAN},
    }


# ── Chat ──────────────────────────────────────────────────────────────────────

@app.post("/chat", tags=["chat"])
async def chat(req: ChatRequest, user = Depends(get_optional_user)):
    user_id = user["user_id"]
    session_id = req.session_id or (f"web_{user_id}" if user_id != "dev_user" else str(uuid.uuid4()))

    history = sessions[session_id]
    response_text = await run_agent(
        session_id=session_id,
        history=history,
        user_message=req.message,
        user_id=user_id,
        language=req.language,
    )
    return {"session_id": session_id, "response": response_text, "messages_in_session": len(history)}


# ── Otros ─────────────────────────────────────────────────────────────────────

@app.post("/chat/stream", tags=["chat"])
async def chat_stream(req: ChatRequest, user = Depends(get_optional_user)):
    """
    Streaming chat — Server-Sent Events.
    El frontend lee tokens en tiempo real: el texto aparece mientras se genera.
    """
    user_id   = user["user_id"]
    session_id = req.session_id or (f"web_{user_id}" if user_id != "dev_user" else str(uuid.uuid4()))
    history   = sessions[session_id]

    async def event_generator():
        # Enviar session_id primero
        yield f"data: {_json.dumps({'session_id': session_id})}\n\n"
        # Stream tokens — pasar user_id real para save_result correcto
        async for chunk in run_agent_stream(session_id, history, req.message, user_id=user_id, language=req.language):
            yield f"data: {_json.dumps({'text': chunk})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control":    "no-cache",
            "Connection":       "keep-alive",
            "X-Accel-Buffering":"no",   # Railway/Nginx: disable response buffering
        },
    )


@app.get("/", include_in_schema=False)
def frontend():
    return FileResponse(FRONTEND)


@app.get("/health", tags=["system"])
def health():
    audit_summary = _audit_cache.get("summary", {})
    return {
        "status": "ok",
        "version": "2.0.0",
        "model": os.getenv("LLM_MODEL", "llama-3.1-8b-instant"),
        "telegram": bool(os.getenv("TELEGRAM_TOKEN")),
        "db": "postgresql" if os.getenv("DATABASE_URL") else "sqlite",
        "topic_audit": {
            "last_run": _audit_cache.get("timestamp", "pending"),
            "pass": audit_summary.get("pass", "?"),
            "warn": audit_summary.get("warn", "?"),
            "fail": audit_summary.get("fail", "?"),
            "failed_topics": audit_summary.get("failed_topics", []),
        },
    }


@app.get("/audit/topics", tags=["system"])
async def audit_topics(samples: int = 20, force: bool = False):
    """
    Auditoría de calidad de topics.
    - Usa cache (24h) por defecto.
    - ?force=true para forzar re-ejecución inmediata.
    - ?samples=N para cambiar número de muestras por topic (default 20).
    """
    global _audit_cache
    if force or not _audit_cache:
        import asyncio
        result = await asyncio.to_thread(_run_topic_audit, samples)
        _audit_cache = result
    return _audit_cache


# ── Content Validation Pipeline ──────────────────────────────────────────────

class ContentSubmitRequest(BaseModel):
    content_type: str = "explanation"   # question | explanation | general
    topic: str | None = None
    content: str                        # stem or main text
    choices: dict | None = None         # {"A": "...", "B": "...", ...}
    correct_answer: str | None = None
    explanation: str | None = None
    source_url: str | None = None
    source_type: str | None = None      # official | textbook | guideline | ai-generated

class ReviewRequest(BaseModel):
    decision: str      # "approved" | "rejected"
    notes: str = ""


@app.post("/content/submit", tags=["pipeline"])
async def content_submit(req: ContentSubmitRequest, user = Depends(get_current_user)):
    """Submit content for validation — runs all 4 automatic layers."""
    item = req.model_dump()
    result = submit_content_item(item, submitted_by=user["user_id"])
    return result


@app.post("/content/{item_id}/review", tags=["pipeline"])
async def content_review(item_id: str, req: ReviewRequest, user = Depends(get_current_user)):
    """Human review decision — approve or reject a content item."""
    result = review_content_item(
        item_id=item_id,
        decision=req.decision,
        reviewed_by=user["username"],
        notes=req.notes,
    )
    return result


@app.get("/content/queue", tags=["pipeline"])
async def content_queue(status: str = "needs_review", user = Depends(get_current_user)):
    """Get items in the review queue."""
    return {"queue": get_review_queue(status=status), "status": status}


@app.get("/content/{item_id}/audit", tags=["pipeline"])
async def content_audit(item_id: str, user = Depends(get_current_user)):
    """Full audit trail for a content item."""
    return {"item_id": item_id, "trail": get_content_audit_trail(item_id)}


@app.get("/pipeline/stats", tags=["pipeline"])
async def pipeline_stats(user = Depends(get_current_user)):
    """Content pipeline statistics."""
    return get_pipeline_stats()


@app.post("/content/validate-preview", tags=["pipeline"])
async def validate_preview(req: ContentSubmitRequest):
    """Preview validation result WITHOUT saving — dry run for editors."""
    from validation import run_validation_pipeline, ContentType
    item = req.model_dump()
    ct = ContentType(item.get("content_type", "explanation"))
    result = run_validation_pipeline(item, ct, submitted_by="preview")
    return result


# ── Question stats (global difficulty / accuracy) ────────────────────────────

@app.get("/q/{question_id}/stats", tags=["questions"])
async def question_stats_endpoint(question_id: str):
    """Global stats for a specific question — used for difficulty badge in frontend."""
    return get_question_stats(question_id)


# ── Mnemonics ─────────────────────────────────────────────────────────────────

@app.get("/mnemonics/{topic}", tags=["mnemonics"])
async def mnemonics_for_topic(topic: str):
    """Returns curated high-yield mnemonics for a topic."""
    from mnemonics_data import get_mnemonics, get_all_topics
    return {"topic": topic, "mnemonics": get_mnemonics(topic), "available_topics": get_all_topics()}


@app.get("/mnemonics", tags=["mnemonics"])
async def mnemonics_index():
    """List all topics that have mnemonics."""
    from mnemonics_data import get_all_topics
    return {"topics": get_all_topics()}


# ── Admin panel ───────────────────────────────────────────────────────────────

@app.get("/admin", include_in_schema=False)
def admin_panel():
    if ADMIN.exists():
        return FileResponse(ADMIN)
    raise HTTPException(404, "Admin panel not found")


@app.get("/progress/{user_id}", tags=["legacy"])
def progress_legacy(user_id: str):
    """Backward compat — para Telegram y dev."""
    return get_progress(user_id)


@app.delete("/session/{session_id}", tags=["legacy"])
def reset_session(session_id: str):
    sessions.pop(session_id, None)
    return {"reset": True}


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
