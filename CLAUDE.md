# Restoration Knowledge Assistant

Single-agent restoration workflow assistant built with LangGraph, Streamlit, Chroma, and OpenAI-compatible tooling.

## Commands

- `python -m venv .venv`
- `.venv\Scripts\Activate.ps1`
- `python -m pip install -r requirements.txt`
- `streamlit run src/app.py`
- `python src/eval.py`
- `python -m pytest -q`
- `python -m compileall src tests`

## Architecture

- `src/knowledge_base.py`: loads seeded markdown docs and builds Chroma on demand
- `src/tools.py`: retrieval, urgency classification, pricing, technician lookup
- `src/agent.py`: LangGraph ReAct agent and live-model wiring
- `src/offline_demo.py`: fallback behavior when live AI calls are unavailable
- `src/app.py`: Streamlit chat interface with tool-call visibility
- `src/eval.py`: evaluation harness for scenario-based checks

## Rules

- Keep the project single-agent unless there is a measured reason to split it.
- Treat safety-sensitive remediation guidance conservatively.
- Do not present mock pricing or mock technician data as production truth.
- Prefer deterministic logic for estimates and routing whenever possible.

