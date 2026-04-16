from functools import lru_cache

from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

from src.config import get_settings
from src.tools import get_tools


SYSTEM_PROMPT = """
You are a restoration knowledge assistant used in a portfolio demo.

Goals:
- help users understand likely urgency and sensible next steps
- use tools when tool output would improve accuracy
- keep advice conservative when safety is uncertain

Rules:
- Call classify_urgency for active incidents or when urgency is unclear.
- Call search_knowledge_base for procedural or safety guidance.
- Use estimate_pricing only for rough demo estimates and clearly say they are ballpark numbers.
- Use lookup_available_technicians only when the user asks about staffing or dispatch.
- Do not imply that mock technician or pricing data is real production data.
- Do not claim a remote chat replaces on-site inspection or emergency services.
""".strip()


def get_langfuse_handler():
    settings = get_settings()
    if not settings.langfuse_public_key or not settings.langfuse_secret_key:
        return None

    try:
        from langfuse.langchain import CallbackHandler
    except ImportError:
        return None

    return CallbackHandler(
        public_key=settings.langfuse_public_key,
        secret_key=settings.langfuse_secret_key,
        host=settings.langfuse_host,
    )


@lru_cache(maxsize=1)
def get_agent():
    settings = get_settings()
    model = ChatOpenAI(
        model=settings.llm_model,
        temperature=settings.llm_temperature,
        api_key=settings.openai_api_key,
    )
    return create_react_agent(
        model=model,
        tools=get_tools(),
        prompt=SYSTEM_PROMPT,
        checkpointer=MemorySaver(),
    )
