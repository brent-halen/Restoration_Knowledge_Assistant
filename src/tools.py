import json
from pathlib import Path

from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

from src.config import get_settings
from src.knowledge_base import build_vectorstore
from src.models import PricingEstimate, TechnicianRecord, UrgencyClassification


ROOT_DIR = Path(__file__).resolve().parent.parent
TECHNICIAN_FILE = ROOT_DIR / "data" / "technicians.json"

PRICE_BOOK = {
    "water_damage": {
        "minor": (800, 2500),
        "moderate": (2500, 7000),
        "severe": (7000, 18000),
    },
    "mold": {
        "minor": (1200, 3500),
        "moderate": (3500, 9000),
        "severe": (9000, 20000),
    },
    "fire_damage": {
        "minor": (1500, 5000),
        "moderate": (5000, 15000),
        "severe": (15000, 35000),
    },
    "general": {
        "minor": (500, 1500),
        "moderate": (1500, 4000),
        "severe": (4000, 10000),
    },
}


def _normalize_damage_type(damage_type: str) -> str:
    value = damage_type.strip().lower()
    aliases = {
        "water": "water_damage",
        "water damage": "water_damage",
        "fire": "fire_damage",
        "fire damage": "fire_damage",
        "smoke": "fire_damage",
    }
    return aliases.get(value, value if value in PRICE_BOOK else "general")


def _load_technicians() -> list[TechnicianRecord]:
    records = json.loads(TECHNICIAN_FILE.read_text(encoding="utf-8"))
    return [TechnicianRecord.model_validate(item) for item in records]


@tool
def search_knowledge_base(question: str) -> str:
    """Retrieve relevant passages from the local restoration knowledge base."""
    settings = get_settings()
    vectorstore = build_vectorstore()
    docs = vectorstore.similarity_search(question, k=settings.retrieval_k)
    if not docs:
        return "No relevant passages were found in the local knowledge base."

    passages = []
    for doc in docs[:3]:
        source = doc.metadata.get("source", "unknown")
        snippet = doc.page_content.strip().replace("\n", " ")
        passages.append(f"Source: {source}\nSnippet: {snippet[:500]}")
    return "\n\n".join(passages)


@tool
def classify_urgency(user_report: str) -> str:
    """Classify the urgency of a restoration incident with structured output."""
    settings = get_settings()
    model = ChatOpenAI(
        model=settings.llm_model,
        temperature=0,
        api_key=settings.openai_api_key,
    )
    structured_model = model.with_structured_output(UrgencyClassification)
    result = structured_model.invoke(
        (
            "Classify this restoration scenario conservatively. "
            "Return urgency based on safety, active damage, contamination risk, and time sensitivity. "
            "Use water_damage, fire_damage, mold, or general for damage_type."
            f"\n\nScenario:\n{user_report}"
        )
    )
    return result.model_dump_json(indent=2)


@tool
def estimate_pricing(damage_type: str, severity: str) -> str:
    """Return a deterministic demo-only price range for the requested damage type."""
    normalized_damage_type = _normalize_damage_type(damage_type)
    normalized_severity = severity.strip().lower()
    if normalized_severity not in {"minor", "moderate", "severe"}:
        normalized_severity = "moderate"

    low, high = PRICE_BOOK[normalized_damage_type][normalized_severity]
    estimate = PricingEstimate(
        service_type=normalized_damage_type,
        severity=normalized_severity,
        low_estimate_usd=low,
        high_estimate_usd=high,
        assumptions=[
            "Demo-only ballpark range.",
            "Does not replace site inspection or line-item estimating.",
            "Range assumes standard access and no major reconstruction.",
        ],
    )
    return estimate.model_dump_json(indent=2)


@tool
def lookup_available_technicians(damage_type: str = "general") -> str:
    """Return available mock technicians who best match the requested damage type."""
    normalized_damage_type = _normalize_damage_type(damage_type)
    matches = [
        technician
        for technician in _load_technicians()
        if technician.on_call
        and (
            normalized_damage_type in technician.specialties
            or "general" in technician.specialties
        )
    ]
    matches.sort(key=lambda record: record.eta_minutes)
    if not matches:
        return "No mock technicians are marked on-call for that specialty."

    payload = [
        {
            "name": record.name,
            "eta_minutes": record.eta_minutes,
            "certifications": record.certifications,
            "specialties": record.specialties,
        }
        for record in matches[:3]
    ]
    return json.dumps(payload, indent=2)


def get_tools():
    return [
        classify_urgency,
        search_knowledge_base,
        estimate_pricing,
        lookup_available_technicians,
    ]
