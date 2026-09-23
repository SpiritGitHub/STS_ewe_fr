# Dossier données + recommandations (Projet académique STS Ewe → Français)

Date: Jan 2026

## 1) Objectif du projet (résumé)
Construire un prototype **Speech → Text → Speech** pour l’Ewe vers le Français:

1. **STT/ASR**: voix (Ewe) → texte (Ewe)
2. **MT**: texte (Ewe) → texte (Français)
3. **TTS**: texte (Français) → voix (Français)

L’objectif académique réaliste est de **démontrer un pipeline complet reproductible**, avec **mesures** (WER/CER, BLEU/chrF) et une **démo applicative**.

---

## 2) Ce que tu as dans le workspace (inventaire)

### A) Dataset ASR Ewe (audio + transcription)
**But**: entraîner/finetuner un modèle qui reconnaît la parole Ewe.

- Audio: `data/Ewe/audios/*.mp3`
- Source métadonnées: `data/Ewe/selected transcribed audios.xlsx`
- Manifest généré: `data/manifests/asr/manifest_ewe_asr.tsv`
  - Colonnes: `split, audio, text, speaker_id, locale`
- Stats (générées): `docs/stats/manifest_asr_stats.json`
  - Lignes: **19152**
  - Splits: **train 15659 / dev 1383 / test 2110**
  - Speakers: **539**
  - Vérif existence audio (échantillon 200): **0 manquant**

**Ce que ça sert**:
- STT Ewe (Speech→Text) entraînable/finetunable.
- TTS Ewe: pas garanti (ce dataset est utilisable pour TTS Ewe *si* la qualité texte est très propre et si tu veux une voix Ewe; mais ton objectif final est du Français en sortie audio).

### B) Dataset texte-only (OpenBible “ewe2”)
**But**: corpus Ewe OpenBible utile pour NLP **et** utilisable en ASR car il contient aussi de l’audio.

- Racine: `data/ewe2`
- Manifest texte-only: `data/manifests/text/manifest_ewe2_openbible.tsv`
- Manifest audio+texte: `data/manifests/asr/manifest_ewe2_audio.tsv` (paires `.flac` + `.txt`)
- Stats (générées): `docs/stats/ewe2_stats.json`
  - Fichiers: **22444**
  - Audio: **22444** fichiers `.flac` (1 audio par verset)
  - Stats audio+texte: `docs/stats/ewe2_audio_stats.json`

**Ce que ça sert**:
- Amélioration du texte (normalisation, correction, LM)
- Données de langue (Ewe) utiles pour post-traitement ASR
- **ASR additionnel** (Speech→Text) via `data/manifests/asr/manifest_ewe2_audio.tsv` (si les audios sont bien de la parole Ewe alignée)

Remarque: ce corpus est de domaine “Bible/église”, donc attention au biais de domaine.

### C) Dataset bitexte Ewe↔Fr (traduction)
**But**: entraîner/finetuner un modèle de traduction Ewe→Fr.
- Manifest: `data/manifests/mt/manifest_ewe_fr_bitext.tsv`
  - Colonnes: `split, source, ee, fr`
- Stats (générées): `docs/stats/ewe_fr_bitext_stats.json`
  - Paires: **1,039,261**
  - Splits: **train 935,329 / dev 52,211 / test 51,721**

**Ce que ça sert**:
- MT (Text→Text) entraînable/finetunable sur un volume très confortable.

### D) Glosbe (outil externe)
- Site: https://fr.glosbe.com/ee/fr

**Ce que ça sert**:
- Validation humaine, variantes lexicales, création manuelle d’un petit jeu de test.

**Note importante (académique/légale)**:
- Éviter le scraping automatique sans API/autorisation explicite.

---

## 3) Ce que tu peux faire maintenant (pipeline complet)

### Pipeline conseillé (réaliste)
- **Entrée**: audio Ewe (micro / fichier)
- **Sortie**: audio Français (TTS FR)

Étapes:
1. **ASR Ewe** entraîné/finetuné avec `data/manifests/asr/manifest_ewe_asr.tsv`
2. **MT Ewe→Fr** entraîné/finetuné avec `data/manifests/mt/manifest_ewe_fr_bitext.tsv`
3. **TTS FR**: modèle pré-entraîné (pas besoin de dataset FR dans ton workspace)

Pourquoi c’est réaliste:
- Tu as les données critiques pour ASR + MT.
- Pour TTS Français, il existe des modèles pré-entraînés (et c’est acceptable dans un projet académique si tu documentes clairement le choix).

### Ce qui manque si tu voulais “tout entraîner toi-même”
- Un dataset **TTS Français** (texte→audio FR) ou une stratégie d’adaptation.
- Mais ce n’est pas obligatoire: un TTS FR pré-entraîné suffit pour la démo STS.

---

## 4) Recommandation académique (ce que je te conseille)

### A) Cadre de projet recommandé
Pour un rendu académique solide, vise:
- **Reproductibilité**: manifests versionnés + scripts de génération + seeds fixes.
- **Évaluation**:
  - ASR: WER et/ou CER sur `dev/test`.
  - MT: chrF et BLEU (au minimum) sur `dev/test`.
  - STS end-to-end: une évaluation qualitative (ex: 20 exemples) + éventuellement une évaluation automatique (ASR du français généré, ou jugement humain).
- **Ablations simples** (très valorisant):
  - MT: base pré-entraînée vs finetune sur bitexte
  - ASR: baseline vs ajout de normalisation du texte / post-correction

### B) Baselines (bon rapport effort/valeur)
- ASR baseline: modèle pré-entraîné + finetune sur tes 19k paires.
- MT baseline: modèle pré-entraîné multilingue (ou Marian/NLLB) + finetune.
- TTS: modèle FR pré-entraîné (sortie vocale claire) + réglages de prononciation.

### C) Protocole expérimental minimal (propre)
- Split déjà défini dans les manifests (important pour éviter fuite speaker côté ASR).
- Conserver `dev` pour sélection de modèles/hyperparamètres.
- Ne toucher `test` qu’à la fin.

### D) Livrables attendus (projet académique)
- Un rapport (PDF/Markdown) qui contient:
  - description des datasets + statistiques
  - description du pipeline
  - résultats (tableaux WER/CER, BLEU/chrF)
  - limites (qualité audio, domaine “église”, biais, licences)
- Une démo (CLI ou mini webapp) qui prend un audio Ewe et rend un audio FR.

---

## 5) Comment les scripts du repo supportent ça

### Scripts existants (workspace)
- `tools/manifests/build_manifest_ewe_asr_from_excel.py` → reconstruit `data/manifests/asr/manifest_ewe_asr.tsv`
- `tools/analysis/analyze_manifest_asr.py` → stats ASR → `docs/stats/manifest_asr_stats.json`
- `tools/manifests/build_manifest_ewe2_openbible.py` → `data/manifests/text/manifest_ewe2_openbible.tsv`
- `tools/analysis/analyze_ewe2.py` → stats OpenBible → `docs/stats/ewe2_stats.json`
- `tools/manifests/build_manifest_ewe_fr_bitext.py` → `data/manifests/mt/manifest_ewe_fr_bitext.tsv` + stats

Le point clé: tout est **reproductible** et “data-driven” via manifests.

---

## 6) Prochaine étape (recommandée)

1. Ajouter une baseline MT (évaluation BLEU/chrF) sur `data/manifests/mt/manifest_ewe_fr_bitext.tsv`.
2. Ajouter une baseline ASR (WER/CER) sur `data/manifests/asr/manifest_ewe_asr.tsv`.
3. Brancher un TTS FR pré-entraîné pour obtenir la démo STS.

Si tu veux, je peux:
- générer un mini jeu de test “académique” (ex: 200 exemples STS) + un script d’évaluation automatique,
- proposer une roadmap “2 semaines” avec jalons et résultats attendus.
