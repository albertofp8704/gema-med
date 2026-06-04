"""
Tools for GEMA-MED agent.

Data sources:
  - MedQA (bigbio/med_qa): 12,723 real USMLE questions — https://huggingface.co/datasets/bigbio/med_qa
  - PubMed E-utilities API (free, no key required) — https://www.ncbi.nlm.nih.gov/home/develop/api/
"""

import random
import hashlib
import httpx

_dataset: list | None = None

TOPIC_KEYWORDS: dict[str, list[str]] = {
    "cardiology":        ["heart", "cardiac", "coronary", "atrial", "ventricular", "myocardial", "aortic", "mitral"],
    "pulmonology":       ["lung", "pulmonary", "respiratory", "bronchial", "asthma", "copd", "pneumonia", "pleural"],
    "nephrology":        ["kidney", "renal", "nephro", "glomerular", "urinary", "creatinine", "dialysis"],
    "neurology":         ["brain", "neurological", "cortex", "seizure", "stroke", "headache", "dementia", "parkinson"],
    "gastroenterology":  ["liver", "gastric", "intestinal", "bowel", "colon", "pancreas", "hepatic", "cirrhosis"],
    "endocrinology":     ["diabetes", "thyroid", "adrenal", "insulin", "glucose", "cortisol", "pituitary"],
    "hematology":        ["anemia", "coagulation", "platelet", "hemoglobin", "leukemia", "lymphoma", "bleeding"],
    "pharmacology":      ["drug", "medication", "inhibitor", "agonist", "receptor", "dosing", "toxicity", "antidote"],
    "microbiology":      ["bacteria", "virus", "fungal", "parasite", "antibiotic", "sepsis", "meningitis"],
    "pathology":         ["tumor", "cancer", "neoplasm", "malignant", "biopsy", "histology", "metastasis"],
    "ob_gyn":            ["pregnant", "fetal", "uterine", "ovarian", "menstrual", "contraception", "gestational"],
    "pediatrics":        ["child", "infant", "neonatal", "developmental", "vaccination", "growth", "congenital"],
    "psychiatry":        ["depression", "anxiety", "schizophrenia", "bipolar", "psychosis", "suicide", "cognitive"],
    "biostatistics":     ["sensitivity", "specificity", "p-value", "confidence interval", "relative risk", "odds ratio"],
}


def _load_dataset() -> list:
    global _dataset
    if _dataset is None:
        print("Loading MedQA dataset from HuggingFace (one-time download ~100 MB)...")
        from datasets import load_dataset  # lazy import — slow startup if imported at top
        raw = load_dataset("bigbio/med_qa", "med_qa_en_source", trust_remote_code=True)
        all_splits = []
        for split in raw.values():
            all_splits.extend(list(split))
        _dataset = all_splits
        print(f"MedQA loaded: {len(_dataset):,} questions")
    return _dataset


def _question_id(question_text: str) -> str:
    return hashlib.md5(question_text[:100].encode()).hexdigest()[:12]


def _detect_step(meta_info: str) -> int:
    m = meta_info.lower()
    if "step1" in m or "step 1" in m:
        return 1
    if "step2" in m or "step 2" in m:
        return 2
    if "step3" in m or "step 3" in m:
        return 3
    return 1  # default


def get_usmle_question(topic: str | None = None, step: str | None = None) -> dict:
    """
    Returns a real USMLE question from MedQA.
    Fields: id, question, options (dict A-E), correct_answer, correct_letter, step (int), topic
    """
    dataset = _load_dataset()
    candidates = dataset

    # Filter by step
    if step:
        step_num = int(step.replace("step", "").strip()) if step.replace("step", "").strip().isdigit() else None
        if step_num:
            candidates = [q for q in candidates if _detect_step(q.get("meta_info", "")) == step_num]

    # Filter by topic keywords
    if topic and topic.lower() in TOPIC_KEYWORDS:
        keywords = TOPIC_KEYWORDS[topic.lower()]
        topic_filtered = [q for q in candidates if any(kw in q["question"].lower() for kw in keywords)]
        if topic_filtered:
            candidates = topic_filtered

    if not candidates:
        candidates = dataset

    q = random.choice(candidates)

    options: dict = q.get("options", {})
    answer_text: str = q.get("answer", "")

    # Resolve correct letter from answer text
    correct_letter = "?"
    for letter, text in options.items():
        if answer_text.strip().lower() == text.strip().lower():
            correct_letter = letter
            break
    # Fallback: answer field sometimes includes letter prefix like "B) ..."
    if correct_letter == "?" and answer_text and answer_text[0].upper() in "ABCDE":
        correct_letter = answer_text[0].upper()

    detected_step = _detect_step(q.get("meta_info", ""))
    detected_topic = topic or "general"
    if not topic:
        q_lower = q["question"].lower()
        for t, kws in TOPIC_KEYWORDS.items():
            if any(kw in q_lower for kw in kws):
                detected_topic = t
                break

    return {
        "id": _question_id(q["question"]),
        "question": q["question"],
        "options": options,
        "correct_answer": answer_text,
        "correct_letter": correct_letter,
        "step": detected_step,
        "topic": detected_topic,
        "meta_info": q.get("meta_info", ""),
    }


async def search_pubmed(query: str, max_results: int = 3) -> list[dict]:
    """
    Search PubMed using the free E-utilities API and return article summaries.
    """
    base = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            search = await client.get(f"{base}/esearch.fcgi", params={
                "db": "pubmed",
                "term": query,
                "retmax": max_results,
                "retmode": "json",
                "sort": "relevance",
            })
            ids: list = search.json().get("esearchresult", {}).get("idlist", [])

            if not ids:
                return []

            summary = await client.get(f"{base}/esummary.fcgi", params={
                "db": "pubmed",
                "id": ",".join(ids),
                "retmode": "json",
            })
            result = summary.json().get("result", {})

        articles = []
        for pmid in ids:
            art = result.get(pmid, {})
            if art:
                articles.append({
                    "pmid": pmid,
                    "title": art.get("title", ""),
                    "journal": art.get("fulljournalname", ""),
                    "year": (art.get("pubdate", "") or "")[:4],
                    "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                })
        return articles

    except Exception as e:
        return [{"error": str(e)}]
