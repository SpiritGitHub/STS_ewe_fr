# Guide d'Utilisation - Dataset Yodi-Mina Common Voice Gej

> 🎙️ **16,774 enregistrements audio** en langue Gej | **98% validés** | **Prêt pour l'entraînement**

## 📂 Structure du Dataset

```
yodi-mina/
├── consolidated/
│   ├── clips/                 # 16,774 fichiers MP3
│   └── metadata/
│       ├── train.tsv          # 1,282 échantillons
│       ├── dev.tsv            # 954 échantillons
│       ├── test.tsv           # 952 échantillons
│       ├── validated.tsv      # 16,406 validés
│       ├── invalidated.tsv    # 332 invalides
│       ├── other.tsv          # 36 autres
│       └── audio_mapping.csv  # Mapping simplifié
│
├── README.md                  # Documentation complète
└── GUIDE_UTILISATION.md       # Ce fichier
```

## 🚀 Démarrage Rapide

## 📊 Accès Rapide aux Données

### Option 1 : Pandas (Recommandé pour débuter)

```python
import pandas as pd
from pathlib import Path

# Définir les chemins
clips_dir = Path("consolidated/clips")
metadata_dir = Path("consolidated/metadata")

# Charger le fichier d'entraînement
train_df = pd.read_csv(metadata_dir / "train.tsv", sep='\t')

# Aperçu des données
print(train_df.head())
print(f"\nNombre d'échantillons: {len(train_df)}")

# Accéder à un fichier audio
first_audio = train_df.iloc[0]['path']
audio_path = clips_dir / first_audio
print(f"Chemin audio: {audio_path}")
```

### Option 2 : Chargement avec LibROSA

```python
import librosa
import pandas as pd

# Charger les métadonnées
train_df = pd.read_csv("consolidated/metadata/train.tsv", sep='\t')

# Charger un fichier audio
audio_file = f"consolidated/clips/{train_df.iloc[0]['path']}"
waveform, sample_rate = librosa.load(audio_file, sr=16000)

print(f"Sample rate: {sample_rate}")
print(f"Durée: {len(waveform)/sample_rate:.2f}s")
print(f"Transcription: {train_df.iloc[0]['sentence']}")
```

### Option 3 : Dataset PyTorch

```python
import torch
from torch.utils.data import Dataset, DataLoader
import torchaudio
import pandas as pd
from pathlib import Path

class GejVoiceDataset(Dataset):
    def __init__(self, tsv_file, clips_dir, sample_rate=16000):
        self.data = pd.read_csv(tsv_file, sep='\t')
        self.clips_dir = Path(clips_dir)
        self.sample_rate = sample_rate
    
    def __len__(self):
        return len(self.data)
    
    def __getitem__(self, idx):
        row = self.data.iloc[idx]
        audio_path = self.clips_dir / row['path']
        
        # Charger l'audio
        waveform, sr = torchaudio.load(audio_path)
        
        # Resampler si nécessaire
        if sr != self.sample_rate:
            resampler = torchaudio.transforms.Resample(sr, self.sample_rate)
            waveform = resampler(waveform)
        
        return {
            'waveform': waveform,
            'text': row['sentence'],
            'sample_rate': self.sample_rate
        }

# Utilisation
train_dataset = GejVoiceDataset(
    'consolidated/metadata/train.tsv',
    'consolidated/clips'
)

train_loader = DataLoader(train_dataset, batch_size=4, shuffle=True)

# Test
sample = train_dataset[0]
print(f"Waveform shape: {sample['waveform'].shape}")
print(f"Text: {sample['text']}")
```

## 🎯 Cas d'Usage Courants

### 1. Entraîner un modèle ASR avec Hugging Face

```python
from datasets import Dataset, Audio
import pandas as pd

# Charger les données
train_df = pd.read_csv("consolidated/metadata/train.tsv", sep='\t')
train_df['audio'] = train_df['path'].apply(lambda x: f"consolidated/clips/{x}")

# Créer un dataset Hugging Face
dataset = Dataset.from_pandas(train_df[['audio', 'sentence']])
dataset = dataset.cast_column('audio', Audio(sampling_rate=16000))

# Utiliser avec un modèle Wav2Vec2 ou Whisper
from transformers import Wav2Vec2Processor, Wav2Vec2ForCTC

processor = Wav2Vec2Processor.from_pretrained("facebook/wav2vec2-base")
# ... fine-tuning
```

### 2. Analyse Exploratoire

```python
import pandas as pd
import matplotlib.pyplot as plt

# Charger toutes les données validées
validated = pd.read_csv("consolidated/metadata/validated.tsv", sep='\t')

# Statistiques de base
print("=== STATISTIQUES ===")
print(f"Total d'enregistrements: {len(validated)}")
print(f"\nRépartition des votes:")
print(validated[['up_votes', 'down_votes']].describe())

# Distribution des genres
if 'gender' in validated.columns:
    print(f"\nDistribution par genre:")
    print(validated['gender'].value_counts())

# Longueur des phrases
validated['sentence_length'] = validated['sentence'].str.len()
print(f"\nLongueur des phrases:")
print(validated['sentence_length'].describe())

# Visualisation
plt.figure(figsize=(10, 4))
plt.hist(validated['sentence_length'], bins=50)
plt.xlabel('Longueur de la phrase (caractères)')
plt.ylabel('Nombre d\'enregistrements')
plt.title('Distribution de la longueur des phrases')
plt.savefig('sentence_length_distribution.png')
```Vérification d'Intégrité

```python
from pathlib import Path
import pandas as pd

clips_dir = Path("consolidated/clips")
validated = pd.read_csv("consolidated/metadata/validated.tsv", sep='\t')

# Vérifier l'existence des fichiers
missing = [f for f in validated['path'] if not (clips_dir / f).exists()]
print(f"✓ Fichiers trouvés: {len(validated) - len(missing)}/{len(validated)}")
if missing:
    print(f"⚠ Fichiers manquants: {len(missing)}")
else:
    print("✅ Tous les fichiers audio sont présents!")
```

---

## 📈 Entraînement de Modèles

## 📈 Exemples d'Entraînement

### Fine-tuning Whisper (OpenAI)

```python
from transformers import WhisperProcessor, WhisperForConditionalGeneration
from datasets import Dataset, Audio
import pandas as pd

# Préparer les données
train_df = pd.read_csv("consolidated/metadata/train.tsv", sep='\t')
train_df['audio'] = train_df['path'].apply(lambda x: f"consolidated/clips/{x}")

dataset = Dataset.from_pandas(train_df[['audio', 'sentence']])
dataset = dataset.cast_column('audio', Audio(sampling_rate=16000))

# Charger Whisper
processor = WhisperProcessor.from_pretrained("openai/whisper-small")
model = WhisperForConditionalGeneration.from_pretrained("openai/whisper-small")

# Preprocessing
def prepare_dataset(batch):
    audio = batch["audio"]
    batch["input_features"] = processor(
        audio["array"], 
        sampling_rate=audio["sampling_rate"]
    ).input_features[0]
    batch["labels"] = processor.tokenizer(batch["sentence"]).input_ids
    return batch

dataset = dataset.map(prepare_dataset, remove_columns=dataset.column_names)

# Training...
```

### Entraînement Wav2Vec2

```python
from transformers import Wav2Vec2CTCTokenizer, Wav2Vec2Processor, Wav2Vec2ForCTC
from transformers import TrainingArguments, Trainer
import pandas as pd

# Créer un tokenizer pour la langue Gej
# ... (voir documentation Hugging Face pour les détails)

# Configuration de l'entraînement
training_args = TrainingArguments(
    output_dir="./wav2vec2-gej",
    per_device_train_batch_size=8,
    per_device_eval_batch_size=8,
    num_train_epochs=30,
    save_steps=500,
    eval_steps=500,
    logging_steps=100,
    learning_rate=3e-4,
    warmup_steps=500,
    save_total_limit=2,
)
```

## 🔧 Utilitaires

### Script de comptage rapide

```bash
# Compter les fichiers audio
ls consolidated/clips/*.mp3 | wc -l

# Voir les premiers fichiers
ls consolidated/clips | head -10
 et Scripts

### Comptage Rapide

```powershell
# Compter les fichiers audio
(Get-ChildItem consolidated/clips/*.mp3).Count

# Taille du dataset
(Get-ChildItem consolidated -Recurse | Measure-Object -Property Length -Sum).Sum / 1GB
```

### Vérification des Fichiers Audio

```python
from pathlib import Path

def check_audio_integrity(clips_dir):
    """Vérifier que tous les MP3 sont valides"""
    clips_dir = Path(clips_dir)
    valid = 0
    invalid = []
    
    for mp3 in clips_dir.glob("*.mp3"):
        try:
            if mp3.stat().st_size > 0:
                valid += 1
            else:
                invalid.append(mp3.name)
        except Exception as e:
            invalid.append(f"{mp3.name}: {e}")
    
    print(f"✓ Fichiers valides: {valid}")
    if invalid:
        print(f"⚠ Fichiers invalides: {len(invalid)}")
    return valid, invalid

# Exécuter
check_audio_integrity("consolidated/clips")
```

---

## 🆘 Résolution de Problèmes

### Erreur "File not found"
```python
from pathlib import Path
print(Path.cwd())  # Vérifier le répertoire actuel
```

### Erreur de lecture TSV
```python
# Spécifier l'encodage UTF-8
df = pd.read_csv("consolidated/metadata/train.tsv", sep='\t', encoding='utf-8')
```

### Audio corrompu
```python
import torchaudio

try:
    waveform, sr = torchaudio.load(audio_path)
except Exception as e:
    print(f"Erreur: {e}")
    # Gérer l'erreur (skip, log, etc.)
```

---

## 📝 Notes Importantes

1. **Chemins relatifs** : Les exemples supposent que vous êtes dans `yodi-mina/`
2. **Sample rate** : Rééchantillonnez à 16kHz pour l'ASR
3. **Encodage** : UTF-8 pour tous les fichiers TSV
4. **Mémoire** : Le chargement complet nécessite >8GB RAM

---

**📘 Pour plus d'informations, consultez [README.md](README.md)**