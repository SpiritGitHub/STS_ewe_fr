# Entraîner les modèles (pour la démo STS Ewe↔Fr)

Voir aussi:
- `docs/technical/TECHNICAL_GUIDE.md` (architecture, API, manifests, troubleshooting)

Ce repo contient déjà les manifests nécessaires:
- ASR Ewe: `data/manifests/asr/manifest_ewe_asr.tsv`
- ASR OpenBible (audio+texte, flac): `data/manifests/asr/manifest_ewe2_audio.tsv`
- MT bitexte Ewe↔Fr: `data/manifests/mt/manifest_ewe_fr_bitext.tsv`

L’idée: entraîner (ou finetune) **au minimum** un modèle MT et un modèle STT, puis brancher un TTS FR pré-entraîné.

## 0) Pré-requis

### Matériel
- Recommandé: GPU (NVIDIA) pour finetune.
- CPU possible pour des tests, mais lent.

### Dépendances ML (optionnelles)
Ces libs ne sont pas installées par défaut car elles sont lourdes:
- `torch`
- `transformers`
- `accelerate`
- `datasets`
- `evaluate`
- `sacrebleu`
- `sentencepiece`
- `jiwer`
- `soundfile`

## Lancer tout l’entraînement d’un coup

Un orchestrateur Python est fourni:
- `ml/train_all.py` : entraîne MT (2 directions) + ASR (écrit dans `models/`)

Exemples:
```powershell
# entraînement complet "quick" (petit volume)
\.\.venv\Scripts\python.exe ml\train_all.py --quick

# reprise automatique (continue training)
\.\.venv\Scripts\python.exe ml\train_all.py --quick --resume auto
```

## 1) Entraîner le modèle de traduction (MT)

Script: `ml/mt/train_mt.py`

### A) Ewe → Français
```powershell
F:/STS/.venv/Scripts/python.exe -m pip install torch transformers accelerate evaluate sacrebleu sentencepiece

F:/STS/.venv/Scripts/python.exe ml/mt/train_mt.py `
  --manifest data/manifests/mt/manifest_ewe_fr_bitext.tsv `
  --direction ee_to_fr `
  --model facebook/nllb-200-distilled-600M `
  --out-dir models/mt_ee_to_fr `
  --max-train 200000 `
  --max-eval 5000
```

Reprise (continue training):
```powershell
F:/STS/.venv/Scripts/python.exe ml/mt/train_mt.py `
  --manifest data/manifests/mt/manifest_ewe_fr_bitext.tsv `
  --direction ee_to_fr `
  --model facebook/nllb-200-distilled-600M `
  --out-dir models/mt_ee_to_fr `
  --resume-from auto
```

### B) Français → Ewe
```powershell
F:/STS/.venv/Scripts/python.exe ml/mt/train_mt.py `
  --manifest data/manifests/mt/manifest_ewe_fr_bitext.tsv `
  --direction fr_to_ee `
  --model facebook/nllb-200-distilled-600M `
  --out-dir models/mt_fr_to_ee `
  --max-train 200000 `
  --max-eval 5000
```

## 2) Brancher le modèle MT dans le backend

Dans `backend/.env`:
```text
MT_PROVIDER=local_transformers
MT_MODEL_DIR_EE_TO_FR=models/mt_ee_to_fr
MT_MODEL_DIR_FR_TO_EE=models/mt_fr_to_ee
```

Puis lancer le backend.

## 3) STT / ASR (à faire ensuite)

Tu as 2 datasets audio+texte:
- `data/manifests/asr/manifest_ewe_asr.tsv` (mp3)
- `data/manifests/asr/manifest_ewe2_audio.tsv` (flac)
Tu peux aussi utiliser les manifests déjà rangés dans `data/manifests/asr/`.

Pour l’ASR, on peut:
- soit finetune Whisper (Transformers)
- soit wav2vec2 CTC

Script ajouté: `ml/asr/train_asr.py`

### A) Entraîner un Whisper Ewe (baseline)
```powershell
F:/STS/.venv/Scripts/python.exe -m pip install torch transformers accelerate datasets evaluate jiwer soundfile

F:/STS/.venv/Scripts/python.exe ml/asr/train_asr.py `
  --manifest data/manifests/asr/manifest_ewe2_audio.tsv `
  --model openai/whisper-small `
  --out-dir models/asr_whisper_ewe `
  --language ewe `
  --task transcribe `
  --max-train 50000 `
  --max-eval 2000
```

Reprise (continue training):
```powershell
F:/STS/.venv/Scripts/python.exe ml/asr/train_asr.py `
  --manifest data/manifests/asr/manifest_ewe2_audio.tsv `
  --model openai/whisper-small `
  --out-dir models/asr_whisper_ewe `
  --resume-from auto
```

### B) Brancher le modèle ASR dans le backend
Dans `backend/.env`:
```text
STT_PROVIDER=local_whisper
STT_MODEL_DIR=models/asr_whisper_ewe
WHISPER_LANGUAGE=ewe
WHISPER_TASK=transcribe
```

Notes:
- Selon ton environnement, `datasets` peut nécessiter `ffmpeg` pour décoder certains formats.
- Pour l’upload audio côté démo, le plus simple est d’envoyer du `.wav`.

## 4) TTS

Le plus simple pour la démo: utiliser un TTS Français pré-entraîné (Azure / Coqui / Piper).
Le backend est prêt à accueillir un provider réel.

## 5) Évaluation & exports (BLEU/chrF/TER + WER/CER)

Deux scripts d’évaluation exportent des **CSV** (prédictions) + **JSON** (métriques):

### MT
```powershell
F:/STS/.venv/Scripts/python.exe -m pip install torch transformers evaluate sacrebleu

F:/STS/.venv/Scripts/python.exe tools/eval/evaluate_mt.py `
  --manifest data/manifests/mt/manifest_ewe_fr_bitext.tsv `
  --direction ee_to_fr `
  --model-dir models/mt_ee_to_fr `
  --out-json docs/results/mt_metrics_ee_to_fr.json `
  --out-csv-prefix docs/results/mt_preds_ee_to_fr `
  --max-examples 2000
```

### ASR
```powershell
F:/STS/.venv/Scripts/python.exe -m pip install torch transformers datasets jiwer soundfile

F:/STS/.venv/Scripts/python.exe tools/eval/evaluate_asr.py `
  --manifest data/manifests/asr/manifest_ewe2_audio.tsv `
  --model-dir models/asr_whisper_ewe `
  --out-json docs/results/asr_metrics.json `
  --out-csv-prefix docs/results/asr_preds `
  --max-examples 500
```

## 6) Notebook d’analyse

Notebook prêt: `notebooks/RESULTS_ANALYSIS.ipynb` (charge les fichiers `docs/results/*.json` / `docs/results/*.csv` et fait une analyse d’erreurs + recommandations).
