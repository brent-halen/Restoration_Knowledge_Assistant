import json
from statistics import mean

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

from src.agent import get_agent
from src.config import get_settings
from src.models import EvaluationScore


TEST_SCENARIOS = [
    {
        "query": "My basement has standing water from a burst pipe that started 30 minutes ago.",
        "expected_damage_type": "water_damage",
        "expected_urgency": "P1_emergency",
    },
    {
        "query": "I found a small patch of mold behind a bathroom vanity and there is no active leak now.",
        "expected_damage_type": "mold",
        "expected_urgency": "P3_standard",
    },
    {
        "query": "There was a kitchen fire yesterday and now the whole first floor smells like smoke.",
        "expected_damage_type": "fire_damage",
        "expected_urgency": "P2_urgent",
    },
    {
        "query": "What would a moderate mold remediation job usually cost?",
        "expected_damage_type": "mold",
        "expected_urgency": "P4_inquiry",
    },
    {
        "query": "Sewage is coming up through my basement drain right now.",
        "expected_damage_type": "water_damage",
        "expected_urgency": "P1_emergency",
    },
    {
        "query": "Can you remodel my kitchen and install new cabinets?",
        "expected_damage_type": "general",
        "expected_urgency": "P4_inquiry",
    },
]


def judge_response(query: str, response: str, expected: dict) -> EvaluationScore:
    settings = get_settings()
    judge = ChatOpenAI(
        model=settings.judge_model,
        temperature=0,
        api_key=settings.openai_api_key,
    )
    structured_judge = judge.with_structured_output(EvaluationScore)
    return structured_judge.invoke(
        (
            "Evaluate this restoration assistant response on a 1-5 scale for "
            "classification_accuracy, completeness, actionability, safety_awareness, and tone. "
            "Be strict. The expected damage type is "
            f"{expected['expected_damage_type']} and the expected urgency is "
            f"{expected['expected_urgency']}.\n\n"
            f"User query:\n{query}\n\nAssistant response:\n{response}"
        )
    )


def run_evaluation():
    agent = get_agent()
    results = []
    for scenario in TEST_SCENARIOS:
        result = agent.invoke({"messages": [HumanMessage(content=scenario["query"])]})
        response = result["messages"][-1].content
        tool_calls = []
        for message in result["messages"]:
            if getattr(message, "tool_calls", None):
                tool_calls.extend(call["name"] for call in message.tool_calls)

        scores = judge_response(scenario["query"], response, scenario)
        results.append(
            {
                "query": scenario["query"],
                "response": response,
                "tool_calls": tool_calls,
                "scores": scores.model_dump(),
            }
        )
    return results


if __name__ == "__main__":
    output = run_evaluation()
    totals = [
        sum(
            [
                item["scores"]["classification_accuracy"],
                item["scores"]["completeness"],
                item["scores"]["actionability"],
                item["scores"]["safety_awareness"],
                item["scores"]["tone"],
            ]
        )
        for item in output
    ]
    summary = {
        "average_total": round(mean(totals), 2),
        "results": output,
    }
    print(json.dumps(summary, indent=2))
