# Technical Guide — STS Ewe↔Fr

This guide explains how the repo is wired (backend + manifests + training/eval) and how to operate it on Windows.

If you just want to run the demo in mock mode first, start here:
- `docs/getting_started/GETTING_STARTED.md`

## 1) Architecture overview

The end-to-end STS pipeline is:

1. **STT**: audio → transcript
2. **MT**: transcript → translation
3. **TTS**: translation → synthesized audio

The system supports both directions via a single `direction` parameter:
- `ee_to_fr`
- `fr_to_ee`

The backend uses a **provider registry** controlled by environment variables so you can start in `mock` mode and later swap to real local models.

Related roadmap/diagram:
- `docs/architecture/DEMO_7J_ROADMAP_ARCHI.md`

## 2) Backend

### 2.1 Run

```powershell
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
Copy-Item backend\.env.example backend\.env
.\.venv\Scripts\python.exe -m uvicorn backend.app:app --reload --host 127.0.0.1 --port 8000
```

- Swagger UI: http://127.0.0.1:8000/docs
- Health: http://127.0.0.1:8000/health

### 2.2 API endpoints

#### `GET /health`
Returns `{ "status": "ok" }`.

#### `POST /api/stt`
- **Content-Type**: `multipart/form-data`
- **Fields**:
  - `direction`: `ee_to_fr` or `fr_to_ee`
  - `audio`: file

PowerShell example:

```powershell
$uri = "http://127.0.0.1:8000/api/stt"
$form = @{
  direction = "ee_to_fr"
  audio = Get-Item "path\to\audio.wav"
}
Invoke-RestMethod -Method Post -Uri $uri -Form $form
```

#### `POST /api/translate`
- **Content-Type**: JSON
- Body:

```json
{ "direction": "ee_to_fr", "text": "..." }
```

PowerShell:

```powershell
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/api/translate" -ContentType "application/json" -Body (@{
  direction = "ee_to_fr";
  text = "Woezɔ";
} | ConvertTo-Json)
```

#### `POST /api/tts`
- **Content-Type**: JSON
- Body:

```json
{ "direction": "ee_to_fr", "text": "...", "return_base64": false }
```

Response includes an `audio_url` you can fetch:
- `GET /api/audio/{audio_id}`

#### `POST /api/sts`
- **Content-Type**: `multipart/form-data`
- Fields:
  - `direction`
  - `audio`
  - `return_audio_base64` (optional boolean)

PowerShell:

```powershell
$uri = "http://127.0.0.1:8000/api/sts"
$form = @{
  direction = "ee_to_fr"
  audio = Get-Item "path\to\audio.wav"
  return_audio_base64 = "false"
}
Invoke-RestMethod -Method Post -Uri $uri -Form $form
```

#### `GET /api/history?limit=50`
Returns recent interactions stored in SQLite.

### 2.3 Storage & DB

- Audio outputs are stored under `backend/storage/audio/` by default.
  - Controlled by `AUDIO_STORAGE_DIR` (relative to the backend folder by default).
- History DB lives at `database/app.db` (repo root).

### 2.4 Provider configuration

Providers are selected via `backend/.env`:

```text
# Provider selection
STT_PROVIDER=mock            # supported: mock, local_whisper
MT_PROVIDER=mock             # supported: mock, local_transformers
TTS_PROVIDER=mock            # only mock currently

# CORS
CORS_ORIGINS=http://localhost:5173

# Audio output dir (relative to backend/ unless absolute)
AUDIO_STORAGE_DIR=storage/audio

# Local STT (Whisper)
STT_MODEL_DIR=models/asr_whisper_ewe
WHISPER_LANGUAGE=ewe
WHISPER_TASK=transcribe

# Local MT (Transformers)
MT_MODEL_DIR_EE_TO_FR=models/mt_ee_to_fr
MT_MODEL_DIR_FR_TO_EE=models/mt_fr_to_ee
```

Notes:
- `mock` providers require no GPU and no keys.
- For `local_transformers` and `local_whisper`, you must train/download models first.

## 3) Data & manifests

### 3.1 Canonical locations

All generated manifests are under:
- ASR: `data/manifests/asr/`
- MT: `data/manifests/mt/`
- Text-only: `data/manifests/text/`

Generated dataset stats JSON are under `docs/stats/`.

### 3.2 Manifest formats

ASR manifests are TSV with columns (see `tools/analysis/analyze_manifest_asr.py`):
- `split` (train/dev/test)
- `audio` (or legacy: `audio_path`)
- `text`
- `speaker_id`
- `locale`

MT bitext manifest is TSV with columns:
- `split` (train/dev/test)
- `ee`
- `fr`

### 3.3 Rebuilding manifests

Common builders:

```powershell
.\.venv\Scripts\python.exe tools\manifests\build_manifest_ewe2_audio.py --out-tsv data\manifests\asr\manifest_ewe2_audio.tsv --out-json docs\stats\ewe2_audio_stats.json
.\.venv\Scripts\python.exe tools\manifests\build_manifest_ewe_fr_bitext.py --out-tsv data\manifests\mt\manifest_ewe_fr_bitext.tsv --out-json docs\stats\ewe_fr_bitext_stats.json
.\.venv\Scripts\python.exe tools\manifests\build_manifest_asr_global.py --out-tsv data\manifests\asr\manifest_asr_global.tsv --out-json docs\stats\asr_global_stats.json
```

## 4) Training & inference (ML)

### 4.1 MT

Train:

```powershell
.\.venv\Scripts\python.exe -m pip install torch transformers accelerate datasets evaluate sacrebleu sentencepiece

.\.venv\Scripts\python.exe ml\mt\train_mt.py --manifest data\manifests\mt\manifest_ewe_fr_bitext.tsv --direction ee_to_fr --model facebook/nllb-200-distilled-600M --out-dir models\mt_ee_to_fr
.\.venv\Scripts\python.exe ml\mt\train_mt.py --manifest data\manifests\mt\manifest_ewe_fr_bitext.tsv --direction fr_to_ee --model facebook/nllb-200-distilled-600M --out-dir models\mt_fr_to_ee
```

CLI inference (uses the backend local provider logic):

```powershell
.\.venv\Scripts\python.exe ml\mt\inference.py --direction ee_to_fr --text "Woezɔ" --model-dir-ee-to-fr models\mt_ee_to_fr
```

### 4.2 ASR (Whisper)

Train:

```powershell
.\.venv\Scripts\python.exe -m pip install torch transformers accelerate datasets evaluate jiwer soundfile
.\.venv\Scripts\python.exe ml\asr\train_asr.py --manifest data\manifests\asr\manifest_ewe2_audio.tsv --model openai/whisper-small --out-dir models\asr_whisper_ewe --language ewe --task transcribe
```

CLI inference:

```powershell
.\.venv\Scripts\python.exe ml\asr\inference.py --direction ee_to_fr --audio path\to\audio.wav --model-dir models\asr_whisper_ewe
```

### 4.3 TTS

Current TTS provider is `mock` (generates a simple WAV) for demo wiring.

CLI:

```powershell
.\.venv\Scripts\python.exe ml\tts\inference.py --direction ee_to_fr --text "Bonjour" --out-wav out.wav
```

## 5) Evaluation & results

Evaluation scripts write:
- Metrics JSON: `docs/results/*.json`
- Predictions CSV: `docs/results/*.csv`

Examples:

```powershell

.\.venv\Scripts\python.exe tools\eval\evaluate_mt.py --manifest data\manifests\mt\manifest_ewe_fr_bitext.tsv --direction ee_to_fr --model-dir models\mt_ee_to_fr --out-json docs\results\mt_metrics_ee_to_fr.json --out-csv-prefix docs\results\mt_preds_ee_to_fr --max-examples 2000

.\.venv\Scripts\python.exe tools\eval\evaluate_asr.py --manifest data\manifests\asr\manifest_ewe2_audio.tsv --model-dir models\asr_whisper_ewe --out-json docs\results\asr_metrics.json --out-csv-prefix docs\results\asr_preds --max-examples 500
```

Notebook analysis:
- `notebooks/RESULTS_ANALYSIS.ipynb`

## 6) Troubleshooting

- **Torch install issues**: install torch separately from https://pytorch.org/ (CPU vs CUDA), then install the rest.
- **Audio decoding**: some pipelines may require `ffmpeg` depending on the format; prefer `.wav` uploads for the demo.
- **Path issues**: training/eval/build scripts resolve repo root automatically; you can run them from any working directory.
