"""
GEMA-MED Telegram Bot
---------------------
Corre integrado con FastAPI (via lifespan en main.py) O standalone:

    python telegram_bot.py

Requiere en .env:
    TELEGRAM_TOKEN=your_bot_token_from_@BotFather
"""

import os
import asyncio
from collections import defaultdict

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)

from agent import run_agent
from db import get_progress, init_db

# Conversaciones en memoria: chat_id → message history
tg_sessions: dict[int, list] = defaultdict(list)

# ── Keyboards ────────────────────────────────────────────────────────────────

TOPICS_KB = [
    [("🫀 Cardio", "cardiology"),     ("🫁 Pulmo",    "pulmonology")],
    [("🧠 Neuro",  "neurology"),      ("🩸 Hemato",   "hematology")],
    [("💊 Farma",  "pharmacology"),   ("🔬 Micro",    "microbiology")],
    [("🏥 Gastro", "gastroenterology"),("⚕️ Nefro",  "nephrology")],
    [("🧬 Endocr", "endocrinology"),  ("🔭 Pato",    "pathology")],
    [("🤰 OB/GYN", "ob_gyn"),         ("👶 Pediatría","pediatrics")],
    [("🧘 Psiq",   "psychiatry"),     ("📊 Bioestadística","biostatistics")],
]

STEPS_KB = [
    ("Step 1 (Ciencias básicas)", "step_1"),
    ("Step 2 CK (Conocimiento clínico)", "step_2"),
    ("Step 3 (Manejo de pacientes)", "step_3"),
]


def main_keyboard() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(label, callback_data=f"topic_{code}") for label, code in row]
        for row in TOPICS_KB
    ]
    rows.append([InlineKeyboardButton(label, callback_data=data) for label, data in STEPS_KB])
    rows.append([InlineKeyboardButton("📊 Mi Progreso", callback_data="cmd_progreso"),
                 InlineKeyboardButton("↺ Reset",        callback_data="cmd_reset")])
    return InlineKeyboardMarkup(rows)


WELCOME_MSG = (
    "🩺 *GEMA\\-MED — USMLE Tutor*\n\n"
    "Hola\\! Soy tu agente de estudio para:\n"
    "• USMLE Step 1, 2 CK, 3\n"
    "• ECFMG Certification \\(IMGs / Cuba\\)\n\n"
    "Selecciona un tema o step, o escríbeme directamente\\.\n\n"
    "*Comandos:*\n"
    "/pregunta \\[tema\\] \\[step\\] — Pregunta aleatoria\n"
    "/progreso — Tus estadísticas\n"
    "/reset — Nueva sesión"
)

# ── Helpers ──────────────────────────────────────────────────────────────────

def _session_id(chat_id: int) -> str:
    return f"tg_{chat_id}"


async def _agent_reply(update: Update, text: str, chat_id: int) -> None:
    """Send user text to Claude agent and reply with the response."""
    sid = _session_id(chat_id)
    response = await run_agent(sid, tg_sessions[chat_id], text)
    await _send_chunks(update, response)


async def _send_chunks(update: Update, text: str) -> None:
    """
    Telegram max message length is 4096 chars.
    Splits long responses and falls back to plain text if markdown parse fails.
    """
    # Light markdown cleanup: avoid unsupported MarkdownV2 chars
    safe = (text
            .replace("**", "*")
            .replace("__", "_")
            .replace("---", "—")
            .replace("```", "`"))

    chunks = [safe[i:i+3800] for i in range(0, len(safe), 3800)]
    for chunk in chunks:
        try:
            await update.effective_message.reply_text(chunk, parse_mode="Markdown")
        except Exception:
            await update.effective_message.reply_text(chunk)  # sin formato


# ── Command handlers ─────────────────────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        WELCOME_MSG,
        parse_mode="MarkdownV2",
        reply_markup=main_keyboard(),
    )


async def cmd_pregunta(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args  # e.g. /pregunta cardiology step1
    if args:
        msg = "Dame una pregunta de " + " ".join(args)
    else:
        msg = "Dame una pregunta de USMLE (tema aleatorio)"
    await _agent_reply(update, msg, update.effective_chat.id)


async def cmd_progreso(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _agent_reply(update, "Muéstrame mi progreso detallado por tema y step", update.effective_chat.id)


async def cmd_reset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    tg_sessions[chat_id].clear()
    await update.message.reply_text(
        "✅ Sesión reiniciada\\. ¡A estudiar de nuevo\\!",
        parse_mode="MarkdownV2",
        reply_markup=main_keyboard(),
    )


# ── Callback (inline buttons) ─────────────────────────────────────────────────

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    data = query.data
    chat_id = update.effective_chat.id

    if data.startswith("topic_"):
        topic = data.replace("topic_", "")
        msg = f"Dame una pregunta de {topic}"

    elif data.startswith("step_"):
        step = data.replace("step_", "")
        msg = f"Dame una pregunta del Step {step}"

    elif data == "cmd_progreso":
        msg = "Muéstrame mi progreso detallado"

    elif data == "cmd_reset":
        tg_sessions[chat_id].clear()
        await query.message.reply_text(
            "✅ Sesión reiniciada\\.",
            parse_mode="MarkdownV2",
            reply_markup=main_keyboard(),
        )
        return

    else:
        return

    thinking = await query.message.reply_text("⏳ Buscando pregunta...")
    sid = _session_id(chat_id)
    response = await run_agent(sid, tg_sessions[chat_id], msg)
    await thinking.delete()
    await _send_chunks(update, response)


# ── Text messages ─────────────────────────────────────────────────────────────

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text    = update.message.text
    chat_id = update.effective_chat.id

    thinking = await update.message.reply_text("⏳ Pensando...")
    sid      = _session_id(chat_id)
    response = await run_agent(sid, tg_sessions[chat_id], text)
    await thinking.delete()
    await _send_chunks(update, response)


# ── Bot lifecycle ─────────────────────────────────────────────────────────────

_bot_app: Application | None = None


async def start_telegram_bot() -> None:
    """
    Inicia el bot dentro del event loop existente (FastAPI compatible).
    Llama esto desde el lifespan de FastAPI.
    """
    global _bot_app
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        print("TELEGRAM_TOKEN no configurado — bot de Telegram desactivado")
        return

    _bot_app = Application.builder().token(token).build()

    _bot_app.add_handler(CommandHandler("start",    cmd_start))
    _bot_app.add_handler(CommandHandler("pregunta", cmd_pregunta))
    _bot_app.add_handler(CommandHandler("progreso", cmd_progreso))
    _bot_app.add_handler(CommandHandler("reset",    cmd_reset))
    _bot_app.add_handler(CallbackQueryHandler(handle_callback))
    _bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    await _bot_app.initialize()
    await _bot_app.start()
    await _bot_app.updater.start_polling(drop_pending_updates=True)
    print("✅ Telegram bot iniciado (polling)")


async def stop_telegram_bot() -> None:
    global _bot_app
    if _bot_app:
        await _bot_app.updater.stop()
        await _bot_app.stop()
        await _bot_app.shutdown()
        print("Telegram bot detenido")


# ── Standalone entry point ────────────────────────────────────────────────────

async def _run_standalone() -> None:
    """Corre el bot sin FastAPI (modo standalone)."""
    from dotenv import load_dotenv
    load_dotenv()
    init_db()
    await start_telegram_bot()
    try:
        await asyncio.Event().wait()   # espera indefinidamente
    except (KeyboardInterrupt, asyncio.CancelledError):
        pass
    finally:
        await stop_telegram_bot()


if __name__ == "__main__":
    asyncio.run(_run_standalone())
