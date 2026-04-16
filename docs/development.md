# Development Notes

## Local setup

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
streamlit run src/app.py
```

Add `OPENAI_API_KEY` to `.env` to enable live agent mode.

## Test commands

```powershell
.venv\Scripts\Activate.ps1
python -m pytest -q
python -m src.eval --mode offline
python -m src.smoke_test --mode offline
python -m compileall src tests
```

## Docker commands

Build:

```powershell
docker build -t restoration-knowledge-assistant .
```

Run:

```powershell
docker run --rm -p 8501:8501 --env-file .env -e CHROMA_PERSIST_DIR=/app/chroma_db restoration-knowledge-assistant
```

Compose:

```powershell
docker compose up --build
```

The compose file uses a named volume for `chroma_db` so embeddings do not need to be rebuilt on every restart.

## Demo prompts

- `My basement has standing water from a burst pipe that started 20 minutes ago. What should I do first?`
- `Do you have technicians available for smoke damage cleanup?`
- `What would a moderate mold remediation job usually cost?`
- `What should I document for insurance after water damage?`

## Environment notes

- Python `3.14` worked in this repository during setup, though `3.12` or `3.13` remains the safer default for broader AI package compatibility.
- The app automatically falls back to offline preview mode when live API access is unavailable.
- Live requests require both a valid API key and available OpenAI quota.

## Current scope

This project is intentionally narrow. It focuses on triage, retrieval, pricing guidance, and dispatch-style lookup rather than trying to simulate a full restoration operating system.
