# Getting Started (Windows / PowerShell)

Goal: run the backend in **mock mode** (no GPU, no keys), then do a quick end-to-end call:
- `POST /api/sts` (Speech → Text → Speech)

If you want training later, see `docs/training/TRAINING_MODELS.md`.

## 1) Create venv

From repo root:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -U pip
```

## 2) Install backend deps + configure env

```powershell
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
Copy-Item backend\.env.example backend\.env
```

By default, `backend/.env` uses mock providers:
- `STT_PROVIDER=mock`
- `MT_PROVIDER=mock`
- `TTS_PROVIDER=mock`

## 3) Run the backend

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.app:app --reload --host 127.0.0.1 --port 8000
```

Check:
- http://127.0.0.1:8000/health
- http://127.0.0.1:8000/docs

## 4) Create a tiny WAV test file

This generates a short beep WAV locally (no extra deps):

```powershell
@'
import wave, math
sr = 22050
seconds = 1.0
freq = 440.0
amp = 12000
n = int(sr * seconds)
with wave.open('test.wav', 'wb') as wf:
    wf.setnchannels(1)
    wf.setsampwidth(2)
    wf.setframerate(sr)
    for i in range(n):
        t = i / sr
        sample = int(amp * math.sin(2 * math.pi * freq * t))
        wf.writeframesraw(sample.to_bytes(2, byteorder='little', signed=True))
print('wrote: test.wav')
'@ | .\.venv\Scripts\python.exe -
```

## 5) Call STS (end-to-end)

```powershell
$uri = "http://127.0.0.1:8000/api/sts"
$form = @{
  direction = "ee_to_fr"
  audio = Get-Item "test.wav"
  return_audio_base64 = "false"
}
Invoke-RestMethod -Method Post -Uri $uri -Form $form
```

Expected response shape:
- `transcript`: mock transcript
- `translation`: mock translation
- `tts.audio_url`: URL to fetch WAV

Fetch the audio:

```powershell
# Replace with the returned URL
Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/audio/<audio_id>" -OutFile out.wav
```

## 6) (Optional) Run training (quick)

```powershell
.\.venv\Scripts\python.exe ml\train_all.py --quick
```

Resume from the latest checkpoints:

```powershell
.\.venv\Scripts\python.exe ml\train_all.py --quick --resume auto
```

Or run a single trainer directly:

```powershell
# ASR (Whisper) — now has a default output dir
.\.venv\Scripts\python.exe ml\asr\train_asr.py --max-train 5000 --max-eval 500

# MT (NLLB) — output dir defaults to models/mt_<direction>
.\.venv\Scripts\python.exe ml\mt\train_mt.py --direction ee_to_fr --max-train 20000 --max-eval 2000
```
