"""
GEMA-MED — Agent con OpenAI SDK (compatible con Groq).

LLM gratuito: Groq + llama-3.3-70b-versatile (14,400 req/día free tier)
Obtén tu key GRATIS en: https://console.groq.com (sin tarjeta)
"""

import os
import json
from openai import AsyncOpenAI

from prompts import SYSTEM_PROMPT
from tools import get_usmle_question, search_pubmed
from db import (
    save_result, get_progress, get_weakness_report,
    set_study_plan, get_study_plan, update_study_phase,
)

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
                "Obtiene una pregunta USMLE real del banco MedQA (10,000+ preguntas). "
                "Úsalo SIEMPRE que el usuario pida una pregunta, quiz, práctica, diagnóstico o simulacro."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "Tema médico para filtrar (omitir para preguntas mixtas en simulacro/diagnóstico)",
                        "enum": [
                            "cardiology", "pulmonology", "nephrology", "neurology",
                            "gastroenterology", "endocrinology", "hematology",
                            "pharmacology", "microbiology", "pathology",
                            "ob_gyn", "pediatrics", "psychiatry", "biostatistics",
                        ],
                    },
                    "step": {
                        "type": "string",
                        "description": "Nivel USMLE",
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
            "description": "Busca referencias clínicas en PubMed para respaldar explicaciones.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Consulta médica"},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "save_result",
            "description": "Guarda el resultado de una respuesta para tracking de progreso.",
            "parameters": {
                "type": "object",
                "properties": {
                    "question_id": {"type": "string"},
                    "topic":       {"type": "string"},
                    "step":        {"type": "integer"},
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
            "description": "Obtiene estadísticas de rendimiento del usuario: total de preguntas, precisión por tema, progreso del día.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_weakness_report",
            "description": "Identifica los sistemas con accuracy < 60% (debilidades) para priorizar revisión.",
            "parameters": {
                "type": "object",
                "properties": {
                    "threshold": {
                        "type": "number",
                        "description": "Umbral de accuracy para considerar debilidad (default: 60)",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "set_study_plan",
            "description": (
                "Guarda el plan de estudio del usuario. "
                "Úsalo cuando el usuario diga su fecha objetivo de examen."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "target_date": {
                        "type": "string",
                        "description": "Fecha objetivo en formato YYYY-MM-DD",
                    },
                    "daily_goal": {
                        "type": "integer",
                        "description": "Preguntas por día (default: 40)",
                    },
                    "current_system": {
                        "type": "string",
                        "description": "Sistema de inicio (default: cardiology)",
                    },
                },
                "required": ["target_date"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_study_plan",
            "description": "Recupera el plan de estudio guardado: fecha objetivo, sistema actual, semanas restantes, cronograma.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_study_phase",
            "description": "Actualiza el sistema o fase actual del plan de estudio.",
            "parameters": {
                "type": "object",
                "properties": {
                    "current_system": {"type": "string"},
                    "current_phase": {
                        "type": "string",
                        "enum": ["planning", "diagnostic", "systems", "review", "simulation", "final"],
                    },
                },
            },
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
                {"role": "system", "content": SYSTEM_PROMPT.replace("{session_id}", session_id)},
                *messages,
            ],
            tools=TOOLS,
            tool_choice="auto",
            max_tokens=2048,
        )

        choice = response.choices[0]
        msg    = choice.message

        if choice.finish_reason == "tool_calls" and msg.tool_calls:
            messages.append({
                "role":       "assistant",
                "content":    msg.content,
                "tool_calls": [tc.model_dump() for tc in msg.tool_calls],
            })

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

    if name == "get_weakness_report":
        return get_weakness_report(session_id, threshold=inputs.get("threshold", 60.0))

    if name == "set_study_plan":
        return set_study_plan(
            user_id=session_id,
            target_date=inputs["target_date"],
            daily_goal=inputs.get("daily_goal", 40),
            current_system=inputs.get("current_system", "cardiology"),
            current_phase="diagnostic",
        )

    if name == "get_study_plan":
        return get_study_plan(session_id)

    if name == "update_study_phase":
        return update_study_phase(
            user_id=session_id,
            current_system=inputs.get("current_system"),
            current_phase=inputs.get("current_phase"),
        )

    return {"error": f"Unknown tool: {name}"}
