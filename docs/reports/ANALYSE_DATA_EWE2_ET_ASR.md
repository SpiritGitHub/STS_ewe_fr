# Analyse rapide des données Ewe (Jan 2026)

Ce document résume ce qui est actuellement disponible dans le workspace et ce que ça permet pour un projet **Speech → Text → Speech**.

Pour une version plus “propre” orientée projet académique (données + utilité + recommandations), voir:
- `docs/reports/DOSSIER_DONNEES_ET_RECOMMANDATIONS_PROJET_STS_EWE_FR.md`

## 1) Ce que tu as déjà

### A. Corpus ASR (audio + texte)
 Fichier: `data/manifests/asr/manifest_ewe_asr.tsv`
- Lignes: **19152**
- Splits: train **15659**, dev **1383**, test **2110**
Rapport JSON: `docs/stats/manifest_asr_stats.json`
- Speakers: **539**
- Vérif existence audio (échantillon 200): **0 manquant**
Source (reproductible): `data/Ewe/selected transcribed audios.xlsx` + `data/Ewe/audios/*.mp3`

### B. Corpus texte (Ewe2 = versets, OpenBible)
- Racine: `data/ewe2`
- Total fichiers .txt: **22444**
- Splits:
  - train: **22192** fichiers
  - dev: **186** (EZR)
  - test: **66** (COL)
- Fichiers vides / whitespace-only: **0**
- Pattern fichiers OK: `BOOK_###_Verse_###.txt` (0 anomalies)
- Longueur texte (caractères): moyenne **~123.81**, médiane **116**, max **325**
- Indice: chaque fichier contient **2 lignes** (statistiques lines = 2 partout)
- Caractères non-ASCII fréquents (échantillonnage): `ɔ ɖ ƒ ŋ ʋ ɛ ɣ …`

Rapport JSON: `docs/stats/ewe2_stats.json`

Manifest OpenBible (texte-only): `data/manifests/text/manifest_ewe2_openbible.tsv`

Audio ewe2:
- Total fichiers .flac: **22444** (1 audio par verset, ex: `EZR_010_Verse_025.flac`)
 - Manifest audio+texte (ASR-ready): `data/manifests/asr/manifest_ewe2_audio.tsv`
 - Stats audio+texte: `docs/stats/ewe2_audio_stats.json`

Corpus bitexte MT:
- Manifest: `data/manifests/mt/manifest_ewe_fr_bitext.tsv`
- Stats: `docs/stats/ewe_fr_bitext_stats.json`

Exemples:
- `F:/STS/.venv/Scripts/python.exe tools/analysis/analyze_manifest_asr.py --manifest data/manifests/asr/manifest_ewe_asr.tsv --check-audio 200 --out-json docs/stats/manifest_asr_stats.json`
- `F:/STS/.venv/Scripts/python.exe tools/analysis/analyze_ewe2.py --root data/ewe2 --out-json docs/stats/ewe2_stats.json`
## 2) Est-ce que ça suffit pour “Speech → Text → Speech” ?

### Oui, partiellement
Tu peux déjà faire:
- **ASR (Speech → Text)**: entraînement/finetune sur tes 19k paires audio+texte.
- **TTS (Text → Speech)**: *si* tu as (ou peux obtenir) des paires texte→audio (mêmes speakers) ou un modèle TTS multi-speaker pré-entraîné à adapter.

Avec le bitexte Ewe↔Fr en plus, tu peux maintenant faire:
- **MT (Text → Text)**: entraînement/finetune d’un modèle Ewe→Fr (ou utilisation d’un modèle pré-entraîné + adaptation).

### Le point bloquant pour un vrai “Text → Speech” end-to-end
Aujourd’hui, le dataset TTS n’est pas “aligné”:
- `manifest_ewe_asr.tsv` = audio + texte (bon pour ASR)
- `ewe2` (OpenBible) = texte seulement (pas d’audio associé)

Donc **ewe2 ne suffit pas à lui seul** pour du TTS supervisé (texte->waveform). Par contre, ewe2 est **très utile** pour:
- enrichir la langue côté texte (LM / post-correction / normalisation)
- data augmentation textuelle
- entraîner un correcteur ou un reranker

## 3) Stratégies réalistes pour faire Speech→Text→Speech avec ce que tu as

### Option A (pragmatique, marche vite)
1. Entraîner/finetune un modèle **ASR** sur ton manifest.
2. Utiliser un **TTS pré-entraîné** (multi-lingue) et tester le rendu Ewe.
3. Optionnel: adapter le TTS avec un sous-ensemble audio+texte (même si initialement “ASR”).
   - Attention: la qualité TTS dépend fortement de la propreté des textes, ponctuation, et stabilité speaker.

### Option B (plus propre)
- Construire un vrai dataset TTS:
  - soit enregistrer des lectures de `ewe2` (ou d’une partie)
  - soit aligner automatiquement si tu trouves/produis l’audio correspondant (souvent difficile)

### Option C (pipeline hybride)
- Utiliser `ewe2` pour **améliorer l’ASR** via un modèle de langage / correction orthographique, puis brancher un TTS générique.

### À propos de Glosbe
Le site https://fr.glosbe.com/ee/fr est très utile pour:
- vérifier des traductions, trouver des variantes lexicales
- faire de la curation manuelle (petits jeux de test)

Par contre, je ne recommande pas de le *scraper* automatiquement sans API/autorisation explicite (risque de violer les Conditions d’utilisation).

## 4) Scripts ajoutés (reproductibles)
- `tools/analysis/analyze_manifest_asr.py`
  - Exemple: `F:/STS/.venv/Scripts/python.exe tools/analysis/analyze_manifest_asr.py --manifest data/manifests/asr/manifest_ewe_asr.tsv --check-audio 200 --out-json docs/stats/manifest_asr_stats.json`
- `tools/analysis/analyze_ewe2.py`
  - Exemple: `F:/STS/.venv/Scripts/python.exe tools/analysis/analyze_ewe2.py --root data/ewe2 --out-json docs/stats/ewe2_stats.json`

Si tu veux, je peux ensuite:
- générer un **manifest TTS** à partir de tes audios (si le texte est “spoken-style” propre)
- proposer un **plan modèle** (ASR + TTS) et la structure `backend`/`frontend` pour la démo.
