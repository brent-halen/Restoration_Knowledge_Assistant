import os
import uuid

import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage

from src.agent import get_agent, get_langfuse_handler
from src.knowledge_base import build_vectorstore
from src.offline_demo import answer_offline


st.set_page_config(page_title="Restoration Agent Demo", page_icon="R", layout="wide")


@st.cache_resource(show_spinner=False)
def load_resources():
    build_vectorstore()
    return get_agent()


def hydrate_env_from_streamlit_secrets():
    for key in [
        "OPENAI_API_KEY",
        "LANGFUSE_PUBLIC_KEY",
        "LANGFUSE_SECRET_KEY",
        "LANGFUSE_HOST",
        "LLM_MODEL",
        "JUDGE_MODEL",
        "EMBEDDING_MODEL",
        "RETRIEVAL_K",
    ]:
        if key in st.secrets and not os.getenv(key):
            os.environ[key] = str(st.secrets[key])


def init_session_state():
    if "thread_id" not in st.session_state:
        st.session_state.thread_id = f"demo-{uuid.uuid4()}"
    if "messages" not in st.session_state:
        st.session_state.messages = []


def render_sidebar():
    st.sidebar.title("Demo Status")
    st.sidebar.caption("Portfolio starter, not production software.")
    st.sidebar.write("Knowledge base: seeded local markdown files")
    st.sidebar.write("Pricing: deterministic demo ranges")
    st.sidebar.write("Technicians: mock availability data")
    st.sidebar.write(f"Session thread: `{st.session_state.thread_id}`")
    mode = "Live agent mode" if os.getenv("OPENAI_API_KEY") else "Offline preview mode"
    st.sidebar.write(f"Mode: {mode}")


def extract_tool_calls(agent_result) -> list[dict]:
    tool_calls = []
    for message in agent_result["messages"]:
        if isinstance(message, AIMessage) and message.tool_calls:
            for tool_call in message.tool_calls:
                tool_calls.append(
                    {
                        "name": tool_call["name"],
                        "args": str(tool_call["args"]),
                    }
                )
    return tool_calls


def main():
    init_session_state()
    hydrate_env_from_streamlit_secrets()
    has_openai_key = bool(os.getenv("OPENAI_API_KEY"))

    st.title("Restoration Knowledge Assistant")
    st.caption(
        "Single-agent portfolio demo with retrieval, structured urgency classification, "
        "deterministic pricing, and mock dispatch data."
    )
    render_sidebar()
    if not has_openai_key:
        st.info(
            "Running in offline preview mode because `OPENAI_API_KEY` is not configured. "
            "You can still demo classification, local retrieval, pricing, and mock dispatch."
        )
        agent = None
    else:
        try:
            agent = load_resources()
        except Exception as exc:
            st.error(f"Startup error: {exc}")
            st.info("Add OPENAI_API_KEY to .env or .streamlit/secrets.toml and restart the app.")
            st.stop()

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message.get("tool_calls"):
                with st.expander("Tool calls", expanded=False):
                    for tool_call in message["tool_calls"]:
                        st.code(
                            f"Tool: {tool_call['name']}\nArgs: {tool_call['args']}",
                            language="yaml",
                        )

    prompt = st.chat_input("Describe the damage situation or ask a workflow question.")
    if not prompt:
        return

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    callbacks = []
    if has_openai_key:
        langfuse_handler = get_langfuse_handler()
        if langfuse_handler:
            callbacks.append(langfuse_handler)

    with st.chat_message("assistant"):
        with st.spinner("Thinking through the request..."):
            if not has_openai_key:
                answer, tool_calls = answer_offline(prompt)
            else:
                try:
                    result = agent.invoke(
                        {"messages": [HumanMessage(content=prompt)]},
                        config={
                            "configurable": {"thread_id": st.session_state.thread_id},
                            "callbacks": callbacks,
                        },
                    )
                    answer = result["messages"][-1].content
                    tool_calls = extract_tool_calls(result)
                except Exception as exc:
                    st.warning(
                        "Live agent call failed, so the app switched to offline preview mode "
                        f"for this message. Details: {exc}"
                    )
                    answer, tool_calls = answer_offline(prompt)
            st.markdown(answer)
            if tool_calls:
                with st.expander("Tool calls", expanded=False):
                    for tool_call in tool_calls:
                        st.code(
                            f"Tool: {tool_call['name']}\nArgs: {tool_call['args']}",
                            language="yaml",
                        )

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": answer,
            "tool_calls": tool_calls,
        }
    )


if __name__ == "__main__":
    main()
