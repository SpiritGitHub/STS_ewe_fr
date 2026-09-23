# Backend (STS Ewe↔Fr)

Backend API for the demo:
- Speak → transcript on screen
- Translate
- Synthesize audio
- Supports both directions (Ewe→Fr and Fr→Ewe)

## Setup (PowerShell)
From repo root (`F:/STS`):

```powershell
F:/STS/.venv/Scripts/python.exe -m pip install -r backend/requirements.txt
Copy-Item backend/.env.example backend/.env
```

## Run
```powershell
F:/STS/.venv/Scripts/python.exe -m uvicorn backend.app:app --reload --host 127.0.0.1 --port 8000
```

Open:
- http://127.0.0.1:8000/health
- http://127.0.0.1:8000/docs

## Providers
Default mode is `mock` (no keys, no GPU). You can later add real providers for:
- STT: Whisper local / Azure / OpenAI
- MT: fine-tuned HF model
- TTS: Azure / Coqui
