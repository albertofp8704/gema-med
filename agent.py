"""
GEMA-MED — Agent con OpenAI SDK (compatible con Groq).

LLM gratuito: Groq + llama-3.3-70b-versatile (14,400 req/día free tier)
Obtén tu key GRATIS en: https://console.groq.com (sin tarjeta)

Variables de entorno:
    GROQ_API_KEY   = tu key de Groq (requerido)
    LLM_MODEL      = modelo a usar (default: llama-3.3-70b-versatile)
    LLM_BASE_URL   = base URL (default: Groq)
"""

import os
import json
from openai import AsyncOpenAI

from prompts import SYSTEM_PROMPT
from tools import get_usmle_question, search_pubmed
from db import save_result, get_progress

client = AsyncOpenAI(
    api_key=os.getenv("GROQ_API_KEY", ""),
    base_url=os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1"),
)

MODEL = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_usmle_question",
            "description": (
                "Obtiene una pregunta USMLE real del banco MedQA (12,723 preguntas). "
                "Úsalo SIEMPRE que el usuario pida una pregunta, quiz, o práctica."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "Tema médico para filtrar",
                        "enum": [
                            "cardiology", "pulmonology", "nephrology", "neurology",
                            "gastroenterology", "endocrinology", "hematology",
                            "pharmacology", "microbiology", "pathology",
                            "ob_gyn", "pediatrics", "psychiatry", "biostatistics",
                        ],
                    },
                    "step": {
                        "type": "string",
                        "description": "Nivel de USMLE Step",
                        "enum": ["step1", "step2", "step3"],
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_pubmed",
            "description": "Busca referencias clínicas en PubMed para respaldar explicaciones médicas.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Consulta médica a buscar en PubMed",
                    }
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "save_result",
            "description": "Guarda el resultado de la respuesta del usuario para tracking de progreso.",
            "parameters": {
                "type": "object",
                "properties": {
                    "question_id": {"type": "string"},
                    "topic":       {"type": "string"},
                    "step":        {"type": "integer", "description": "1, 2 o 3"},
                    "correct":     {"type": "boolean"},
                },
                "required": ["question_id", "topic", "step", "correct"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_progress",
            "description": "Obtiene las estadísticas de rendimiento del usuario en esta sesión.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
]


async def run_agent(session_id: str, history: list[dict], user_message: str) -> str:
    history.append({"role": "user", "content": user_message})
    messages = list(history)

    while True:
        response = await client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT.format(session_id=session_id)},
                *messages,
            ],
            tools=TOOLS,
            tool_choice="auto",
            max_tokens=2048,
        )

        choice = response.choices[0]
        msg    = choice.message

        if choice.finish_reason == "tool_calls" and msg.tool_calls:
            # Agrega la respuesta del asistente con sus tool calls
            messages.append({
                "role":       "assistant",
                "content":    msg.content,
                "tool_calls": [tc.model_dump() for tc in msg.tool_calls],
            })

            # Ejecuta cada tool call y agrega el resultado
            for tc in msg.tool_calls:
                args   = json.loads(tc.function.arguments)
                result = await _dispatch(tc.function.name, args, session_id)
                messages.append({
                    "role":         "tool",
                    "tool_call_id": tc.id,
                    "content":      json.dumps(result, ensure_ascii=False),
                })
        else:
            text = msg.content or ""
            history.append({"role": "assistant", "content": text})
            return text


async def _dispatch(name: str, inputs: dict, session_id: str) -> dict:
    if name == "get_usmle_question":
        return get_usmle_question(
            topic=inputs.get("topic"),
            step=inputs.get("step"),
        )

    if name == "search_pubmed":
        return {"results": await search_pubmed(inputs["query"])}

    if name == "save_result":
        save_result(
            user_id=session_id,
            question_id=inputs["question_id"],
            topic=inputs.get("topic", "general"),
            step=inputs.get("step", 1),
            correct=inputs["correct"],
        )
        return {"saved": True}

    if name == "get_progress":
        return get_progress(session_id)

    return {"error": f"Unknown tool: {name}"}
