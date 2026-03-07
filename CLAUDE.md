# CLAUDE.md

## Project Overview

Glucose Actions — glucose monitoring system via LibreLinkUp API with automated alerts. Reads glucose data from a FreeStyle Libre CGM sensor and fires alerts when levels leave the safe range. Runs as a cron job every 5 minutes on Linux.

## Architecture

```
cron → src/main.py (orchestrator)
         ├── src/glucose_reader.py    → pylibrelinkup → LibreLinkUp API
         ├── src/alert_engine.py      → threshold evaluation + cooldown + message building
         ├── src/state.py             → JSON state persistence (atomic writes)
         └── src/outputs/
               ├── base.py            → BaseOutput (ABC)
               ├── webhook.py         → Alexa/VoiceMonkey HTTP POST
               └── whatsapp.py        → WhatsApp Cloud API (template messages)
```

**Flow:** read glucose → check if stale → evaluate thresholds → check cooldown → build message → send via enabled outputs → persist state.

## Commands

- **Run:** `python -m src.main` (from project root, with `.venv` activated)
- **Tests:** `pytest tests/ -v`
- **Validate connections:** `python validate_lib.py`, `python validate_webhook.py`, `python validate_whatsapp.py`

## Code Conventions

- Python 3.12+ with type hints (use `str | None` not `Optional[str]`)
- No docstrings or comments unless logic is non-obvious
- Outputs extend `BaseOutput` ABC and implement `send_alert(message, glucose_value, level) -> bool`
- New output types must be wired in `build_outputs()` in `src/main.py` and configured in `config.example.yaml`
- Config loaded from `config.yaml` (YAML), secrets can be overridden via env vars
- State persisted via atomic JSON writes (temp file + `os.replace`)
- File lock via `fcntl` prevents concurrent cron runs
- Logger name: `glucose-actions`

## Key Files

- `config.yaml` — runtime config with credentials (**never commit**, in `.gitignore`)
- `config.example.yaml` — config template for new users
- `state.json` — alert state between executions (**never commit**)
- `requirements.txt` — dependencies: pylibrelinkup, PyYAML, requests, pytest

## Security

- Never commit `config.yaml` or `state.json`
- Credentials go in env vars (`LIBRELINKUP_EMAIL`, `LIBRELINKUP_PASSWORD`, `WHATSAPP_ACCESS_TOKEN`) or `config.yaml`
- Never log secrets — tokens are redacted in debug output
