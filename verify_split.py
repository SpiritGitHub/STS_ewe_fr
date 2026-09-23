"""
Script de vérification pour s'assurer que toutes les lignes ont été couvertes
"""
import pandas as pd
from pathlib import Path

# Lire le fichier original
print("Vérification de la division...")
print("=" * 60)

df_original = pd.read_excel("Mina.xlsx")
total_original = len(df_original)
print(f"Fichier original (Mina.xlsx): {total_original} lignes")
print()

# Compter les lignes dans tous les fichiers CSV
splits_dir = Path("mina_translation_splits")
csv_files = sorted(splits_dir.glob("mina_part_*.csv"))

total_splits = 0
print(f"Fichiers CSV trouvés: {len(csv_files)}")
print()

# Vérifier chaque fichier
for csv_file in csv_files:
    df_split = pd.read_csv(csv_file)
    num_lines = len(df_split)
    total_splits += num_lines
    print(f"{csv_file.name}: {num_lines} lignes")

print()
print("=" * 60)
print(f"TOTAL ORIGINAL:  {total_original} lignes")
print(f"TOTAL DISTRIBUÉ: {total_splits} lignes")
print()

if total_original == total_splits:
    print("✓ VÉRIFICATION RÉUSSIE! Toutes les lignes sont couvertes.")
else:
    difference = total_original - total_splits
    print(f"❌ ATTENTION! Différence de {difference} lignes!")
    
print("=" * 60)
