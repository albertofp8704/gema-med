"""
GEMA-MED — Agent optimizado para velocidad.

Estrategia:
  - Preguntas USMLE: fetch en Python → 1 sola llamada a Groq (no tool calls)
  - Respuestas/explicaciones: 1 llamada con contexto de la pregunta
  - General chat: 1 llamada sin tools
  → Reduce de 2-3 roundtrips Groq a 1 por request
"""

import os
import re
import json
from openai import AsyncOpenAI

from prompts import SYSTEM_PROMPT
from tools import get_usmle_question, search_pubmed, TOPIC_KEYWORDS
from db import (
    save_result, get_progress, get_weakness_report,
    set_study_plan, get_study_plan, update_study_phase,
)

client = AsyncOpenAI(
    api_key=os.getenv("GROQ_API_KEY", ""),
    base_url=os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1"),
)

MODEL      = os.getenv("LLM_MODEL", "llama-3.1-8b-instant")
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "1000"))

# Last question per session — needed to save results after answering
_session_last_question: dict[str, dict] = {}

# ── Detección rápida de intención ─────────────────────────────────────────────

_QUESTION_WORDS = {"pregunta","question","dame","give","quiz","otra","next","siguiente",
                   "siguiente","another","diagnóstico","simulacro","practice"}
_ANSWER_LETTERS = {"a","b","c","d"}
_TOPIC_RE = re.compile(
    r"\b(" + "|".join(TOPIC_KEYWORDS.keys()) + r")\b", re.I
)
_STEP_RE = re.compile(r"\bstep\s*([123])\b", re.I)


def _detect_intent(text: str) -> str:
    """Returns: 'question' | 'answer' | 'plan' | 'progress' | 'general'"""
    low = text.strip().lower()
    # Single letter → answer to active question
    if len(low) <= 2 and low.strip() in _ANSWER_LETTERS:
        return "answer"
    # Plan-related
    if any(w in low for w in ("mi plan","fecha","examen","objetivo","schedule","semana")):
        return "plan"
    # Progress-related
    if any(w in low for w in ("progreso","progress","debilidad","weakness","estadística","stats")):
        return "progress"
    # Question request
    if any(w in low for w in _QUESTION_WORDS):
        return "question"
    return "general"


# ── Fast path: 1 llamada Groq sin tool calls ──────────────────────────────────

async def _fast_question(session_id: str, history: list, topic: str | None, step: str | None) -> str:
    """Fetch pregunta en Python + 1 Groq call para formatearla. Evita 1 roundtrip."""
    q = get_usmle_question(topic=topic, step=step)
    _session_last_question[session_id] = q  # store for save_result after answer

    display_topic = (topic or q["topic"]).replace("_", " ").title()
    step_num = step.replace("step","") if step else "1"

    opts_text = "\n".join(f"{k}) {v}" for k, v in q["options"].items())
    q_block = (
        f"PREGUNTA DISPONIBLE (ID: {q['id']} | Tema: {q['topic']} | Source: {q['source']}):\n"
        f"{q['question']}\n\nOpciones:\n{opts_text}\n"
        f"Respuesta correcta: {q['correct_letter']}) {q['correct_answer']}\n"
        f"Explicación base: {q.get('explanation','')[:300]}"
    )

    system = (
        SYSTEM_PROMPT.replace("{session_id}", session_id)
        + f"\n\n---\n{q_block}\n---\n"
        + f"INSTRUCCION: Presenta la pregunta usando el formato UWorld exacto. "
        + f"El encabezado DEBE ser exactamente: '**USMLE Step {step_num} -- {display_topic}**'. "
        + "NO cambies el tema del encabezado. NO reveles la respuesta correcta. "
        + "Termina con '*(Escribe tu respuesta: A, B, C o D)*'"
    )

    resp = await client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system},
            *history[:-1],  # sin el último mensaje del usuario
            {"role": "user",   "content": "Presenta la siguiente pregunta USMLE."},
        ],
        max_tokens=700,
        temperature=0.2,
    )
    return resp.choices[0].message.content or ""


async def _fast_explanation(session_id: str, history: list, letter: str) -> str:
    """1 Groq call con contexto completo de la conversación para generar explicación."""
    resp = await client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT.replace("{session_id}", session_id)},
            *history,
        ],
        max_tokens=MAX_TOKENS,
        temperature=0.2,
    )
    return resp.choices[0].message.content or ""


async def _fast_general(session_id: str, history: list) -> str:
    """Chat general sin tool calls — 1 roundtrip."""
    resp = await client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT.replace("{session_id}", session_id)},
            *history,
        ],
        max_tokens=MAX_TOKENS,
        temperature=0.3,
    )
    return resp.choices[0].message.content or ""


# ── Tool use (plan, progress, search) ─────────────────────────────────────────

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_progress",
            "description": "Obtiene estadísticas de rendimiento del usuario.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_weakness_report",
            "description": "Identifica temas con accuracy < 60%.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "set_study_plan",
            "description": "Guarda el plan de estudio cuando el usuario indica su fecha de examen.",
            "parameters": {
                "type": "object",
                "properties": {
                    "target_date":     {"type": "string", "description": "Fecha YYYY-MM-DD"},
                    "plan_type":       {"type": "string", "description": "12_week o 6_week"},
                    "daily_questions": {"type": "integer"},
                    "current_week":    {"type": "integer"},
                },
                "required": ["target_date"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_study_plan",
            "description": "Recupera el plan de estudio guardado.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_pubmed",
            "description": "Busca referencias en PubMed para respaldar explicaciones.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                },
                "required": ["query"],
            },
        },
    },
]


async def _tool_call_path(session_id: str, history: list) -> str:
    """Tool use para plan/progress/search — hasta 4 iteraciones."""
    messages = list(history)
    for _ in range(4):
        try:
            resp = await client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT.replace("{session_id}", session_id)},
                    *messages,
                ],
                tools=TOOLS,
                tool_choice="auto",
                parallel_tool_calls=False,
                max_tokens=MAX_TOKENS,
            )
        except Exception as e:
            print(f"[TOOL ERROR] {e}")
            return await _fast_general(session_id, history)

        choice = resp.choices[0]
        msg    = choice.message

        if choice.finish_reason == "tool_calls" and msg.tool_calls:
            messages.append({
                "role": "assistant", "content": msg.content,
                "tool_calls": [tc.model_dump() for tc in msg.tool_calls],
            })
            for tc in msg.tool_calls:
                try:
                    args   = json.loads(tc.function.arguments)
                    result = await _dispatch_tool(tc.function.name, args, session_id)
                except Exception as e:
                    result = {"error": str(e)}
                messages.append({
                    "role": "tool", "tool_call_id": tc.id,
                    "content": json.dumps(result, ensure_ascii=False),
                })
        else:
            return msg.content or ""

    return "No pude completar la solicitud. Intenta de nuevo."


async def _dispatch_tool(name: str, inputs: dict, session_id: str) -> dict:
    if name == "get_progress":
        return get_progress(session_id)
    if name == "get_weakness_report":
        return get_weakness_report(session_id)
    if name == "set_study_plan":
        return set_study_plan(
            user_id=session_id,
            target_date=inputs["target_date"],
            plan_type=inputs.get("plan_type", "12_week"),
            daily_questions=inputs.get("daily_questions", 60),
            current_week=inputs.get("current_week", 1),
        )
    if name == "get_study_plan":
        return get_study_plan(session_id)
    if name == "search_pubmed":
        return {"results": await search_pubmed(inputs["query"])}
    return {"error": f"Unknown tool: {name}"}


# ── Streaming entry point ─────────────────────────────────────────────────────

async def run_agent_stream(session_id: str, history: list[dict], user_message: str):
    """
    Async generator — yields text chunks for Server-Sent Events streaming.
    Same logic as run_agent but streams tokens as they arrive from Groq.
    """
    history.append({"role": "user", "content": user_message})
    intent = _detect_intent(user_message)
    full_text = ""

    try:
        if intent == "question":
            topic_m = _TOPIC_RE.search(user_message)
            step_m  = _STEP_RE.search(user_message)
            topic   = topic_m.group(0).lower() if topic_m else None
            step    = f"step{step_m.group(1)}" if step_m else None

            q = get_usmle_question(topic=topic, step=step)
            _session_last_question[session_id] = q

            # Use the REQUESTED topic as the display label (not Groq's guess)
            display_topic = (topic or q["topic"]).replace("_", " ").title()
            step_num = step.replace("step","") if step else "1"

            opts_text = "\n".join(f"{k}) {v}" for k, v in q["options"].items())
            q_block = (
                f"\n\nPREGUNTA (ID:{q['id']} | Tema:{q['topic']}):\n"
                f"{q['question']}\n\nOpciones:\n{opts_text}\n"
                f"Respuesta correcta: {q['correct_letter']}) {q['correct_answer']}\n"
                f"Explicación base: {q.get('explanation','')[:300]}"
            )
            system = (
                SYSTEM_PROMPT.replace("{session_id}", session_id) + q_block
                + f"\n\nINSTRUCCIÓN: Presenta la pregunta en formato UWorld exacto. "
                + f"El encabezado DEBE ser exactamente: '**USMLE Step {step_num} — {display_topic}**'. "
                + "NO cambies el tema del encabezado. NO reveles la respuesta. "
                + "Termina con '*(Escribe tu respuesta: A, B, C o D)*'"
            )
            stream = await client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": system},
                    *history[:-1],
                    {"role": "user", "content": "Presenta la siguiente pregunta USMLE."},
                ],
                stream=True, max_tokens=700, temperature=0.2,
            )

        elif intent == "answer":
            stream = await client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT.replace("{session_id}", session_id)},
                    *history,
                ],
                stream=True, max_tokens=MAX_TOKENS, temperature=0.2,
            )

        elif intent in ("plan", "progress"):
            # Tool calls can't stream — fall back to full response then yield
            text = await _tool_call_path(session_id, history)
            history.append({"role": "assistant", "content": text})
            yield text
            return

        else:
            stream = await client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT.replace("{session_id}", session_id)},
                    *history,
                ],
                stream=True, max_tokens=MAX_TOKENS, temperature=0.3,
            )

        # Yield chunks as they arrive
        async for chunk in stream:
            delta = chunk.choices[0].delta.content or ""
            if delta:
                full_text += delta
                yield delta

        history.append({"role": "assistant", "content": full_text})

        # Post-stream: save result if it was an answer
        if intent == "answer":
            last_q = _session_last_question.get(session_id)
            if last_q:
                first = full_text[:120].lower()
                is_correct = "correcto" in first and "incorrecto" not in first
                try:
                    save_result(
                        user_id=session_id,
                        question_id=last_q.get("id", "unknown"),
                        topic=last_q.get("topic", "general"),
                        step=last_q.get("step", 1),
                        correct=is_correct,
                    )
                except Exception as e:
                    print(f"[save_result error] {e}")

    except Exception as e:
        print(f"[STREAM ERROR] {type(e).__name__}: {e}")
        err = f"Error: {str(e)[:200]}"
        yield err
        history.append({"role": "assistant", "content": err})


# ── Non-streaming entry point (kept for compatibility) ────────────────────────

async def run_agent(session_id: str, history: list[dict], user_message: str) -> str:
    history.append({"role": "user", "content": user_message})

    intent = _detect_intent(user_message)

    try:
        if intent == "question":
            # Fast path: 1 API call (no tool calls)
            topic_m = _TOPIC_RE.search(user_message)
            step_m  = _STEP_RE.search(user_message)
            topic   = topic_m.group(0).lower() if topic_m else None
            step    = f"step{step_m.group(1)}" if step_m else None
            text = await _fast_question(session_id, history, topic, step)

        elif intent == "answer":
            # Fast path: 1 API call con historial (el modelo ve la pregunta anterior)
            text = await _fast_explanation(session_id, history, user_message.strip().upper())
            # Save result — detect correct/incorrect from first line of response
            last_q = _session_last_question.get(session_id)
            if last_q:
                first_line = text[:120].lower()
                is_correct = "correcto" in first_line and "incorrecto" not in first_line
                try:
                    save_result(
                        user_id=session_id,
                        question_id=last_q.get("id", "unknown"),
                        topic=last_q.get("topic", "general"),
                        step=last_q.get("step", 1),
                        correct=is_correct,
                    )
                except Exception as e:
                    print(f"[save_result error] {e}")

        elif intent in ("plan", "progress"):
            # Tool use para operaciones de DB
            text = await _tool_call_path(session_id, history)

        else:
            # Chat general — 1 call sin tools
            text = await _fast_general(session_id, history)

    except Exception as e:
        print(f"[AGENT ERROR] {type(e).__name__}: {e}")
        text = f"Error: {str(e)[:200]}"

    history.append({"role": "assistant", "content": text})
    return text
