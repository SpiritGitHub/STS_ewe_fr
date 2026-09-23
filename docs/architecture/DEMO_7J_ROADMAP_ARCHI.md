# Roadmap Démo (7 jours) + Architecture – Interprète FR↔Ewe (Voix ↔ Texte ↔ Voix)

Date: 2026-01-17

## Objectif démo (ce que le public voit)
Tu lances l’interface, tu choisis un mode:
- **Mode 1 – FR → Ewe**: tu parles en français → l’app affiche le **texte FR** reconnu → affiche la **traduction Ewe** (et **optionnellement** la lit à voix haute).
- **Mode 2 – Ewe → FR**: tu parles en ewe → l’app affiche le **texte Ewe** reconnu → affiche la **traduction FR** (et peut la lire à voix haute).

> Priorité démo (7 jours): **qualité + stabilité + latence**, pas entraînement long.
> Stratégie: modèles pré-entraînés (Whisper pour STT, NLLB/équivalent pour MT, TTS prêt pour FR). Le TTS Ewe est un bonus.

---

## Périmètre V1 (démo 7 jours)
### Fonctionnel (must-have)
- Enregistrement **push-to-talk** (appuyer pour parler, relâcher pour lancer le traitement)
- Affichage en temps réel:
  - texte source reconnu (FR ou Ewe)
  - texte traduit (Ewe ou FR)
  - statut / latence / erreurs
- Bouton “Rejouer” (rejouer l’audio enregistré)

### Audio (nice-to-have)
- TTS **Français**: oui (facile et fiable)
- TTS **Ewe**: optionnel (à activer seulement si tu trouves un moteur/voix acceptable)

### Plan B de démo (obligatoire)
- 5–10 clips audio **pré-enregistrés** (FR et Ewe) dans l’interface.
- Si le micro live échoue: tu cliques un clip → la pipeline tourne quand même.

---

## Roadmap jour par jour (7 jours)

### Jour 1 – Cadrage + UX démo
- Écrire le script de démo (2–3 minutes) + 10 phrases “safe” (phrases courtes, vocabulaire simple).
- Choisir le format UI:
  - **Streamlit** (recommandé) pour aller vite.
- Décider un mode de fonctionnement:
  - **non-streaming** (push-to-talk) pour éviter les bugs en live.

Livrable: script de démo + wireframe UI.

### Jour 2 – Pipeline technique minimal (texte)
- Implémenter un backend (FastAPI) avec:
  - STT via Whisper (FR/Ewe)
  - Traduction via un modèle multilingue (ex: NLLB)
- Tester en “texte uniquement” (sans micro) avec un fichier audio.

Livrable: endpoint `/pipeline` qui renvoie JSON (source_text + translated_text).

### Jour 3 – Interface démo
- UI Streamlit:
  - 2 boutons: “Parler FR” / “Parler Ewe”
  - affichage des textes
  - affichage de la latence
- Ajouter le mode “upload un audio” (wav/mp3) pour le plan B.

Livrable: UI fonctionnelle avec au moins 1 chemin complet.

### Jour 4 – Stabilisation (les vrais trucs qui sauvent une démo)
- VAD/segmentation simple (ou durée max 15s) pour éviter les longs enregistrements.
- Gestion d’erreurs:
  - timeouts
  - message user-friendly si STT/MT échoue
- Logging minimal (garder les inputs/outputs du run de démo).

Livrable: démo stable sans crash sur 20 essais.

### Jour 5 – Ajout TTS (voix)
- TTS Français (lecture du texte FR traduit) via un moteur existant.
- Ajouter un bouton “Lire la traduction”.

Livrable: FR→(texte) + lecture FR OK.

### Jour 6 – Qualité perçue (spécial présentation)
- Améliorer “la perception”:
  - normalisation texte (ponctuation, espaces)
  - glossaire mini (termes clés: « reconnaissance vocale », « traduction », etc.)
  - limiter les phrases à 1–2 phrases max
- Préparer les clips audio pré-enregistrés.

Livrable: démo “propre” sur ton script.

### Jour 7 – Répétition générale + plan de secours
- Répéter 5 fois sur la machine de présentation.
- Vérifier micro, latence, audio.
- Prévoir:
  - mode offline si possible
  - sinon hotspot internet stable

Livrable: démonstration répétable + plan B activable en 1 clic.

---

## Architecture projet (simple et efficace)

### Structure de dossiers (proposée)
- `backend/` : API FastAPI (STT, traduction, TTS)
- `frontend/` : UI Streamlit (démo)
- `data/` : datasets + manifest + audios de démo
- `models/` : modèles téléchargés/cache (à ignorer Git si besoin)
- `tools/` : scripts utilitaires (préparation, checks, évaluation, etc.)
- `docs/` : notes, roadmap, script de présentation

### Dataflow (pipeline)
1) UI enregistre audio (FR/Ewe)
2) Backend STT → texte source
3) Backend MT → texte cible
4) (Option) Backend TTS → audio cible
5) UI affiche textes + joue l’audio

### API minimale
- `POST /pipeline`
  - input: audio + `direction` (`fr_to_ewe` ou `ewe_to_fr`)
  - output: `{ source_text, target_text, timings, (optional) target_audio_url }`
- `GET /health`
  - sanity check

---

## Risques (et comment les neutraliser en 7 jours)
- **FR→Ewe**: la traduction peut être moyenne selon modèles disponibles → phrases simples + glossaire + plan B (clips).
- **Ewe STT**: la qualité peut varier → limiter la durée + parler clairement + plan B (clips).
- **Latence**: modèles lourds → limiter audio, préparer cache, éviter streaming.
- **Internet** (si modèle cloud) → privilégier local/offline ou hotspot.

---

## Après la démo (si tu veux améliorer)
- Fine-tuner STT Ewe avec [data/manifests/asr/manifest_ewe_asr.tsv](../data/manifests/asr/manifest_ewe_asr.tsv)
- Trouver corpus parallèle Ewe–Fr pour fine-tune MT (ou post-édition)
- Ajouter TTS Ewe (plus long)
