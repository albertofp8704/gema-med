"""
Database layer — SQLite (dev) / PostgreSQL (prod via DATABASE_URL).
Uses SQLAlchemy Core so the same SQL works in both engines.
"""

import os
import sqlalchemy as sa
from datetime import datetime, date

_raw = os.getenv("DATABASE_URL", "sqlite:///./gema_med.db")
DATABASE_URL = _raw.replace("postgres://", "postgresql://", 1) if _raw.startswith("postgres://") else _raw

engine   = sa.create_engine(DATABASE_URL, pool_pre_ping=True)
metadata = sa.MetaData()

# ── Tables ────────────────────────────────────────────────────────────────────

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

study_plans_tbl = sa.Table(
    "study_plans", metadata,
    sa.Column("user_id",        sa.String, primary_key=True),
    sa.Column("target_date",    sa.String, nullable=True),   # ISO date YYYY-MM-DD
    sa.Column("daily_goal",     sa.Integer, default=40),
    sa.Column("current_system", sa.String, default="cardiology"),
    sa.Column("current_phase",  sa.String, default="planning"),
    sa.Column("created_at",     sa.String, nullable=False),
    sa.Column("updated_at",     sa.String, nullable=False),
)


def init_db() -> None:
    metadata.create_all(engine)


# ── Results ───────────────────────────────────────────────────────────────────

def save_result(user_id: str, question_id: str, topic: str, step: int, correct: bool) -> None:
    with engine.begin() as conn:
        conn.execute(results_tbl.insert().values(
            user_id=user_id,
            question_id=question_id,
            topic=topic or "general",
            step=step or 1,
            correct=int(correct),
            timestamp=datetime.now().isoformat(),
        ))


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

        # Questions answered today
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
            {
                "topic":    r.topic,
                "total":    r.total,
                "correct":  int(r.correct or 0),
                "accuracy": round(int(r.correct or 0) / r.total * 100, 1) if r.total else 0.0,
            }
            for r in by_topic
        ],
        "by_step": [
            {
                "step":     r.step,
                "total":    r.total,
                "correct":  int(r.correct or 0),
                "accuracy": round(int(r.correct or 0) / r.total * 100, 1) if r.total else 0.0,
            }
            for r in by_step
        ],
    }


def get_weakness_report(user_id: str, threshold: float = 60.0) -> dict:
    """Returns systems with accuracy below threshold and today's progress."""
    progress = get_progress(user_id)
    weak = [t for t in progress["by_topic"] if t["total"] >= 5 and t["accuracy"] < threshold]
    strong = [t for t in progress["by_topic"] if t["total"] >= 5 and t["accuracy"] >= threshold]
    weak.sort(key=lambda x: x["accuracy"])

    return {
        "weak_topics":    weak,
        "strong_topics":  strong,
        "overall_accuracy": progress["overall_accuracy"],
        "total_answered": progress["total_answered"],
        "answered_today": progress["answered_today"],
        "threshold":      threshold,
    }


# ── Study Plan ────────────────────────────────────────────────────────────────

SYSTEM_ORDER = [
    "cardiology", "pulmonology", "nephrology", "gastroenterology",
    "hematology", "neurology", "psychiatry", "endocrinology",
    "ob_gyn", "pharmacology", "microbiology", "pathology", "biostatistics",
]

SYSTEM_WEEKS = {
    "cardiology": 2.0, "pulmonology": 1.5, "nephrology": 1.5,
    "gastroenterology": 2.0, "hematology": 1.5, "neurology": 2.0,
    "psychiatry": 1.0, "endocrinology": 1.5, "ob_gyn": 1.5,
    "pharmacology": 1.5, "microbiology": 2.0, "pathology": 1.0,
    "biostatistics": 0.5,
}


def _weeks_until(target_date_str: str) -> float:
    try:
        target = date.fromisoformat(target_date_str)
        delta = (target - date.today()).days
        return max(delta / 7, 0)
    except Exception:
        return 20.0


def set_study_plan(user_id: str, target_date: str, daily_goal: int = 40,
                   current_system: str = "cardiology", current_phase: str = "diagnostic") -> dict:
    now = datetime.now().isoformat()
    with engine.begin() as conn:
        existing = conn.execute(
            sa.select(study_plans_tbl).where(study_plans_tbl.c.user_id == user_id)
        ).fetchone()

        if existing:
            conn.execute(
                study_plans_tbl.update()
                .where(study_plans_tbl.c.user_id == user_id)
                .values(target_date=target_date, daily_goal=daily_goal,
                        current_system=current_system, current_phase=current_phase,
                        updated_at=now)
            )
        else:
            conn.execute(study_plans_tbl.insert().values(
                user_id=user_id, target_date=target_date, daily_goal=daily_goal,
                current_system=current_system, current_phase=current_phase,
                created_at=now, updated_at=now,
            ))

    return get_study_plan(user_id)


def get_study_plan(user_id: str) -> dict:
    with engine.connect() as conn:
        row = conn.execute(
            sa.select(study_plans_tbl).where(study_plans_tbl.c.user_id == user_id)
        ).fetchone()

    if not row:
        return {"has_plan": False}

    weeks_left = _weeks_until(row.target_date) if row.target_date else None

    # Build week-by-week schedule
    schedule = []
    if weeks_left:
        week = 1
        for sys in SYSTEM_ORDER:
            w = SYSTEM_WEEKS.get(sys, 1.0)
            schedule.append({
                "week": f"{week}–{week + w - 0.5:.0f}".replace(".5", "½"),
                "system": sys,
                "weeks": w,
            })
            week += w

    return {
        "has_plan":       True,
        "target_date":    row.target_date,
        "daily_goal":     row.daily_goal,
        "current_system": row.current_system,
        "current_phase":  row.current_phase,
        "weeks_left":     round(weeks_left, 1) if weeks_left else None,
        "days_left":      int(weeks_left * 7) if weeks_left else None,
        "schedule":       schedule,
        "system_order":   SYSTEM_ORDER,
    }


def update_study_phase(user_id: str, current_system: str = None,
                       current_phase: str = None) -> dict:
    updates = {"updated_at": datetime.now().isoformat()}
    if current_system: updates["current_system"] = current_system
    if current_phase:  updates["current_phase"]  = current_phase

    with engine.begin() as conn:
        conn.execute(
            study_plans_tbl.update()
            .where(study_plans_tbl.c.user_id == user_id)
            .values(**updates)
        )
    return get_study_plan(user_id)
