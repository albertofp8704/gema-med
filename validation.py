"""
GEMA-MED — Medical Content Validation Pipeline
================================================
Fail-fast, multi-layer validation before any content reaches users.

Layers:
  1. Schema     — required fields, types, length
  2. Semantic   — medical coherence, no empty answers, no hallucination markers
  3. Source     — source present and non-generic
  4. Risk       — clinical risk score (treatment/dosage/diagnosis triggers)
  5. Human gate — final approval required for high-risk content

States: draft → auto_checked → needs_review → approved / rejected → archived
Only "approved" content can be served.
"""

import re
import hashlib
import datetime
from enum import Enum
from typing import Optional


# ── Content States ────────────────────────────────────────────────────────────

class ContentStatus(str, Enum):
    DRAFT        = "draft"
    AUTO_CHECKED = "auto_checked"   # passed all auto checks, low risk
    NEEDS_REVIEW = "needs_review"   # failed a check or high risk — human required
    APPROVED     = "approved"       # human approved — safe to publish
    REJECTED     = "rejected"       # human rejected — archived, never served
    ARCHIVED     = "archived"       # soft delete


class ContentType(str, Enum):
    QUESTION    = "question"
    EXPLANATION = "explanation"
    REFERENCE   = "reference"
    GENERAL     = "general"


class RiskLevel(str, Enum):
    LOW    = "low"
    MEDIUM = "medium"
    HIGH   = "high"


# ── Risk keywords — any of these trigger mandatory human review ───────────────

RISK_HIGH_TERMS = [
    # Treatment / Dosage
    "mg/kg", "mg/day", "dose of", "dosage", "loading dose", "maintenance dose",
    "administer", "infuse", "inject", "titrate",
    # Diagnosis assertion (not question form)
    "the diagnosis is", "patient has", "confirms diagnosis", "definitively",
    "this confirms", "diagnostic of",
    # Urgency / Emergency
    "immediately", "emergent", "life-threatening", "do not delay",
    "call 911", "activate code",
    # Drug interactions / contraindications
    "do not use", "contraindicated in", "fatal if", "lethal dose",
    "overdose treatment", "antidote is",
]

RISK_MEDIUM_TERMS = [
    "treatment is", "therapy includes", "management involves",
    "prescribe", "recommend", "guideline", "first-line",
    "clinical decision", "surgery", "procedure",
]

# Hallucination markers — LLM artifacts that should never reach users
HALLUCINATION_MARKERS = [
    "i'm sorry", "lo siento", "as an ai", "como ia", "i cannot",
    "the previous question", "la pregunta anterior",
    "i apologize", "me disculpo", "unfortunately i",
    "i don't have access", "no tengo acceso",
    "as a language model", "como modelo de lenguaje",
]

# Generic / invalid sources
GENERIC_SOURCES = [
    "google", "wikipedia", "unknown", "n/a", "none", "", "various",
    "internet", "web", "online", "general knowledge",
]


# ── Validation Result ─────────────────────────────────────────────────────────

class ValidationResult:
    def __init__(self):
        self.passed   = True
        self.errors   : list[str] = []
        self.warnings : list[str] = []
        self.risk_level : RiskLevel = RiskLevel.LOW
        self.risk_reasons : list[str] = []
        self.final_status : ContentStatus = ContentStatus.AUTO_CHECKED

    def fail(self, msg: str):
        self.passed = False
        self.errors.append(msg)
        self.final_status = ContentStatus.NEEDS_REVIEW

    def warn(self, msg: str):
        self.warnings.append(msg)

    def flag_review(self, reason: str):
        self.risk_reasons.append(reason)
        self.final_status = ContentStatus.NEEDS_REVIEW

    def to_dict(self) -> dict:
        return {
            "passed":      self.passed,
            "status":      self.final_status.value,
            "risk_level":  self.risk_level.value,
            "errors":      self.errors,
            "warnings":    self.warnings,
            "risk_reasons": self.risk_reasons,
        }


# ── Layer 1: Schema Validation ────────────────────────────────────────────────

def validate_schema(item: dict, content_type: ContentType) -> ValidationResult:
    """Check required fields, types, lengths."""
    result = ValidationResult()

    # Universal required fields
    for field in ["id", "topic", "content"]:
        if not item.get(field):
            result.fail(f"Missing required field: '{field}'")

    # Type-specific required fields
    if content_type == ContentType.QUESTION:
        if not item.get("correct_answer"):
            result.fail("Question must have 'correct_answer'")
        if not item.get("choices") or len(item.get("choices", [])) < 2:
            result.fail("Question must have at least 2 choices")
        if not item.get("explanation") or len(item.get("explanation", "")) < 30:
            result.fail("Question must have explanation (min 30 chars)")

    if content_type == ContentType.EXPLANATION:
        content = item.get("content", "")
        if len(content) < 50:
            result.fail("Explanation too short (min 50 chars)")
        if len(content) > 10_000:
            result.warn("Explanation very long — consider splitting")

    # Topic validation
    from tools import TOPIC_KEYWORDS
    topic = (item.get("topic") or "").lower().replace(" ", "_")
    if topic and topic not in TOPIC_KEYWORDS and topic != "general":
        result.warn(f"Unknown topic '{topic}' — not in standard list")

    return result


# ── Layer 2: Semantic / Medical Coherence ────────────────────────────────────

def validate_semantic(item: dict, content_type: ContentType) -> ValidationResult:
    """Check medical coherence, detect hallucinations, validate answer format."""
    result = ValidationResult()
    content = (item.get("content") or item.get("stem") or "").lower()
    explanation = (item.get("explanation") or "").lower()
    combined = content + " " + explanation

    # Check for LLM hallucination markers
    for marker in HALLUCINATION_MARKERS:
        if marker in combined:
            result.fail(f"Hallucination marker detected: '{marker}'")

    # Choices validation for questions
    if content_type == ContentType.QUESTION:
        choices = item.get("choices", {})
        if isinstance(choices, dict):
            for letter, text in choices.items():
                if not text or len(str(text).strip()) < 2:
                    result.fail(f"Choice '{letter}' is empty or too short")
        correct = item.get("correct_answer", "")
        if isinstance(choices, dict) and correct not in choices:
            result.fail(f"correct_answer '{correct}' not in choices {list(choices.keys())}")

    # No diagnostic assertions without hedging
    assertion_patterns = [
        r"\bthe diagnosis is\b",
        r"\bpatient definitely has\b",
        r"\bthis confirms\b.*\bdiagnosis\b",
    ]
    for pat in assertion_patterns:
        if re.search(pat, combined):
            result.flag_review(f"Assertive diagnostic language: '{pat}'")

    # Content must not be a copy-paste of question stem as explanation
    stem = (item.get("stem") or item.get("content") or "").lower()
    exp  = (item.get("explanation") or "").lower()
    if stem and exp and len(stem) > 20:
        overlap = len(set(stem.split()) & set(exp.split())) / max(len(set(stem.split())), 1)
        if overlap > 0.85:
            result.warn("Explanation overlaps heavily with question — may be a copy")

    return result


# ── Layer 3: Source Validation ────────────────────────────────────────────────

def validate_source(item: dict) -> ValidationResult:
    """Check source presence and quality."""
    result = ValidationResult()
    source     = (item.get("source_url") or item.get("source") or "").strip().lower()
    source_type = (item.get("source_type") or "").strip().lower()

    if not source:
        result.flag_review("No source provided — requires human verification")
        return result

    # Reject generic/empty sources
    if any(g in source for g in GENERIC_SOURCES):
        result.flag_review(f"Generic or invalid source: '{source}'")

    # Prefer official sources
    OFFICIAL_DOMAINS = ["pubmed", "ncbi.nlm", "nejm.org", "acc.org", "aha.org",
                        "uptodate", "medscape", "cdc.gov", "who.int", "nbme.org",
                        "amboss", "firstaid", "pathoma"]
    is_official = any(d in source for d in OFFICIAL_DOMAINS)
    if not is_official:
        result.warn(f"Source '{source}' not from official medical database — verify manually")

    return result


# ── Layer 4: Clinical Risk Scoring ───────────────────────────────────────────

def score_risk(item: dict) -> tuple[RiskLevel, list[str]]:
    """
    Calculate clinical risk level.
    HIGH  → mandatory human review, no auto-publish
    MEDIUM → flagged for review
    LOW   → can auto-publish if all other checks pass
    """
    content = " ".join([
        str(item.get("content", "")),
        str(item.get("stem", "")),
        str(item.get("explanation", "")),
    ]).lower()

    reasons: list[str] = []

    high_hits = [t for t in RISK_HIGH_TERMS if t in content]
    med_hits  = [t for t in RISK_MEDIUM_TERMS if t in content]

    if high_hits:
        return RiskLevel.HIGH, [f"High-risk term: '{h}'" for h in high_hits[:3]]
    if med_hits:
        return RiskLevel.MEDIUM, [f"Medium-risk term: '{m}'" for m in med_hits[:2]]

    return RiskLevel.LOW, []


# ── Master Pipeline ───────────────────────────────────────────────────────────

def run_validation_pipeline(
    item: dict,
    content_type: ContentType = ContentType.EXPLANATION,
    submitted_by: str = "system",
) -> dict:
    """
    Run all 4 automatic validation layers.
    Returns final status and full audit report.
    Human approval (layer 5) is done separately via the review endpoint.

    Returns:
        {
          "id": str,
          "final_status": str,    # auto_checked | needs_review
          "layers": {...},        # per-layer results
          "risk_level": str,
          "risk_reasons": [...],
          "errors": [...],
          "warnings": [...],
          "submitted_by": str,
          "validated_at": str,
        }
    """
    # Layer 1: Schema
    l1 = validate_schema(item, content_type)

    # Layer 2: Semantic (only if schema passed)
    l2 = validate_semantic(item, content_type) if l1.passed else ValidationResult()

    # Layer 3: Source
    l3 = validate_source(item)

    # Layer 4: Risk score
    risk_level, risk_reasons = score_risk(item)

    # Aggregate
    all_errors   = l1.errors + l2.errors + l3.errors
    all_warnings = l1.warnings + l2.warnings + l3.warnings
    review_flags = l2.risk_reasons + l3.risk_reasons + risk_reasons

    # Determine final status
    if not l1.passed or not l2.passed:
        final_status = ContentStatus.NEEDS_REVIEW   # hard errors
    elif risk_level == RiskLevel.HIGH:
        final_status = ContentStatus.NEEDS_REVIEW   # high clinical risk
    elif review_flags:
        final_status = ContentStatus.NEEDS_REVIEW   # soft flags
    else:
        final_status = ContentStatus.AUTO_CHECKED

    return {
        "id":           item.get("id", _generate_id(item)),
        "final_status": final_status.value,
        "risk_level":   risk_level.value,
        "risk_reasons": risk_reasons,
        "errors":       all_errors,
        "warnings":     all_warnings,
        "review_flags": review_flags,
        "layers": {
            "schema":   l1.to_dict(),
            "semantic": l2.to_dict(),
            "source":   l3.to_dict(),
        },
        "submitted_by":  submitted_by,
        "validated_at":  datetime.datetime.utcnow().isoformat(),
        "can_publish":   final_status == ContentStatus.APPROVED,
    }


def can_publish(item_status: str) -> bool:
    """Gate: only approved items can be served to users."""
    return item_status == ContentStatus.APPROVED.value


def _generate_id(item: dict) -> str:
    content = str(item.get("content", "") or item.get("stem", ""))
    return "v_" + hashlib.md5(content[:100].encode()).hexdigest()[:12]
