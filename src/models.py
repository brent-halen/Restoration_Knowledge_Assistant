from typing import Literal

from pydantic import BaseModel, Field


class UrgencyClassification(BaseModel):
    damage_type: Literal["water_damage", "fire_damage", "mold", "general"]
    urgency: Literal["P1_emergency", "P2_urgent", "P3_standard", "P4_inquiry"]
    reasoning: str = Field(description="Short explanation for the urgency decision.")
    immediate_actions: list[str] = Field(
        default_factory=list,
        description="Concrete next actions for the user.",
    )


class PricingEstimate(BaseModel):
    service_type: str
    severity: Literal["minor", "moderate", "severe"]
    low_estimate_usd: int
    high_estimate_usd: int
    assumptions: list[str] = Field(default_factory=list)


class TechnicianRecord(BaseModel):
    name: str
    certifications: list[str]
    specialties: list[str]
    on_call: bool
    eta_minutes: int


class EvaluationScore(BaseModel):
    classification_accuracy: int = Field(ge=1, le=5)
    completeness: int = Field(ge=1, le=5)
    actionability: int = Field(ge=1, le=5)
    safety_awareness: int = Field(ge=1, le=5)
    tone: int = Field(ge=1, le=5)
    notes: str

