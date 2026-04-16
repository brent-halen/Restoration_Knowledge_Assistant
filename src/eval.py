import json
from statistics import mean

from langchain_core.messages import HumanMessage

from src.agent import get_agent
from src.offline_demo import answer_offline


TEST_SCENARIOS = [
    {
        "query": "My basement has standing water from a burst pipe that started 30 minutes ago.",
        "expected_damage_type": "water_damage",
        "expected_urgency": "P1_emergency",
        "expected_tools": ["classify_urgency_offline", "search_knowledge_base_offline"],
    },
    {
        "query": "I found a small patch of mold behind a bathroom vanity and there is no active leak now.",
        "expected_damage_type": "mold",
        "expected_urgency": "P3_standard",
        "expected_tools": ["classify_urgency_offline", "search_knowledge_base_offline"],
    },
    {
        "query": "There was a kitchen fire yesterday and now the whole first floor smells like smoke.",
        "expected_damage_type": "fire_damage",
        "expected_urgency": "P2_urgent",
        "expected_tools": ["classify_urgency_offline", "search_knowledge_base_offline"],
    },
    {
        "query": "What would a moderate mold remediation job usually cost?",
        "expected_damage_type": "mold",
        "expected_urgency": "P3_standard",
        "expected_tools": ["classify_urgency_offline", "estimate_pricing_offline"],
    },
    {
        "query": "Sewage is coming up through my basement drain right now.",
        "expected_damage_type": "water_damage",
        "expected_urgency": "P1_emergency",
        "expected_tools": ["classify_urgency_offline", "search_knowledge_base_offline"],
    },
    {
        "query": "Do you have technicians available for smoke damage cleanup?",
        "expected_damage_type": "fire_damage",
        "expected_urgency": "P2_urgent",
        "expected_tools": ["classify_urgency_offline", "lookup_available_technicians_offline"],
    },
]


def _extract_classification(tool_calls: list[dict]) -> dict:
    for call in tool_calls:
        if call["name"] == "classify_urgency_offline":
            return call["args"]
    return {}


def evaluate_offline() -> dict:
    results = []
    for index, scenario in enumerate(TEST_SCENARIOS, start=1):
        answer, tool_calls = answer_offline(scenario["query"])
        classification = _extract_classification(tool_calls)
        tool_names = [call["name"] for call in tool_calls]

        damage_type_match = (
            classification.get("damage_type") == scenario["expected_damage_type"]
        )
        urgency_match = classification.get("urgency") == scenario["expected_urgency"]
        tools_match = all(
            expected_tool in tool_names for expected_tool in scenario["expected_tools"]
        )
        answer_present = bool(answer.strip())

        passed_checks = [
            damage_type_match,
            urgency_match,
            tools_match,
            answer_present,
        ]

        results.append(
            {
                "scenario_index": index,
                "query": scenario["query"],
                "damage_type_match": damage_type_match,
                "urgency_match": urgency_match,
                "tools_match": tools_match,
                "answer_present": answer_present,
                "score_pct": round(sum(passed_checks) / len(passed_checks) * 100, 1),
                "tool_calls": tool_names,
                "answer_preview": answer[:180],
            }
        )

    overall_score = round(mean(item["score_pct"] for item in results), 1)
    return {
        "mode": "offline",
        "scenario_count": len(results),
        "overall_score_pct": overall_score,
        "results": results,
    }


def evaluate_live() -> dict:
    agent = get_agent()
    results = []
    for index, scenario in enumerate(TEST_SCENARIOS, start=1):
        result = agent.invoke(
            {"messages": [HumanMessage(content=scenario["query"])]},
            config={"configurable": {"thread_id": f"eval-live-{index}"}},
        )
        tool_names = []
        for message in result["messages"]:
            if getattr(message, "tool_calls", None):
                tool_names.extend(call["name"] for call in message.tool_calls)

        answer = result["messages"][-1].content
        results.append(
            {
                "scenario_index": index,
                "query": scenario["query"],
                "tool_calls": tool_names,
                "answer_preview": answer[:180],
            }
        )

    return {
        "mode": "live",
        "scenario_count": len(results),
        "results": results,
    }


def print_markdown_summary(summary: dict):
    print("\nMARKDOWN_TABLE_START")
    if summary["mode"] == "offline":
        print("| # | Damage | Urgency | Tools | Score |")
        print("|---|--------|---------|-------|-------|")
        for item in summary["results"]:
            print(
                "| "
                f"{item['scenario_index']} | "
                f"{'PASS' if item['damage_type_match'] else 'FAIL'} | "
                f"{'PASS' if item['urgency_match'] else 'FAIL'} | "
                f"{'PASS' if item['tools_match'] else 'FAIL'} | "
                f"{item['score_pct']}% |"
            )
    else:
        print("| # | Tool Calls | Answer Preview |")
        print("|---|------------|----------------|")
        for item in summary["results"]:
            tool_names = ", ".join(item["tool_calls"])
            preview = item["answer_preview"].replace("|", "/")
            print(f"| {item['scenario_index']} | {tool_names} | {preview} |")
    print("MARKDOWN_TABLE_END")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode",
        choices=["offline", "live"],
        default="offline",
        help="Evaluation mode. Offline is deterministic and does not require live model access.",
    )
    args = parser.parse_args()

    summary = evaluate_offline() if args.mode == "offline" else evaluate_live()
    print(json.dumps(summary, indent=2))
    print_markdown_summary(summary)
