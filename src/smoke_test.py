import argparse
import json

from langchain_core.messages import HumanMessage

from src.agent import get_agent
from src.offline_demo import answer_offline


DEFAULT_QUERY = (
    "My basement has standing water from a burst pipe that started 20 minutes ago. "
    "What should I do first, and do you have any technicians available?"
)


def run_offline(query: str):
    answer, tool_calls = answer_offline(query)
    payload = {
        "mode": "offline",
        "query": query,
        "answer": answer,
        "tool_calls": tool_calls,
    }
    print(json.dumps(payload, indent=2))


def run_live(query: str):
    agent = get_agent()
    result = agent.invoke(
        {"messages": [HumanMessage(content=query)]},
        config={"configurable": {"thread_id": "smoke-test"}},
    )

    tool_calls = []
    for message in result["messages"]:
        if getattr(message, "tool_calls", None):
            tool_calls.extend(call["name"] for call in message.tool_calls)

    payload = {
        "mode": "live",
        "query": query,
        "answer": result["messages"][-1].content,
        "tool_calls": tool_calls,
    }
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["offline", "live"], default="offline")
    parser.add_argument("--query", default=DEFAULT_QUERY)
    args = parser.parse_args()

    if args.mode == "offline":
        run_offline(args.query)
    else:
        run_live(args.query)

