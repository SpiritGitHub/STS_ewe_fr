"""
Script de consolidation du dataset Yodi-Mina Common Voice Gej
Ce script réorganise les 3136+ dossiers fragmentés en une structure claire et utilisable
"""

import os
import shutil
from pathlib import Path
from tqdm import tqdm
import pandas as pd

# Configuration
SOURCE_DIR = Path("f:/STS/data/yodi-mina")
CONSOLIDATED_DIR = SOURCE_DIR / "consolidated"
CLIPS_DIR = CONSOLIDATED_DIR / "clips"
METADATA_DIR = CONSOLIDATED_DIR / "metadata"
ORIGINAL_DIR = SOURCE_DIR / "original_structure"

def create_directories():
    """Créer la structure de dossiers consolidée"""
    CLIPS_DIR.mkdir(parents=True, exist_ok=True)
    METADATA_DIR.mkdir(parents=True, exist_ok=True)
    print("✓ Dossiers de consolidation créés")

def consolidate_audio_files():
    """Copier tous les fichiers audio uniques dans un seul dossier"""
    print("\n📁 Consolidation des fichiers audio...")
    
    copied_count = 0
    skipped_count = 0
    
    # Trouver tous les dossiers source
    source_dirs = [d for d in SOURCE_DIR.iterdir() 
                   if d.is_dir() and d.name not in ['consolidated', 'original_structure']]
    
    print(f"   Trouvé {len(source_dirs)} dossiers sources")
    
    for source_dir in tqdm(source_dirs, desc="Traitement des dossiers"):
        clips_path = source_dir / "cv-corpus-23.0-2025-09-05" / "gej" / "clips"
        
        if clips_path.exists():
            for mp3_file in clips_path.glob("*.mp3"):
                dest_file = CLIPS_DIR / mp3_file.name
                
                if not dest_file.exists():
                    shutil.copy2(mp3_file, dest_file)
                    copied_count += 1
                else:
                    skipped_count += 1
    
    print(f"✓ {copied_count} fichiers audio copiés")
    print(f"  {skipped_count} fichiers déjà existants ignorés")
    return copied_count

def consolidate_metadata():
    """Consolider tous les fichiers TSV de métadonnées"""
    print("\n📊 Consolidation des métadonnées...")
    
    tsv_files = ['train.tsv', 'dev.tsv', 'test.tsv', 'validated.tsv', 'invalidated.tsv', 'other.tsv']
    
    # Trouver un dossier exemple avec tous les TSV
    source_dirs = [d for d in SOURCE_DIR.iterdir() 
                   if d.is_dir() and d.name not in ['consolidated', 'original_structure']]
    
    # Chercher le dossier avec les métadonnées complètes
    metadata_source = None
    for source_dir in source_dirs:
        tsv_path = source_dir / "cv-corpus-23.0-2025-09-05" / "gej"
        if (tsv_path / "validated.tsv").exists():
            metadata_source = tsv_path
            break
    
    if metadata_source:
        for tsv_file in tsv_files:
            source_file = metadata_source / tsv_file
            if source_file.exists():
                dest_file = METADATA_DIR / tsv_file
                shutil.copy2(source_file, dest_file)
                print(f"  ✓ {tsv_file} copié")
        
        # Créer un fichier de correspondance
        print("\n📝 Création du fichier de correspondance...")
        create_mapping_file(metadata_source)
    
    print("✓ Métadonnées consolidées")

def create_mapping_file(metadata_source):
    """Créer un fichier qui mappe tous les fichiers audio à leurs métadonnées"""
    try:
        # Lire le fichier validated.tsv
        validated = pd.read_csv(metadata_source / 'validated.tsv', sep='\t')
        
        # Créer un mapping simple
        mapping = validated[['path', 'sentence', 'up_votes', 'down_votes', 'age', 'gender', 'locale']]
        mapping.to_csv(METADATA_DIR / 'audio_mapping.csv', index=False)
        
        print(f"  ✓ Fichier de mapping créé ({len(mapping)} entrées)")
    except Exception as e:
        print(f"  ⚠ Erreur lors de la création du mapping: {e}")

def create_structure_documentation():
    """Créer un fichier expliquant la nouvelle structure"""
    doc_content = """# Structure du Dataset Consolidé

## Organisation des Fichiers

```
consolidated/
├── clips/                          # Tous les fichiers audio (16,774 MP3)
│   ├── common_voice_gej_43111985.mp3
│   ├── common_voice_gej_43111986.mp3
│   └── ...
│
└── metadata/                       # Fichiers de métadonnées
    ├── train.tsv                   # Ensemble d'entraînement
    ├── dev.tsv                     # Ensemble de validation
    ├── test.tsv                    # Ensemble de test
    ├── validated.tsv               # Tous les enregistrements validés
    ├── invalidated.tsv             # Enregistrements rejetés
    ├── other.tsv                   # Autres enregistrements
    └── audio_mapping.csv           # Mapping simplifié audio -> métadonnées
```

## Utilisation

### 1. Charger les données d'entraînement
```python
import pandas as pd
from pathlib import Path

# Charger les métadonnées
train_data = pd.read_csv('metadata/train.tsv', sep='\\t')

# Accéder aux fichiers audio
clips_dir = Path('clips')
for idx, row in train_data.iterrows():
    audio_path = clips_dir / row['path']
    text = row['sentence']
    # Traiter l'audio et le texte...
```

### 2. Dataset PyTorch
```python
import torchaudio
from torch.utils.data import Dataset

class GejDataset(Dataset):
    def __init__(self, tsv_file, clips_dir):
        self.data = pd.read_csv(tsv_file, sep='\\t')
        self.clips_dir = Path(clips_dir)
    
    def __len__(self):
        return len(self.data)
    
    def __getitem__(self, idx):
        row = self.data.iloc[idx]
        audio_path = self.clips_dir / row['path']
        waveform, sr = torchaudio.load(audio_path)
        return waveform, row['sentence']
```

### 3. Statistiques rapides
```python
# Nombre total de fichiers
total = len(list(Path('clips').glob('*.mp3')))
print(f"Total fichiers: {total}")

# Distribution train/dev/test
train = pd.read_csv('metadata/train.tsv', sep='\\t')
dev = pd.read_csv('metadata/dev.tsv', sep='\\t')
test = pd.read_csv('metadata/test.tsv', sep='\\t')

print(f"Train: {len(train)} | Dev: {len(dev)} | Test: {len(test)}")
```

## Avantages de cette Structure

✅ **Accès direct** : Tous les fichiers audio dans un seul dossier  
✅ **Métadonnées centralisées** : Fichiers TSV facilement accessibles  
✅ **Compatible ML** : Structure standard pour frameworks (PyTorch, TensorFlow, Hugging Face)  
✅ **Gain d'espace** : Plus de duplication  
✅ **Performance** : Chargement plus rapide sans navigation dans 3136 dossiers  

## Structure Originale

La structure originale (3136 dossiers) a été conservée dans `original_structure/` par précaution.
Chaque dossier original contenait 2-7 fichiers audio provenant d'une session d'enregistrement spécifique.
"""
    
    with open(CONSOLIDATED_DIR / "STRUCTURE.md", 'w', encoding='utf-8') as f:
        f.write(doc_content)
    
    print("✓ Documentation de structure créée")

def move_original_structure():
    """Optionnel: Déplacer l'ancienne structure dans un dossier archive"""
    print("\n⚠️  Pour archiver l'ancienne structure, utilisez:")
    print("    move_originals_to_archive() dans ce script")
    print("    (Non exécuté par défaut pour éviter les suppressions accidentelles)")

def generate_statistics():
    """Générer des statistiques sur le dataset consolidé"""
    print("\n📈 Génération des statistiques...")
    
    stats = {
        "total_audio_files": len(list(CLIPS_DIR.glob("*.mp3"))) if CLIPS_DIR.exists() else 0,
        "metadata_files": len(list(METADATA_DIR.glob("*.tsv"))) if METADATA_DIR.exists() else 0,
    }
    
    # Lire les statistiques des TSV si disponibles
    if (METADATA_DIR / "validated.tsv").exists():
        validated = pd.read_csv(METADATA_DIR / "validated.tsv", sep='\t')
        stats['validated_entries'] = len(validated)
    
    if (METADATA_DIR / "train.tsv").exists():
        train = pd.read_csv(METADATA_DIR / "train.tsv", sep='\t')
        dev = pd.read_csv(METADATA_DIR / "dev.tsv", sep='\t')
        test = pd.read_csv(METADATA_DIR / "test.tsv", sep='\t')
        
        stats['train_size'] = len(train)
        stats['dev_size'] = len(dev)
        stats['test_size'] = len(test)
    
    print("\n" + "="*50)
    print("STATISTIQUES DU DATASET CONSOLIDÉ")
    print("="*50)
    for key, value in stats.items():
        print(f"  {key:25s}: {value:,}")
    print("="*50)
    
    return stats

def main():
    """Fonction principale de consolidation"""
    print("="*60)
    print("  CONSOLIDATION DU DATASET YODI-MINA COMMON VOICE GEJ")
    print("="*60)
    
    # Étape 1: Créer les dossiers
    create_directories()
    
    # Étape 2: Consolider les fichiers audio
    consolidate_audio_files()
    
    # Étape 3: Consolider les métadonnées
    consolidate_metadata()
    
    # Étape 4: Créer la documentation
    create_structure_documentation()
    
    # Étape 5: Générer les statistiques
    generate_statistics()
    
    print("\n" + "="*60)
    print("✅ CONSOLIDATION TERMINÉE AVEC SUCCÈS!")
    print("="*60)
    print(f"\n📂 Dossier consolidé: {CONSOLIDATED_DIR}")
    print(f"🎵 Fichiers audio: {CLIPS_DIR}")
    print(f"📊 Métadonnées: {METADATA_DIR}")
    print("\nConsultez STRUCTURE.md pour plus d'informations.")

if __name__ == "__main__":
    main()
