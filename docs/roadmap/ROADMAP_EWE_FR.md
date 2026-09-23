# Roadmap – Application Ewe → Français (Voix → Texte → Traduction → Voix)

Date: 2026-01-17

## Démo (7 jours) orientée présentation
Pour un objectif “interprète live” (FR↔Ewe) avec interface, voir:
- [DEMO_7J_ROADMAP_ARCHI.md](../architecture/DEMO_7J_ROADMAP_ARCHI.md)

## Objectif
Construire une application capable de :
1) convertir la parole en Ewe en texte (STT),
2) traduire ce texte Ewe en français (MT),
3) restituer la traduction en audio français (TTS),
4) (bonus) gérer aussi Français → Ewe.

> Contrainte: pas de collecte terrain et peu/pas de données Ewe disponibles.
> Stratégie recommandée: **V1 = prototype avec modèles pré-entraînés (zéro/few-shot)**, puis **V2 = amélioration via données ouvertes** (ex: BibleTTS) si besoin.

---

## V1 (rapide, sans collecte terrain) – 1 à 2 semaines
Objectif: une démo fonctionnelle end-to-end.

### 1) STT Ewe (Speech-to-Text)
- Utiliser un modèle pré-entraîné robuste (zéro-shot) :
  - **OpenAI Whisper** (via implémentations open-source) est souvent le plus simple pour démarrer.
- Pré-traitement minimal:
  - normalisation audio (16 kHz, mono),
  - découpage en segments (VAD) si l’audio est long.
- Sortie: texte Ewe brut.

### 2) Traduction Ewe → Français
- Utiliser un modèle multilingue prêt à l’emploi:
  - **NLLB** (No Language Left Behind) est un bon candidat.
- Important:
  - conserver un mode “texte seulement” pour debug (voir STT et MT séparément).

### 3) TTS Français
- Utiliser un TTS français existant (pas d’entraînement requis), ex:
  - Piper / Coqui TTS / ou un service cloud si autorisé.

### 4) API et pipeline
- Backend: **FastAPI** (Python).
- Endpoints recommandés:
  - `/transcribe` (audio → texte ewe)
  - `/translate` (texte ewe → texte fr)
  - `/speak` (texte fr → audio)
  - `/pipeline` (audio ewe → {texte ewe, texte fr, audio fr})

### 5) Interface (démo)
- Web simple (ou Streamlit pour gagner du temps):
  - bouton enregistrer → affiche transcription → affiche traduction → bouton écouter.

**Livrables V1**
- Démo utilisable + pipeline complet.
- Mesures minimales: latence moyenne et exemples d’erreurs typiques.

---

## V2 (amélioration sans terrain) – 2 à 6 semaines
Objectif: augmenter la qualité STT et préparer le bonus.

### 6) Données “open” sans collecte terrain
Même si tu n’as pas le temps de collecter, tu peux exploiter des ressources ouvertes.

#### A) Audio + texte (très utile pour STT/TTS)
1) **BibleTTS (OpenSLR SLR129)** – inclut **Ewe**
- Licence: **CC BY-SA 4.0**
- Contenu: jusqu’à ~80h (selon langue), **studio 48 kHz**, versets alignés (speech + transcripts), splits train/dev/test.
- Langues alignées (inclut Ewe) mentionnées sur la page.
- Lien: https://openslr.org/129/
- Fichier Ewe: sur la page, télécharger l’archive **ewe.tgz** (si listée; la page indique explicitement Ewe dans les langues alignées).

> Note: c’est généralement **1 seul locuteur** et domaine “Bible”: excellent pour démarrer, mais généralisation limitée pour parole spontanée multi-locuteurs.

2) (Optionnel) **Nicolingua radio / VA** (OpenSLR SLR105/SLR106)
- Utile pour pré-entraînement/robustesse… mais pas Ewe (plutôt Guinée: Susu, Pular, Maninka, etc.).
- Liens: https://openslr.org/105/ et https://openslr.org/106/

#### B) Texte parallèle / benchmarks traduction (utile pour MT)
1) **FLORES-200 / NLLB-Seed (texte)**
- Sert de **benchmark** et petit corpus parallèle.
- FLORES-200: CC BY-SA 4.0 (référence HuggingFace/GitHub).
- Lien dataset card: https://huggingface.co/datasets/facebook/flores
- Repo (archivé) avec détails licences: https://github.com/facebookresearch/flores

2) **OPUS (texte parallèle)**
- Très bon agrégateur de corpus parallèles.
- À vérifier si Ewe↔Fr existe: https://opus.nlpl.eu/
  - (Si le site est instable, essayer plus tard ou via miroirs.)

#### C) Common Voice (audio + texte, si Ewe disponible)
- Common Voice se télécharge via Mozilla Data Collective:
  - https://datacollective.mozillafoundation.org/datasets?q=common+voice
- Il faut vérifier si la locale Ewe est présente (ex: `ee`).

### 7) Fine-tuning STT (si nécessaire)
- Si V1 est trop bruitée:
  - fine-tuner Whisper/XLS-R sur BibleTTS Ewe (d’abord pour “lecture”)
  - ajouter augmentation (bruit, reverb) pour simuler terrain
- Évaluer: WER/CER sur dev/test.

### 8) Fine-tuning MT Ewe→Fr (si nécessaire)
- Si tu trouves du parallèle Ewe-Fr (OPUS ou autre):
  - fine-tune NLLB/mBART sur le corpus.
- Sinon:
  - garder NLLB en inference-only + post-édition légère (règles, glossaire).

---

## V3 (bonus) – Français → Ewe (selon temps)
### 9) MT inverse (Fr→Ewe)
- Utiliser le même modèle multilingue si support (NLLB) ou fine-tune.

### 10) TTS Ewe (optionnel)
- BibleTTS inclut des données Ewe: peut servir à entraîner un TTS Ewe.
- Priorité: d’abord texte Fr→Ewe, puis ajouter la voix si nécessaire.

---

## Conseils pragmatiques (vu la contrainte “pas de terrain”)
- **Démarre par V1** (zéro collecte) pour avoir une démo présentable rapidement.
- **Ensuite seulement**: améliore STT avec BibleTTS Ewe (OpenSLR 129).
- Documente toujours:
  - licences (CC BY-SA vs CC0),
  - domaine des données (Bible ≠ conversation),
  - limites et biais.

---

## Checklist rapide (à cocher)
- [ ] Démo V1 STT→MT→TTS fonctionne localement
- [ ] API `/pipeline` OK
- [ ] UI minimale OK
- [ ] Ajout BibleTTS Ewe pour améliorer STT/TTS (si besoin)
- [ ] Évaluation WER/CER + quelques exemples
- [ ] Bonus Fr→Ewe (texte)

