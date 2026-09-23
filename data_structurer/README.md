# Dataset Yodi-Mina - Common Voice Gej

> 🎙️ **16,774 enregistrements audio** en langue Gej pour l'entraînement de modèles ASR, TTS et MT

## 📋 Description Générale

Ce dataset contient des enregistrements audio en langue **Gej** (une langue africaine), provenant du projet **Mozilla Common Voice** (version 23.0, datée du 5 septembre 2025).

### Informations Clés
- **Langue** : Gej (code ISO: `gej`)
- **Source** : Mozilla Common Voice
- **Version** : cv-corpus-23.0-2025-09-05
- **Nombre total de fichiers audio** : 16,774 fichiers MP3
- **Structure** : Consolidée et prête à l'emploi

## 🚀 Démarrage Rapide

### Structure du Dataset

```
yodi-mina/
├── consolidated/              ← UTILISEZ CE DOSSIER
│   ├── clips/                 # 16,774 fichiers audio MP3
│   └── metadata/              # Fichiers TSV de métadonnées
│       ├── train.tsv          (1,282 échantillons)
│       ├── dev.tsv            (954 échantillons)
│       ├── test.tsv           (952 échantillons)
│       ├── validated.tsv      (16,406 validés)
│       ├── invalidated.tsv    (332 invalides)
│       ├── other.tsv          (36 autres)
│       └── audio_mapping.csv  (mapping simplifié)
│
├── README.md                  # Ce fichier
├── GUIDE_UTILISATION.md       # Guide pratique avec exemples
└── consolidate_dataset.py     # Script de consolidation (déjà exécuté)
```

### Chargement Rapide

```python
import pandas as pd
from pathlib import Path

# Charger les métadonnées
train_df = pd.read_csv('consolidated/metadata/train.tsv', sep='\t')

# Accéder aux fichiers audio
clips_dir = Path('consolidated/clips')
audio_path = clips_dir / train_df.iloc[0]['path']
```

**📘 Pour plus d'exemples, consultez [GUIDE_UTILISATION.md](GUIDE_UTILISATION.md)**

## 🗂️ Structure des Données

### Fichiers Audio
- **Emplacement** : `consolidated/clips/`
- **Format** : MP3
- **Nomenclature** : `common_voice_gej_XXXXXXXX.mp3`
- **Total** : 16,774 fichiers audio

### Fichiers de Métadonnées (TSV)

Tous les fichiers TSV sont dans `consolidated/metadata/` :

| Fichier | Entrées | Description |
|---------|---------|-------------|
| `train.tsv` | 1,282 | Ensemble d'entraînement |
| `dev.tsv` | 954 | Ensemble de validation |
| `test.tsv` | 952 | Ensemble de test |
| `validated.tsv` | 16,406 | Tous les enregistrements validés |
| `invalidated.tsv` | 332 | Enregistrements rejetés |
| `other.tsv` | 36 | Autres enregistrements |
| `audio_mapping.csv` | 16,406 | Mapping simplifié (CSV) |

### Colonnes des fichiers TSV

| Colonne | Description |
|---------|-------------|
| `client_id` | Identifiant anonymisé du contributeur (hash SHA-256) |
| `path` | Nom du fichier audio MP3 correspondant |
| `sentence_id` | Identifiant unique de la phrase (hash SHA-256) |
| `sentence` | Texte transcrit en langue Gej |
| `sentence_domain` | Domaine thématique de la phrase |
| `up_votes` | Nombre de votes positifs (validation) |
| `down_votes` | Nombre de votes négatifs (rejet) |
| `age` | Tranche d'âge du locuteur |
| `gender` | Genre du locuteur |
| `accents` | Accent régional |
| `variant` | Variante dialectale |
| `locale` | Code de langue (toujours `gej`) |
| `segment` | Segment du dataset (train/dev/test) |

### Exemple de données

```tsv
sentence: "Ana gble."
up_votes: 2
down_votes: 1
path: common_voice_gej_43119839.mp3
```

## 🎯 Utilisations Possibles

### 1. **Reconnaissance Vocale Automatique (ASR)**
- Entraîner des modèles Speech-to-Text pour la langue Gej
- Créer des systèmes de transcription automatique
- Développer des assistants vocaux en langue locale

### 2. **Recherche Linguistique**
- Étudier la phonétique et la phonologie de la langue Gej
- Analyser les variations dialectales
- Documenter une langue peu dotée numériquement

### 3. **Synthèse Vocale (TTS)**
- Développer des voix synthétiques en Gej
- Créer des outils de lecture audio pour le contenu en Gej
- Applications d'accessibilité

### 4. **Traduction Automatique**
- Composante audio pour systèmes de traduction parlée
- Speech-to-Speech translation (Gej vers autres langues)
- Sous-titrage automatique

### 5. **Applications Éducatives**
- Outils d'apprentissage de la langue Gej
- Applications de prononciation
- Préservation du patrimoine linguistique

### 6. **Accessibilité**
- Commandes vocales pour applications mobiles
- Interface vocale pour personnes analphabètes
- Outils pour personnes malvoyantes

## 📊 Statistiques

| Métrique | Valeur |
|----------|--------|
| **Fichiers audio total** | 16,774 MP3 |
| **Enregistrements validés** | 16,406 (98.0%) |
| **Enregistrements invalidés** | 332 (2.0%) |
| **Ensemble d'entraînement** | 1,282 (7.6%) |
| **Ensemble de validation** | 954 (5.7%) |
| **Ensemble de test** | 952 (5.7%) |
| **Taux de validation** | 98.0% |

## 🔧 Utilisation avec les Frameworks ML

### � Utilisation

### Chargement Simple avec Pandas

```python
import pandas as pd
from pathlib import Path

# Charger les données d'entraînement
train_df = pd.read_csv('consolidated/metadata/train.tsv', sep='\t')

# Accéder à un fichier audio
clips_dir = Path('consolidated/clips')
first_audio = clips_dir / train_df.iloc[0]['path']
print(f"Audio: {first_audio}")
print(f"Texte: {train_df.iloc[0]['sentence']}")
```

### Dataset PyTorch

```python
import torchaudio
import pandas as pd
from torch.utils.data import Dataset

class GejDataset(Dataset):
    def __init__(self, tsv_file, clips_dir):
        self.data = pd.read_csv(tsv_file, sep='\t')
        self.clips_dir = Path(clips_dir)
    
    def __len__(self):
        return len(self.data)
    
    def __getitem__(self, idx):
        row = self.data.iloc[idx]
        audio_path = self.clips_dir / row['path']
- **Qualité** : Enregistrements de contributeurs volontaires avec différents équipements
- **Validation** : 98% des enregistrements validés par la communauté
- **Licence** : CC-0 (Common Voice - domaine public)
- **Sample Rate** : Les fichiers sont généralement à 48kHz, rééchantillonnez à 16kHz pour l'ASR
- **Encodage** : UTF-8 pour tous les fichiers TSV

## 🆘 Support et Documentation

- **Guide pratique** : [GUIDE_UTILISATION.md](GUIDE_UTILISATION.md)
- **Common Voice** : [commonvoice.mozilla.org](https://commonvoice.mozilla.org/)
- **Script de consolidation** : `consolidate_dataset.py` (déjà exécuté)

## 📅 Informations

- **Dataset** : Mozilla Common Voice v23.0
- **Date de consolidation** : 21 janvier 2026
- **Status** : ✅ Prêt à l'emploim/)

## 📞 Provenance des Données

Les noms de dossiers au format "15057161776 15057156734" suggèrent que ces données proviennent de sessions WhatsApp ou d'identifiants de téléphones utilisés lors de la collecte des enregistrements vocaux.

---

**Date de création du README** : 21 janvier 2026  
**Version du dataset** : Common Voice 23.0 (2025-09-05)
