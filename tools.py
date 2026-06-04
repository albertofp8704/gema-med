"""
GEMA-MED — Question bank tools

Fuentes combinadas:
  1. GBaker/MedQA-USMLE-4-options  →  10,178 preguntas USMLE reales (parquet, gratis)
  2. openlifescienceai/medmcqa      → 183,000 preguntas médicas reales (exámenes India)
  3. PubMed E-utilities API         → referencias clínicas peer-reviewed (gratis, sin key)

Total combinado: ~193,000 preguntas
"""

import random
import hashlib
import httpx

_dataset: list | None = None

# ── Topic keywords para búsqueda y filtrado ───────────────────────────────────

TOPIC_KEYWORDS: dict[str, list[str]] = {
    "cardiology":       ["heart", "cardiac", "coronary", "atrial", "ventricular", "myocardial",
                          "aortic", "mitral", "pericarditis", "arrhythmia", "hypertension"],
    "pulmonology":      ["lung", "pulmonary", "respiratory", "bronchial", "asthma", "copd",
                          "pneumonia", "pleural", "tuberculosis", "dyspnea"],
    "nephrology":       ["kidney", "renal", "nephro", "glomerular", "urinary", "creatinine",
                          "dialysis", "proteinuria", "hematuria", "acid-base"],
    "neurology":        ["brain", "neurological", "cortex", "seizure", "stroke", "headache",
                          "dementia", "parkinson", "nerve", "spinal", "meningitis", "cranial"],
    "gastroenterology": ["liver", "gastric", "intestinal", "bowel", "colon", "pancreas",
                          "hepatic", "cirrhosis", "peptic", "diarrhea", "esophag"],
    "endocrinology":    ["diabetes", "thyroid", "adrenal", "insulin", "glucose", "cortisol",
                          "pituitary", "hormone", "hypoglycemia", "cushing", "addison"],
    "hematology":       ["anemia", "coagulation", "platelet", "hemoglobin", "leukemia",
                          "lymphoma", "bleeding", "thrombosis", "sickle", "thalassemia"],
    "pharmacology":     ["drug", "medication", "inhibitor", "agonist", "receptor", "dose",
                          "toxicity", "antidote", "side effect", "mechanism of action",
                          "antibiotic", "analgesic", "antihypertensive", "statin"],
    "microbiology":     ["bacteria", "virus", "fungal", "parasite", "antibiotic", "sepsis",
                          "infection", "gram", "culture", "pathogen", "protozoa", "helminth"],
    "pathology":        ["tumor", "cancer", "neoplasm", "malignant", "biopsy", "histology",
                          "metastasis", "carcinoma", "sarcoma", "inflammation", "necrosis"],
    "ob_gyn":           ["pregnant", "fetal", "uterine", "ovarian", "menstrual", "contraception",
                          "gestational", "obstetric", "gynecological", "preeclampsia"],
    "pediatrics":       ["child", "infant", "neonatal", "developmental", "vaccination", "growth",
                          "congenital", "pediatric", "adolescent", "newborn"],
    "psychiatry":       ["depression", "anxiety", "schizophrenia", "bipolar", "psychosis",
                          "suicide", "cognitive", "psychiatric", "mental", "dsm"],
    "biostatistics":    ["sensitivity", "specificity", "p-value", "confidence interval",
                          "relative risk", "odds ratio", "prevalence", "incidence", "bias",
                          "randomized", "cohort", "cross-sectional", "number needed"],
    "anatomy":          ["anatomy", "histology", "embryology", "nerve supply", "blood supply",
                          "lymphatic", "ligament", "tendon", "foramen", "artery"],
    "physiology":       ["physiology", "homeostasis", "membrane potential", "action potential",
                          "osmolarity", "filtration", "secretion", "absorption", "regulation"],
    "biochemistry":     ["biochemistry", "enzyme", "metabolism", "protein", "dna", "rna",
                          "gene", "metabolic", "amino acid", "fatty acid", "glycolysis", "krebs"],
}

# ── MedMCQA subject → nuestro topic ──────────────────────────────────────────

MEDMCQA_SUBJECT_MAP: dict[str, str] = {
    "Pharmacology":                  "pharmacology",
    "Medicine":                      "general",        # se refina por keywords
    "Pathology":                     "pathology",
    "Microbiology":                  "microbiology",
    "Anatomy":                       "anatomy",
    "Physiology":                    "physiology",
    "Biochemistry":                  "biochemistry",
    "Surgery":                       "gastroenterology",
    "Obstetrics & Gynaecology":      "ob_gyn",
    "Paediatrics":                   "pediatrics",
    "Psychiatry":                    "psychiatry",
    "Ophthalmology":                 "neurology",
    "ENT":                           "neurology",
    "Orthopaedics":                  "anatomy",
    "Radiology":                     "pathology",
    "Dermatology":                   "pathology",
    "Anaesthesia":                   "pharmacology",
    "Forensic Medicine":             "biostatistics",
    "Social & Preventive Medicine":  "biostatistics",
    "Dental":                        "pathology",
}


def _question_id(text: str) -> str:
    return hashlib.md5(text[:100].encode()).hexdigest()[:12]


def _detect_topic_by_keywords(question: str) -> str:
    q = question.lower()
    for topic, kws in TOPIC_KEYWORDS.items():
        if any(kw in q for kw in kws):
            return topic
    return "general"


# ── Loaders ───────────────────────────────────────────────────────────────────

def _load_gbaker() -> list[dict]:
    """GBaker/MedQA-USMLE-4-options — 10,178 preguntas USMLE. Parquet, sin scripts."""
    print("  → GBaker/MedQA-USMLE-4-options ...")
    from datasets import load_dataset
    raw = load_dataset("GBaker/MedQA-USMLE-4-options")

    result = []
    for split in raw.values():
        for q in split:
            opts: dict = q.get("options", {})
            letter = (q.get("answer") or q.get("answer_idx") or "A").strip().upper()
            if letter and letter[0] in "ABCDE":
                letter = letter[0]
            result.append({
                "_source":      "medqa",
                "question":     q["question"],
                "options":      opts,
                "correct_letter": letter,
                "correct_answer": opts.get(letter, ""),
                "explanation":  "",
                "topic":        _detect_topic_by_keywords(q["question"]),
                "step":         1,
            })
    print(f"     {len(result):,} preguntas")
    return result


def _load_medmcqa(max_questions: int = 100_000) -> list[dict]:
    """
    openlifescienceai/medmcqa — 183k preguntas de exámenes médicos reales.
    Limitamos a max_questions para controlar uso de RAM en Railway.
    """
    print("  → openlifescienceai/medmcqa ...")
    from datasets import load_dataset
    raw = load_dataset("openlifescienceai/medmcqa", split="train")

    result = []
    letters = ["A", "B", "C", "D"]

    for q in raw:
        # Filtrar preguntas inválidas
        if q.get("choice_type") != "single":
            continue
        question = (q.get("question") or "").strip()
        if len(question) < 20:
            continue
        opts = {
            "A": (q.get("opa") or "").strip(),
            "B": (q.get("opb") or "").strip(),
            "C": (q.get("opc") or "").strip(),
            "D": (q.get("opd") or "").strip(),
        }
        if any(len(v) < 2 for v in opts.values()):
            continue
        cop = q.get("cop")
        if cop not in [0, 1, 2, 3]:
            continue

        correct_letter = letters[cop]
        subject = q.get("subject_name", "")
        topic = MEDMCQA_SUBJECT_MAP.get(subject, "general")
        if topic == "general":
            topic = _detect_topic_by_keywords(question)

        result.append({
            "_source":        "medmcqa",
            "question":       question,
            "options":        opts,
            "correct_letter": correct_letter,
            "correct_answer": opts[correct_letter],
            "explanation":    (q.get("exp") or "").strip(),
            "topic":          topic,
            "step":           1,
        })

        if len(result) >= max_questions:
            break

    print(f"     {len(result):,} preguntas")
    return result


def _load_dataset() -> list[dict]:
    global _dataset
    if _dataset is None:
        print("GEMA-MED: cargando banco de preguntas combinado...")
        gbaker   = _load_gbaker()
        medmcqa  = _load_medmcqa(max_questions=100_000)
        combined = gbaker + medmcqa
        random.shuffle(combined)          # mezclar fuentes
        _dataset = combined
        print(f"✅ Banco cargado: {len(_dataset):,} preguntas totales "
              f"(MedQA: {len(gbaker):,} · MedMCQA: {len(medmcqa):,})")
    return _dataset


# ── get_usmle_question ────────────────────────────────────────────────────────

def get_usmle_question(topic: str | None = None, step: str | None = None) -> dict:
    """
    Devuelve una pregunta aleatoria del banco combinado (110k preguntas).
    Filtra por tema (topic) y step si se especifican.
    """
    dataset = _load_dataset()
    candidates = dataset

    # Filtrar por topic
    if topic and topic.lower() in TOPIC_KEYWORDS:
        t = topic.lower()
        # Primero por campo topic exacto
        by_field = [q for q in candidates if q["topic"] == t]
        # Fallback: búsqueda por keywords en el texto
        if not by_field:
            kws = TOPIC_KEYWORDS[t]
            by_field = [q for q in candidates if any(kw in q["question"].lower() for kw in kws)]
        if by_field:
            candidates = by_field

    if not candidates:
        candidates = dataset

    q = random.choice(candidates)

    return {
        "id":             _question_id(q["question"]),
        "question":       q["question"],
        "options":        q["options"],
        "correct_letter": q["correct_letter"],
        "correct_answer": q["correct_answer"],
        "explanation":    q.get("explanation", ""),
        "step":           q.get("step", 1),
        "topic":          q.get("topic", "general"),
        "source":         q.get("_source", "unknown"),
    }


# ── PubMed search ─────────────────────────────────────────────────────────────

async def search_pubmed(query: str, max_results: int = 3) -> list[dict]:
    """Busca en PubMed con la API gratuita de NCBI E-utilities."""
    base = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            search = await client.get(f"{base}/esearch.fcgi", params={
                "db": "pubmed", "term": query,
                "retmax": max_results, "retmode": "json", "sort": "relevance",
            })
            ids: list = search.json().get("esearchresult", {}).get("idlist", [])
            if not ids:
                return []

            summary = await client.get(f"{base}/esummary.fcgi", params={
                "db": "pubmed", "id": ",".join(ids), "retmode": "json",
            })
            result = summary.json().get("result", {})

        return [
            {
                "pmid":    pmid,
                "title":   result[pmid].get("title", ""),
                "journal": result[pmid].get("fulljournalname", ""),
                "year":    (result[pmid].get("pubdate") or "")[:4],
                "url":     f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
            }
            for pmid in ids if pmid in result
        ]
    except Exception as e:
        return [{"error": str(e)}]
