"""
GEMA-MED — USMLE Study Agent
FastAPI backend: Claude agent + Telegram bot + web frontend

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
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

load_dotenv()

from auth import get_current_user
from db import init_db, get_progress
from agent import run_agent

# ── In-memory conversation store (session_id → message history) ──────────────
# For multi-user prod, replace with Redis. Fine for 50 users.
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
            print("python-telegram-bot not installed — skipping")

    channels = ["Web UI (http://localhost:8000)", "REST API (/docs)"]
    if telegram_started:
        channels.append("Telegram Bot")
    print(f"✅ GEMA-MED ready — {', '.join(channels)}")
    yield

    if telegram_started:
        from telegram_bot import stop_telegram_bot
        await stop_telegram_bot()


app = FastAPI(
    title="GEMA-MED USMLE Tutor",
    description="AI agent for USMLE Step 1/2/3 + ECFMG. Claude + MedQA + PubMed.",
    version="1.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # tighten to Vercel domain in prod
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Models ────────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    session_id: str | None = None
    message: str

    model_config = {"json_schema_extra": {"examples": [
        {"message": "Dame una pregunta de cardiology del Step 2"},
        {"session_id": "abc123", "message": "B"},
    ]}}


class ChatResponse(BaseModel):
    session_id: str
    response: str
    messages_in_session: int


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/", include_in_schema=False)
def frontend():
    """Serve the plain HTML fallback UI (no auth, for quick testing)."""
    return FileResponse(FRONTEND)


@app.get("/health")
def health():
    return {
        "status":   "ok",
        "agent":    "GEMA-MED",
        "model":    os.getenv("LLM_MODEL", "llama-3.3-70b-versatile"),
        "llm":      "groq" if "groq" in os.getenv("LLM_BASE_URL", "groq") else "custom",
        "telegram": bool(os.getenv("TELEGRAM_TOKEN")),
        "auth":     bool(os.getenv("CLERK_DOMAIN")),
        "db":       "postgresql" if os.getenv("DATABASE_URL") else "sqlite",
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(
    req: ChatRequest,
    user_id: str = Depends(get_current_user),
):
    """
    Main chat endpoint. Auth-aware:
    - Web (Clerk): user_id = Clerk sub, used as session prefix → web_{user_id}
    - Telegram: calls run_agent() directly, bypasses this endpoint
    - Dev (no Clerk): user_id = "dev_user"
    """
    # Web sessions are prefixed so they don't collide with Telegram sessions
    if user_id == "dev_user":
        session_id = req.session_id or str(uuid.uuid4())
    else:
        session_id = req.session_id or f"web_{user_id}"

    history = sessions[session_id]
    response_text = await run_agent(
        session_id=session_id,
        history=history,
        user_message=req.message,
    )

    return ChatResponse(
        session_id=session_id,
        response=response_text,
        messages_in_session=len(history),
    )


@app.get("/progress/{user_id}")
def progress(user_id: str):
    """
    Progress for any user_id (Clerk user_id, Telegram tg_chatid, or dev_user).
    No auth required — IDs are opaque enough for a friends app.
    """
    return get_progress(user_id)


@app.delete("/session/{session_id}")
def reset_session(session_id: str):
    sessions.pop(session_id, None)
    return {"reset": True, "session_id": session_id}


@app.get("/sessions")
def list_sessions():
    return {"active_sessions": list(sessions.keys())}


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
