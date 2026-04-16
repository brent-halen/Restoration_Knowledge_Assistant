import json
import re
from pathlib import Path

from src.models import PricingEstimate, TechnicianRecord, UrgencyClassification


ROOT_DIR = Path(__file__).resolve().parent.parent
KNOWLEDGE_DIR = ROOT_DIR / "data" / "knowledge"
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

STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "has",
    "how",
    "i",
    "in",
    "is",
    "it",
    "my",
    "of",
    "on",
    "or",
    "that",
    "the",
    "there",
    "to",
    "we",
    "what",
    "with",
    "you",
}


def normalize_damage_type(value: str) -> str:
    normalized = value.strip().lower()
    aliases = {
        "water": "water_damage",
        "water damage": "water_damage",
        "fire": "fire_damage",
        "fire damage": "fire_damage",
        "smoke": "fire_damage",
    }
    return aliases.get(normalized, normalized if normalized in PRICE_BOOK else "general")


def classify_urgency_offline(user_report: str) -> UrgencyClassification:
    text = user_report.lower()

    if any(term in text for term in ["sewage", "black water", "rising water", "standing water", "burst pipe right now"]):
        return UrgencyClassification(
            damage_type="water_damage",
            urgency="P1_emergency",
            reasoning="Active water intrusion or contamination suggests immediate mitigation is needed.",
            immediate_actions=[
                "Keep people away from unsafe or contaminated areas.",
                "Stop the water source if it can be done safely.",
                "Document the damage and seek emergency mitigation.",
            ],
        )

    if any(term in text for term in ["burst pipe", "flood", "basement water", "ceiling leak", "water stain", "standing water"]):
        urgency = "P1_emergency" if any(term in text for term in ["30 minutes", "right now", "immediately", "active", "just happened"]) else "P2_urgent"
        return UrgencyClassification(
            damage_type="water_damage",
            urgency=urgency,
            reasoning="Water damage can spread quickly and often benefits from fast mitigation.",
            immediate_actions=[
                "Stop the source if safe.",
                "Move contents away from affected areas.",
                "Take photos and note when the damage was discovered.",
            ],
        )

    if any(term in text for term in ["fire", "smoke", "soot", "grease fire"]):
        return UrgencyClassification(
            damage_type="fire_damage",
            urgency="P2_urgent",
            reasoning="Recent fire or smoke damage often needs prompt stabilization and residue assessment.",
            immediate_actions=[
                "Confirm the area is safe to enter.",
                "Document residue and affected contents.",
                "Avoid aggressive cleaning until treatment is scoped.",
            ],
        )

    if "mold" in text:
        urgency = "P2_urgent" if any(term in text for term in ["widespread", "strong odor", "active leak", "symptom"]) else "P3_standard"
        return UrgencyClassification(
            damage_type="mold",
            urgency=urgency,
            reasoning="Mold usually requires moisture-source correction first, with urgency rising if spread or health concerns are mentioned.",
            immediate_actions=[
                "Address any moisture source first.",
                "Limit disturbance of visible growth.",
                "Arrange inspection or remediation planning if spread is significant.",
            ],
        )

    return UrgencyClassification(
        damage_type="general",
        urgency="P4_inquiry",
        reasoning="The request does not describe a clear active restoration emergency.",
        immediate_actions=[
            "Clarify the damage type and timeline.",
            "Share photos or measurements if available.",
        ],
    )


def infer_severity(user_report: str) -> str:
    text = user_report.lower()
    if any(term in text for term in ["small", "patch", "minor", "single room"]):
        return "minor"
    if any(term in text for term in ["two floors", "whole first floor", "widespread", "severe", "crawl space", "standing water"]):
        return "severe"
    return "moderate"


def estimate_pricing_offline(damage_type: str, severity: str) -> PricingEstimate:
    normalized_damage_type = normalize_damage_type(damage_type)
    normalized_severity = severity if severity in {"minor", "moderate", "severe"} else "moderate"
    low, high = PRICE_BOOK[normalized_damage_type][normalized_severity]
    return PricingEstimate(
        service_type=normalized_damage_type,
        severity=normalized_severity,
        low_estimate_usd=low,
        high_estimate_usd=high,
        assumptions=[
            "Offline demo ballpark range.",
            "Not a line-item estimate and not a substitute for inspection.",
            "Assumes standard access and no major reconstruction scope.",
        ],
    )


def lookup_available_technicians_offline(damage_type: str) -> list[TechnicianRecord]:
    normalized_damage_type = normalize_damage_type(damage_type)
    records = json.loads(TECHNICIAN_FILE.read_text(encoding="utf-8"))
    technicians = [TechnicianRecord.model_validate(item) for item in records]
    matches = [
        record
        for record in technicians
        if record.on_call
        and (
            normalized_damage_type in record.specialties
            or "general" in record.specialties
        )
    ]
    matches.sort(key=lambda record: record.eta_minutes)
    return matches[:3]


def _extract_keywords(text: str) -> list[str]:
    words = re.findall(r"[a-zA-Z]+", text.lower())
    return [word for word in words if len(word) > 2 and word not in STOP_WORDS]


def search_knowledge_base_offline(question: str) -> list[dict]:
    keywords = _extract_keywords(question)
    results = []
    for path in sorted(KNOWLEDGE_DIR.glob("*.md")):
        content = path.read_text(encoding="utf-8")
        lowered = content.lower()
        score = sum(lowered.count(keyword) for keyword in keywords)
        if score <= 0:
            continue
        snippet = " ".join(content.split())[:500]
        results.append({"source": path.name, "score": score, "snippet": snippet})
    results.sort(key=lambda item: item["score"], reverse=True)
    return results[:3]


def answer_offline(user_report: str) -> tuple[str, list[dict]]:
    text = user_report.lower()
    tool_calls = []

    classification = classify_urgency_offline(user_report)
    tool_calls.append(
        {
            "name": "classify_urgency_offline",
            "args": classification.model_dump(),
        }
    )

    if any(term in text for term in ["price", "cost", "estimate", "ballpark"]):
        severity = infer_severity(user_report)
        estimate = estimate_pricing_offline(classification.damage_type, severity)
        tool_calls.append(
            {
                "name": "estimate_pricing_offline",
                "args": estimate.model_dump(),
            }
        )
        answer = (
            f"Offline demo mode classified this as `{classification.damage_type}` with urgency "
            f"`{classification.urgency}`.\n\n"
            f"Ballpark range: `${estimate.low_estimate_usd:,}` to `${estimate.high_estimate_usd:,}`.\n\n"
            f"Why: {classification.reasoning}\n\n"
            f"Immediate actions:\n- " + "\n- ".join(classification.immediate_actions) + "\n\n"
            "This is a deterministic demo estimate, not a scoped restoration bid."
        )
        return answer, tool_calls

    if any(term in text for term in ["technician", "crew", "dispatch", "available", "someone here"]):
        matches = lookup_available_technicians_offline(classification.damage_type)
        tool_calls.append(
            {
                "name": "lookup_available_technicians_offline",
                "args": [match.model_dump() for match in matches],
            }
        )
        if matches:
            match_lines = [f"- {match.name}: ETA {match.eta_minutes} min, certs {', '.join(match.certifications)}" for match in matches]
            dispatch_block = "\n".join(match_lines)
        else:
            dispatch_block = "- No mock technicians are marked on-call for that specialty."
        answer = (
            f"Offline demo mode classified this as `{classification.damage_type}` with urgency "
            f"`{classification.urgency}`.\n\n"
            f"Why: {classification.reasoning}\n\n"
            "Mock dispatch matches:\n"
            f"{dispatch_block}\n\n"
            "This dispatch data is mock portfolio data, not a live scheduling feed."
        )
        return answer, tool_calls

    kb_results = search_knowledge_base_offline(user_report)
    tool_calls.append(
        {
            "name": "search_knowledge_base_offline",
            "args": kb_results,
        }
    )
    if kb_results:
        source_block = "\n".join(
            f"- {item['source']}: {item['snippet'][:180]}..."
            for item in kb_results
        )
    else:
        source_block = "- No strong local keyword match was found."

    answer = (
        f"Offline demo mode classified this as `{classification.damage_type}` with urgency "
        f"`{classification.urgency}`.\n\n"
        f"Why: {classification.reasoning}\n\n"
        f"Immediate actions:\n- " + "\n- ".join(classification.immediate_actions) + "\n\n"
        "Relevant local notes:\n"
        f"{source_block}\n\n"
        "This offline path is a deterministic preview. Add an OpenAI API key to enable the full LangGraph agent."
    )
    return answer, tool_calls
