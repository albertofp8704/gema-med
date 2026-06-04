"""
Database layer — SQLite for dev, PostgreSQL for prod.

Uses SQLAlchemy Core (no ORM) so the same SQL works in both engines.

Railway auto-injects DATABASE_URL as postgres://... → we normalize it.
"""

import os
import sqlalchemy as sa
from datetime import datetime

_raw = os.getenv("DATABASE_URL", "sqlite:///./gema_med.db")
# Railway uses legacy postgres:// scheme; SQLAlchemy 2.x needs postgresql://
DATABASE_URL = _raw.replace("postgres://", "postgresql://", 1) if _raw.startswith("postgres://") else _raw

engine   = sa.create_engine(DATABASE_URL, pool_pre_ping=True)
metadata = sa.MetaData()

results_tbl = sa.Table(
    "results",
    metadata,
    sa.Column("id",          sa.Integer, primary_key=True, autoincrement=True),
    sa.Column("user_id",     sa.String,  nullable=False, index=True),
    sa.Column("question_id", sa.String,  nullable=False),
    sa.Column("topic",       sa.String,  default="general"),
    sa.Column("step",        sa.Integer, default=1),
    sa.Column("correct",     sa.Integer, nullable=False),
    sa.Column("timestamp",   sa.String,  nullable=False),
)


def init_db() -> None:
    metadata.create_all(engine)


def save_result(
    user_id: str,
    question_id: str,
    topic: str,
    step: int,
    correct: bool,
) -> None:
    with engine.begin() as conn:
        conn.execute(
            results_tbl.insert().values(
                user_id=user_id,
                question_id=question_id,
                topic=topic or "general",
                step=step or 1,
                correct=int(correct),
                timestamp=datetime.now().isoformat(),
            )
        )


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
            )
            .where(results_tbl.c.user_id == user_id)
            .group_by(results_tbl.c.topic)
            .order_by(sa.func.count().desc())
        ).fetchall()

        by_step = conn.execute(
            sa.select(
                results_tbl.c.step,
                sa.func.count().label("total"),
                sa.func.coalesce(sa.func.sum(results_tbl.c.correct), 0).label("correct"),
            )
            .where(results_tbl.c.user_id == user_id)
            .group_by(results_tbl.c.step)
        ).fetchall()

    total   = agg.total   or 0
    correct = int(agg.correct or 0)

    return {
        "user_id":          user_id,
        "total_answered":   total,
        "total_correct":    correct,
        "overall_accuracy": round(correct / total * 100, 1) if total else 0.0,
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
