from src.offline_demo import (
    answer_offline,
    classify_urgency_offline,
    estimate_pricing_offline,
    search_knowledge_base_offline,
)


def test_classify_urgency_offline_for_sewage_backup():
    result = classify_urgency_offline(
        "Sewage is backing up through my basement drain right now."
    )
    assert result.damage_type == "water_damage"
    assert result.urgency == "P1_emergency"


def test_estimate_pricing_offline_returns_ballpark():
    result = estimate_pricing_offline("mold", "moderate")
    assert result.low_estimate_usd == 3500
    assert result.high_estimate_usd == 9000


def test_search_knowledge_base_offline_finds_relevant_docs():
    results = search_knowledge_base_offline("What should I document for insurance after water damage?")
    assert results
    assert any("insurance" in item["source"] or "water" in item["source"] for item in results)


def test_answer_offline_returns_tool_calls():
    answer, tool_calls = answer_offline(
        "A pipe burst and there is standing water in my basement right now. Do you have technicians available?"
    )
    assert "Offline demo mode" in answer
    assert tool_calls
    assert any(call["name"] == "lookup_available_technicians_offline" for call in tool_calls)
