"""
Database layer — SQLite (dev) / PostgreSQL (prod via DATABASE_URL).
SQLAlchemy Core — mismo SQL en ambos motores.
"""

import os
import sqlalchemy as sa
from datetime import datetime, date

_raw = os.getenv("DATABASE_URL", "sqlite:///./gema_med.db")
DATABASE_URL = _raw.replace("postgres://", "postgresql://", 1) if _raw.startswith("postgres://") else _raw

engine   = sa.create_engine(DATABASE_URL, pool_pre_ping=True)
metadata = sa.MetaData()

# ── Tabla: usuarios ───────────────────────────────────────────────────────────

users_tbl = sa.Table(
    "users", metadata,
    sa.Column("id",            sa.Integer, primary_key=True, autoincrement=True),
    sa.Column("username",      sa.String,  unique=True, nullable=False, index=True),
    sa.Column("password_hash", sa.String,  nullable=False),
    sa.Column("display_name",  sa.String,  nullable=True),
    sa.Column("created_at",    sa.String,  nullable=False),
)

# ── Tabla: resultados de preguntas ────────────────────────────────────────────

results_tbl = sa.Table(
    "results", metadata,
    sa.Column("id",          sa.Integer, primary_key=True, autoincrement=True),
    sa.Column("user_id",     sa.String,  nullable=False, index=True),
    sa.Column("question_id", sa.String,  nullable=False),
    sa.Column("topic",       sa.String,  default="general"),
    sa.Column("step",        sa.Integer, default=1),
    sa.Column("correct",     sa.Integer, nullable=False),
    sa.Column("timestamp",   sa.String,  nullable=False),
)

# ── Tabla: content validation pipeline ───────────────────────────────────────

content_items_tbl = sa.Table(
    "content_items", metadata,
    sa.Column("id",             sa.String,  primary_key=True),
    sa.Column("content_type",   sa.String,  nullable=False),          # question|explanation|general
    sa.Column("topic",          sa.String,  nullable=True),
    sa.Column("content",        sa.Text,    nullable=False),           # stem or text
    sa.Column("choices",        sa.Text,    nullable=True),            # JSON
    sa.Column("correct_answer", sa.String,  nullable=True),
    sa.Column("explanation",    sa.Text,    nullable=True),
    sa.Column("source_url",     sa.String,  nullable=True),
    sa.Column("source_type",    sa.String,  nullable=True),
    sa.Column("risk_level",     sa.String,  default="low"),
    sa.Column("status",         sa.String,  default="draft", index=True),
    sa.Column("validation_report", sa.Text, nullable=True),           # JSON
    sa.Column("submitted_by",   sa.String,  nullable=True),
    sa.Column("reviewed_by",    sa.String,  nullable=True),
    sa.Column("review_notes",   sa.Text,    nullable=True),
    sa.Column("version",        sa.Integer, default=1),
    sa.Column("created_at",     sa.String,  nullable=False),
    sa.Column("updated_at",     sa.String,  nullable=False),
    sa.Column("last_verified_at", sa.String, nullable=True),
)

content_audit_tbl = sa.Table(
    "content_audit", metadata,
    sa.Column("id",          sa.Integer, primary_key=True, autoincrement=True),
    sa.Column("item_id",     sa.String,  nullable=False, index=True),
    sa.Column("action",      sa.String,  nullable=False),             # submitted|validated|approved|rejected|archived
    sa.Column("from_status", sa.String,  nullable=True),
    sa.Column("to_status",   sa.String,  nullable=True),
    sa.Column("actor",       sa.String,  nullable=True),              # user_id or "system"
    sa.Column("notes",       sa.Text,    nullable=True),
    sa.Column("timestamp",   sa.String,  nullable=False),
)

# ── Tabla: estadísticas globales por pregunta ────────────────────────────────

question_stats_tbl = sa.Table(
    "question_stats", metadata,
    sa.Column("question_id",       sa.String,  primary_key=True),
    sa.Column("total_attempts",    sa.Integer, default=0,  nullable=False),
    sa.Column("correct_attempts",  sa.Integer, default=0,  nullable=False),
    sa.Column("last_updated",      sa.String,  nullable=True),
)

# ── Tabla: planes de estudio ──────────────────────────────────────────────────

study_plans_tbl = sa.Table(
    "study_plans", metadata,
    sa.Column("user_id",          sa.String,  primary_key=True),
    sa.Column("target_date",      sa.String,  nullable=True),
    sa.Column("plan_type",        sa.String,  default="12_week"),
    sa.Column("daily_questions",  sa.Integer, default=60),
    sa.Column("language",         sa.String,  default="bilingual"),
    sa.Column("current_week",     sa.Integer, default=1),
    sa.Column("current_system",   sa.String,  default="mixed"),
    sa.Column("current_phase",    sa.String,  default="diagnostic"),
    sa.Column("created_at",       sa.String,  nullable=False),
    sa.Column("updated_at",       sa.String,  nullable=False),
)


def init_db() -> None:
    metadata.create_all(engine)


# ── Planes de 12 semanas ──────────────────────────────────────────────────────

TWELVE_WEEK_PLAN = [
    {"week": 1,  "name": "Base y diagnóstico",      "phase": "diagnostic",  "system": "mixed",        "emoji": "🔍", "daily": 40,
     "activities": ["Examen diagnóstico (40 Qs mixtas)", "Definir calendario semanal", "Organizar recursos (FA, Pathoma, Anki)", "Empezar Anki top cards"]},
    {"week": 2,  "name": "Bioquímica",              "phase": "systems",     "system": "biochemistry",  "emoji": "⚗️", "daily": 60,
     "activities": ["First Aid: Biochemistry chapter", "Pathoma: General Principles", "Anki: Biochemistry deck", "60 preguntas/día"]},
    {"week": 3,  "name": "Fisiología",              "phase": "systems",     "system": "physiology",    "emoji": "🫀", "daily": 60,
     "activities": ["First Aid: Physiology systems", "Sketchy: Cardio fisiología", "Correlacionar con patología", "60 preguntas/día"]},
    {"week": 4,  "name": "Patología",               "phase": "systems",     "system": "pathology",     "emoji": "🔬", "daily": 60,
     "activities": ["Pathoma completo (Goljan)", "First Aid: Pathology highlights", "Anotar errores en spreadsheet", "60 preguntas/día"]},
    {"week": 5,  "name": "Microbiología",           "phase": "systems",     "system": "microbiology",  "emoji": "🦠", "daily": 60,
     "activities": ["Sketchy Micro (bacterias, virus, hongos)", "First Aid: Microbiology", "Anki: Micro bugs", "60 preguntas/día"]},
    {"week": 6,  "name": "Farmacología",            "phase": "systems",     "system": "pharmacology",  "emoji": "💊", "daily": 60,
     "activities": ["Sketchy Pharm (todos los mecanismos)", "First Aid: Pharmacology", "Revisar efectos adversos clave", "60 preguntas/día"]},
    {"week": 7,  "name": "Consolidación — Débiles", "phase": "review",      "system": "mixed",         "emoji": "💪", "daily": 80,
     "activities": ["Revisar incorrectas de semanas 2-6", "Segundo pase por temas débiles (<60%)", "Mini bloques cronometrados (20 Qs)", "80 preguntas/día"]},
    {"week": 8,  "name": "Cardio + Pulmo",          "phase": "review",      "system": "cardiology",    "emoji": "🫁", "daily": 80,
     "activities": ["FA: Cardiovascular + Pulmonary", "Sketchy: Cardio drugs repaso", "Bloques cronometrados cardio", "80 preguntas/día"]},
    {"week": 9,  "name": "Renal + GI",              "phase": "review",      "system": "nephrology",    "emoji": "🏥", "daily": 80,
     "activities": ["FA: Renal + GI/Liver", "Pathoma: Renal y GI", "Revisar acid-base", "80 preguntas/día"]},
    {"week": 10, "name": "Neuro + Psiquiatría",     "phase": "review",      "system": "neurology",     "emoji": "🧠", "daily": 80,
     "activities": ["FA: Neurology + Psychiatry", "Sketchy: Psych meds", "Bloques mixtos completos", "80 preguntas/día"]},
    {"week": 11, "name": "Simulación I",            "phase": "simulation",  "system": "mixed",         "emoji": "🎯", "daily": 80,
     "activities": ["2 NBME Self-Assessments", "Bloques de 40 preguntas (60 min)", "Revisar TODAS las incorrectas", "Sin material nuevo"]},
    {"week": 12, "name": "Simulación II + Cierre",  "phase": "simulation",  "system": "mixed",         "emoji": "🏁", "daily": 40,
     "activities": ["FA completo (último repaso)", "Solo errores repetidos", "Dormir bien", "Descanso 3-5 días antes del examen"]},
]

SIX_WEEK_PLAN = [
    {"week": 1,  "name": "Diagnóstico + Bioquímica", "phase": "diagnostic", "system": "biochemistry",  "emoji": "🔍", "daily": 60,
     "activities": ["Diagnóstico inicial 40 Qs", "FA + Pathoma: Biochem/Physio", "60-80 preguntas/día"]},
    {"week": 2,  "name": "Patología + Micro",        "phase": "systems",    "system": "pathology",     "emoji": "🔬", "daily": 80,
     "activities": ["Pathoma: Pathology completo", "Sketchy Micro: bacterias/virus", "80 preguntas/día"]},
    {"week": 3,  "name": "Farmacología + Cardio",    "phase": "systems",    "system": "pharmacology",  "emoji": "💊", "daily": 80,
     "activities": ["Sketchy Pharm completo", "FA: Cardio + Pulmo", "80 preguntas/día"]},
    {"week": 4,  "name": "Renal + GI + Neuro",      "phase": "systems",    "system": "nephrology",    "emoji": "🏥", "daily": 80,
     "activities": ["FA: Renal, GI, Neuro", "Revisar incorrectas semanales", "80 preguntas/día"]},
    {"week": 5,  "name": "Consolidación intensiva",  "phase": "review",     "system": "mixed",         "emoji": "💪", "daily": 80,
     "activities": ["Revisar todos los temas débiles", "Bloques cronometrados 40 Qs", "NBME Free: 1 examen"]},
    {"week": 6,  "name": "Simulación + Cierre",      "phase": "simulation", "system": "mixed",         "emoji": "🏁", "daily": 40,
     "activities": ["2 NBME Self-Assessments", "FA: repaso final", "Descanso previo al examen"]},
]

PLAN_TEMPLATES = {
    "12_week": TWELVE_WEEK_PLAN,
    "6_week":  SIX_WEEK_PLAN,
}


def get_week_detail(plan_type: str, week: int) -> dict:
    template = PLAN_TEMPLATES.get(plan_type, TWELVE_WEEK_PLAN)
    week = max(1, min(week, len(template)))
    return template[week - 1]


# ── Funciones: content validation pipeline ───────────────────────────────────

def submit_content_item(item: dict, submitted_by: str = "system") -> dict:
    """Submit a content item through the validation pipeline."""
    import json as _json
    from validation import run_validation_pipeline, ContentType
    now = datetime.now().isoformat()

    # Detect content type
    ct = ContentType(item.get("content_type", "explanation"))

    # Run automatic validation
    report = run_validation_pipeline(item, ct, submitted_by)
    item_id = report["id"]

    with engine.begin() as conn:
        # Check if already exists (update version)
        existing = conn.execute(
            sa.select(content_items_tbl.c.version)
            .where(content_items_tbl.c.id == item_id)
        ).fetchone()

        if existing:
            version = existing.version + 1
            conn.execute(
                content_items_tbl.update()
                .where(content_items_tbl.c.id == item_id)
                .values(
                    status=report["final_status"],
                    risk_level=report["risk_level"],
                    validation_report=_json.dumps(report),
                    version=version,
                    updated_at=now,
                )
            )
        else:
            version = 1
            conn.execute(content_items_tbl.insert().values(
                id=item_id,
                content_type=ct.value,
                topic=item.get("topic"),
                content=item.get("content") or item.get("stem", ""),
                choices=_json.dumps(item.get("choices")) if item.get("choices") else None,
                correct_answer=item.get("correct_answer"),
                explanation=item.get("explanation"),
                source_url=item.get("source_url") or item.get("source"),
                source_type=item.get("source_type"),
                risk_level=report["risk_level"],
                status=report["final_status"],
                validation_report=_json.dumps(report),
                submitted_by=submitted_by,
                version=1,
                created_at=now,
                updated_at=now,
            ))

        # Audit log
        conn.execute(content_audit_tbl.insert().values(
            item_id=item_id,
            action="submitted",
            from_status="draft",
            to_status=report["final_status"],
            actor=submitted_by,
            notes=f"Auto-validation: {len(report['errors'])} errors, risk={report['risk_level']}",
            timestamp=now,
        ))

    return {**report, "version": version}


def review_content_item(
    item_id: str,
    decision: str,          # "approved" | "rejected"
    reviewed_by: str,
    notes: str = "",
) -> dict:
    """Human review decision — only humans can approve or reject."""
    if decision not in ("approved", "rejected"):
        raise ValueError("decision must be 'approved' or 'rejected'")

    now = datetime.now().isoformat()
    with engine.begin() as conn:
        row = conn.execute(
            sa.select(content_items_tbl)
            .where(content_items_tbl.c.id == item_id)
        ).fetchone()

        if not row:
            raise ValueError(f"Content item '{item_id}' not found")

        if row.status == "approved" and decision == "approved":
            return {"message": "Already approved", "status": "approved"}

        old_status = row.status
        conn.execute(
            content_items_tbl.update()
            .where(content_items_tbl.c.id == item_id)
            .values(
                status=decision,
                reviewed_by=reviewed_by,
                review_notes=notes,
                last_verified_at=now,
                updated_at=now,
            )
        )
        conn.execute(content_audit_tbl.insert().values(
            item_id=item_id,
            action=decision,
            from_status=old_status,
            to_status=decision,
            actor=reviewed_by,
            notes=notes or f"Human review by {reviewed_by}",
            timestamp=now,
        ))

    return {"item_id": item_id, "status": decision, "reviewed_by": reviewed_by}


def get_review_queue(status: str = "needs_review", limit: int = 50) -> list:
    """Get items waiting for human review."""
    with engine.connect() as conn:
        rows = conn.execute(
            sa.select(content_items_tbl)
            .where(content_items_tbl.c.status == status)
            .order_by(content_items_tbl.c.created_at.desc())
            .limit(limit)
        ).fetchall()
    return [dict(r._mapping) for r in rows]


def get_content_audit_trail(item_id: str) -> list:
    """Full audit trail for a content item."""
    with engine.connect() as conn:
        rows = conn.execute(
            sa.select(content_audit_tbl)
            .where(content_audit_tbl.c.item_id == item_id)
            .order_by(content_audit_tbl.c.timestamp)
        ).fetchall()
    return [dict(r._mapping) for r in rows]


def get_pipeline_stats() -> dict:
    """Summary statistics for the content pipeline."""
    with engine.connect() as conn:
        by_status = conn.execute(
            sa.select(
                content_items_tbl.c.status,
                sa.func.count().label("count"),
            ).group_by(content_items_tbl.c.status)
        ).fetchall()
        by_risk = conn.execute(
            sa.select(
                content_items_tbl.c.risk_level,
                sa.func.count().label("count"),
            ).group_by(content_items_tbl.c.risk_level)
        ).fetchall()
    return {
        "by_status": {r.status: r.count for r in by_status},
        "by_risk":   {r.risk_level: r.count for r in by_risk},
    }


# ── Funciones: usuarios ───────────────────────────────────────────────────────

def create_user(username: str, password_hash: str, display_name: str = None) -> dict:
    now = datetime.now().isoformat()
    with engine.begin() as conn:
        result = conn.execute(
            users_tbl.insert().values(
                username=username.lower().strip(),
                password_hash=password_hash,
                display_name=display_name or username,
                created_at=now,
            )
        )
        return {"id": result.inserted_primary_key[0], "username": username, "display_name": display_name or username}


def get_user_by_username(username: str) -> dict | None:
    with engine.connect() as conn:
        row = conn.execute(
            users_tbl.select().where(users_tbl.c.username == username.lower().strip())
        ).fetchone()
    if not row:
        return None
    return {"id": row.id, "username": row.username, "password_hash": row.password_hash, "display_name": row.display_name}


def get_user_by_id(user_id: str) -> dict | None:
    try:
        uid = int(user_id)
    except (ValueError, TypeError):
        return None
    with engine.connect() as conn:
        row = conn.execute(users_tbl.select().where(users_tbl.c.id == uid)).fetchone()
    if not row:
        return None
    return {"id": row.id, "username": row.username, "display_name": row.display_name}


# ── Funciones: resultados ─────────────────────────────────────────────────────

def save_result(user_id: str, question_id: str, topic: str, step: int, correct: bool) -> None:
    now = datetime.now().isoformat()
    with engine.begin() as conn:
        conn.execute(results_tbl.insert().values(
            user_id=user_id, question_id=question_id, topic=topic or "general",
            step=step or 1, correct=int(correct), timestamp=now,
        ))
        # Upsert global question stats
        existing = conn.execute(
            sa.select(question_stats_tbl)
            .where(question_stats_tbl.c.question_id == question_id)
        ).fetchone()
        if existing:
            conn.execute(
                question_stats_tbl.update()
                .where(question_stats_tbl.c.question_id == question_id)
                .values(
                    total_attempts=existing.total_attempts + 1,
                    correct_attempts=existing.correct_attempts + int(correct),
                    last_updated=now,
                )
            )
        else:
            conn.execute(question_stats_tbl.insert().values(
                question_id=question_id,
                total_attempts=1,
                correct_attempts=int(correct),
                last_updated=now,
            ))


def get_question_stats(question_id: str) -> dict:
    with engine.connect() as conn:
        row = conn.execute(
            sa.select(question_stats_tbl)
            .where(question_stats_tbl.c.question_id == question_id)
        ).fetchone()
    if not row or row.total_attempts == 0:
        return {"question_id": question_id, "total": 0, "correct": 0, "accuracy": None, "difficulty": "new"}
    total    = row.total_attempts
    correct  = row.correct_attempts
    accuracy = round(correct / total * 100, 1)
    if accuracy >= 70:
        difficulty = "easy"
    elif accuracy >= 40:
        difficulty = "medium"
    else:
        difficulty = "hard"
    return {"question_id": question_id, "total": total, "correct": correct, "accuracy": accuracy, "difficulty": difficulty}


def get_progress(user_id: str) -> dict:
    with engine.connect() as conn:
        agg = conn.execute(
            sa.select(
                sa.func.count().label("total"),
                sa.func.coalesce(sa.func.sum(results_tbl.c.correct), 0).label("correct"),
            ).where(results_tbl.c.user_id == user_id)
        ).fetchone()

        by_topic = conn.execute(
            sa.select(
                results_tbl.c.topic,
                sa.func.count().label("total"),
                sa.func.coalesce(sa.func.sum(results_tbl.c.correct), 0).label("correct"),
            ).where(results_tbl.c.user_id == user_id)
             .group_by(results_tbl.c.topic)
             .order_by(sa.func.count().desc())
        ).fetchall()

        by_step = conn.execute(
            sa.select(
                results_tbl.c.step,
                sa.func.count().label("total"),
                sa.func.coalesce(sa.func.sum(results_tbl.c.correct), 0).label("correct"),
            ).where(results_tbl.c.user_id == user_id)
             .group_by(results_tbl.c.step)
        ).fetchall()

        today = date.today().isoformat()
        today_row = conn.execute(
            sa.select(sa.func.count().label("total"))
            .where(results_tbl.c.user_id == user_id)
            .where(results_tbl.c.timestamp.like(f"{today}%"))
        ).fetchone()

    total   = agg.total   or 0
    correct = int(agg.correct or 0)

    return {
        "user_id":          user_id,
        "total_answered":   total,
        "total_correct":    correct,
        "overall_accuracy": round(correct / total * 100, 1) if total else 0.0,
        "answered_today":   today_row.total if today_row else 0,
        "by_topic": [
            {"topic": r.topic, "total": r.total, "correct": int(r.correct or 0),
             "accuracy": round(int(r.correct or 0) / r.total * 100, 1) if r.total else 0.0}
            for r in by_topic
        ],
        "by_step": [
            {"step": r.step, "total": r.total, "correct": int(r.correct or 0),
             "accuracy": round(int(r.correct or 0) / r.total * 100, 1) if r.total else 0.0}
            for r in by_step
        ],
    }


def get_weakness_report(user_id: str, threshold: float = 60.0) -> dict:
    progress = get_progress(user_id)
    weak   = sorted([t for t in progress["by_topic"] if t["total"] >= 5 and t["accuracy"] < threshold],
                    key=lambda x: x["accuracy"])
    strong = [t for t in progress["by_topic"] if t["total"] >= 5 and t["accuracy"] >= threshold]
    return {
        "weak_topics": weak, "strong_topics": strong,
        "overall_accuracy": progress["overall_accuracy"],
        "total_answered":   progress["total_answered"],
        "answered_today":   progress["answered_today"],
        "threshold": threshold,
    }


# ── Funciones: plan de estudio ────────────────────────────────────────────────

def _weeks_until(target_date_str: str) -> float:
    try:
        return max((date.fromisoformat(target_date_str) - date.today()).days / 7, 0)
    except Exception:
        return 20.0


def set_study_plan(user_id: str, target_date: str, plan_type: str = "12_week",
                   daily_questions: int = 60, language: str = "bilingual",
                   current_week: int = 1) -> dict:
    now = datetime.now().isoformat()
    week_detail = get_week_detail(plan_type, current_week)

    with engine.begin() as conn:
        existing = conn.execute(
            study_plans_tbl.select().where(study_plans_tbl.c.user_id == user_id)
        ).fetchone()

        values = dict(
            target_date=target_date, plan_type=plan_type, daily_questions=daily_questions,
            language=language, current_week=current_week,
            current_system=week_detail.get("system", "mixed"),
            current_phase=week_detail.get("phase", "diagnostic"),
            updated_at=now,
        )
        if existing:
            conn.execute(study_plans_tbl.update().where(study_plans_tbl.c.user_id == user_id).values(**values))
        else:
            conn.execute(study_plans_tbl.insert().values(user_id=user_id, created_at=now, **values))

    return get_study_plan(user_id)


def get_study_plan(user_id: str) -> dict:
    with engine.connect() as conn:
        row = conn.execute(study_plans_tbl.select().where(study_plans_tbl.c.user_id == user_id)).fetchone()

    if not row:
        return {"has_plan": False}

    weeks_left = _weeks_until(row.target_date) if row.target_date else None
    week_detail = get_week_detail(row.plan_type, row.current_week)
    total_weeks = len(PLAN_TEMPLATES.get(row.plan_type, TWELVE_WEEK_PLAN))

    return {
        "has_plan":          True,
        "target_date":       row.target_date,
        "plan_type":         row.plan_type,
        "daily_questions":   row.daily_questions,
        "language":          row.language,
        "current_week":      row.current_week,
        "total_weeks":       total_weeks,
        "current_system":    row.current_system,
        "current_phase":     row.current_phase,
        "weeks_left":        round(weeks_left, 1) if weeks_left else None,
        "days_left":         int(weeks_left * 7) if weeks_left else None,
        "current_week_detail": week_detail,
    }


def update_study_phase(user_id: str, current_week: int = None,
                       current_system: str = None, current_phase: str = None) -> dict:
    updates = {"updated_at": datetime.now().isoformat()}
    if current_week is not None:
        updates["current_week"] = current_week
        # Auto-update system and phase from template
        plan_row = None
        with engine.connect() as conn:
            plan_row = conn.execute(study_plans_tbl.select().where(study_plans_tbl.c.user_id == user_id)).fetchone()
        if plan_row:
            w = get_week_detail(plan_row.plan_type, current_week)
            updates["current_system"] = w.get("system", "mixed")
            updates["current_phase"]  = w.get("phase", "systems")
    if current_system: updates["current_system"] = current_system
    if current_phase:  updates["current_phase"]  = current_phase

    with engine.begin() as conn:
        conn.execute(study_plans_tbl.update().where(study_plans_tbl.c.user_id == user_id).values(**updates))

    return get_study_plan(user_id)
