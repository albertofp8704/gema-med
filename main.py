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
)
from agent import run_agent, run_agent_stream

sessions: dict[str, list] = defaultdict(list)
FRONTEND = Path(__file__).parent / "frontend.html"


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
    print(f"✅ GEMA-MED listo — {', '.join(channels)}")

    # Precalentar el banco de preguntas en background (evita timeout en primera pregunta)
    import asyncio
    from tools import _load_dataset
    asyncio.create_task(asyncio.to_thread(_load_dataset))
    print("⏳ Cargando banco de preguntas en background...")

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
        # Stream tokens
        async for chunk in run_agent_stream(session_id, history, req.message):
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
    return {
        "status": "ok", "version": "2.0.0",
        "model": os.getenv("LLM_MODEL", "llama-3.3-70b-versatile"),
        "telegram": bool(os.getenv("TELEGRAM_TOKEN")),
        "db": "postgresql" if os.getenv("DATABASE_URL") else "sqlite",
    }


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
