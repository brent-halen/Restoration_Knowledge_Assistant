# Architecture

## Purpose

Restoration Knowledge Assistant is a single-agent application for restoration-related triage and workflow support. It combines retrieval, structured classification, deterministic estimates, and mock dispatch lookup behind a conversational interface.

## System Components

### Streamlit UI

The Streamlit app provides the chat interface, session state, sidebar status, and tool-call visibility. It is responsible for choosing between live-agent execution and offline preview behavior depending on whether working API credentials are available and whether live calls succeed.

### LangGraph agent

The live path uses a LangGraph ReAct agent. The agent receives the user message, decides when to use tools, and composes the final answer. The system prompt keeps the assistant conservative about safety, pricing, and claims of certainty.

### Tool layer

The tool layer exposes four primary capabilities:

- urgency classification
- knowledge-base retrieval
- deterministic pricing
- mock technician lookup

This keeps responsibilities explicit and makes agent behavior easier to inspect.

### Knowledge base

The knowledge base is built from seeded markdown documents stored in `data/knowledge/`. In live mode, the app indexes those documents into Chroma and uses OpenAI embeddings for retrieval.

### Offline preview engine

When live AI calls are unavailable, the app falls back to deterministic logic in `src/offline_demo.py`. This preserves the product flow for demos, reviews, and local verification.

## Execution Modes

### Live mode

Live mode is used when:

- `OPENAI_API_KEY` is configured
- the OpenAI project has available quota
- the outbound request succeeds

In this mode, the app uses the LangGraph agent and OpenAI-backed classification/retrieval pipeline.

### Offline mode

Offline mode is used when:

- no API key is configured
- a live request fails
- the project is being demonstrated without external dependencies

In this mode, the app uses heuristic classification, local keyword retrieval, deterministic pricing, and mock dispatch lookup.

## Design Principles

- Keep the architecture legible and inspectable.
- Prefer deterministic behavior where hallucinations would be costly or misleading.
- Expose tool use to the user rather than hiding agent internals.
- Make the app resilient to missing credentials, quota issues, and live-service failure.

