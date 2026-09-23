# STS (Ewe ↔ Français)

End-to-end demo project for **Speech → Text → Speech** in both directions:
- **Ewe → Français**
- **Français → Ewe**

The repository contains:
- A **FastAPI backend** with a provider-based architecture (mock by default)
- **Manifests** for ASR + MT datasets
- **Training + evaluation** entrypoints under `ml/`
- A `tools/` package for dataset tooling (manifests, checks, evaluation)

## Quick links
- Getting started: `docs/getting_started/GETTING_STARTED.md`
- Technical guide: `docs/technical/TECHNICAL_GUIDE.md`
- Training guide: `docs/training/TRAINING_MODELS.md`
- Backend-only readme: `backend/README.md`

## Repo layout

- `backend/` — FastAPI API server (STT / MT / TTS / STS)
- `ml/` — ML entrypoints
  - `ml/mt/train_mt.py`, `ml/mt/inference.py`
  - `ml/asr/train_asr.py`, `ml/asr/inference.py`
  - `ml/tts/inference.py`
- `tools/` — dataset tooling + evaluation (Python)
- `data/` — datasets (raw) + canonical manifests under `data/manifests/`
- `docs/` — roadmap, reports, training docs, stats
- `database/` — SQLite DB (`database/app.db`) used by the backend history endpoint
- `frontend/` — static assets/templates (UI can be wired to the backend)

## Setup (Windows / PowerShell)

Create a venv at repo root (recommended):

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -U pip
```

### Option A — Backend only (fast, demo with mocks)

```powershell
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
Copy-Item backend\.env.example backend\.env
```

Run the API:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.app:app --reload --host 127.0.0.1 --port 8000
```

Open:
- http://127.0.0.1:8000/health
- http://127.0.0.1:8000/docs

### Option B — Full project (training + evaluation)

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item backend\.env.example backend\.env
```

If `torch` installation fails, install it from https://pytorch.org/ first (CPU vs CUDA), then re-run the command above.

## Run a full (quick) training sweep

This trains MT (both directions) + ASR (Whisper) and writes checkpoints under `models/`.

```powershell
# trains MT (both directions) + ASR
\.\.venv\Scripts\python.exe ml\train_all.py --quick
```

Resume from the latest checkpoints:

```powershell
\.\.venv\Scripts\python.exe ml\train_all.py --quick --resume auto
```

## Data & manifests

Canonical manifest locations:
- ASR: `data/manifests/asr/`
- MT: `data/manifests/mt/`
- Text-only corpora: `data/manifests/text/`

Generated stats JSON are stored under `docs/stats/`.

## Backend API (high level)

Directions are always one of:
- `ee_to_fr`
- `fr_to_ee`

Main endpoints:
- `POST /api/stt` (multipart form: `direction`, `audio`)
- `POST /api/translate` (JSON: `direction`, `text`)
- `POST /api/tts` (JSON: `direction`, `text`)
- `POST /api/sts` (multipart form: `direction`, `audio`)
- `GET /api/history`

See `docs/technical/TECHNICAL_GUIDE.md` for exact request formats and examples.
