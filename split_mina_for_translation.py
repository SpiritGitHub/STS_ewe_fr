"""
Script pour diviser le fichier Mina.xlsx en 100 fichiers pour traduction
"""
import pandas as pd
import os
from pathlib import Path

def split_excel_for_translation(input_file, num_files=100, output_dir="mina_translation_splits"):
    """
    Divise un fichier Excel en plusieurs fichiers CSV pour faciliter la traduction
    
    Args:
        input_file: Chemin vers le fichier Excel
        num_files: Nombre de fichiers de sortie (défaut: 100)
        output_dir: Dossier de sortie
    """
    # Créer le dossier de sortie
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # Lire le fichier Excel
    print(f"Lecture du fichier {input_file}...")
    df = pd.read_excel(input_file)
    
    total_rows = len(df)
    print(f"Total de lignes: {total_rows}")
    
    # Calculer le nombre de lignes par fichier
    rows_per_file = total_rows // num_files
    remainder = total_rows % num_files
    
    print(f"Nombre de lignes par fichier: ~{rows_per_file}")
    
    # Diviser et sauvegarder
    start_idx = 0
    for i in range(num_files):
        # Ajouter une ligne supplémentaire aux premiers fichiers si nécessaire
        end_idx = start_idx + rows_per_file + (1 if i < remainder else 0)
        
        # Extraire la portion
        df_split = df.iloc[start_idx:end_idx].copy()
        
        # Ajouter une colonne pour la traduction si elle n'existe pas
        if 'traduction' not in df_split.columns and 'translation' not in df_split.columns:
            df_split['traduction'] = ''
        
        # Nom du fichier de sortie
        output_file = output_path / f"mina_part_{i+1:03d}_of_{num_files}.csv"
        
        # Sauvegarder en CSV avec encodage UTF-8
        df_split.to_csv(output_file, index=False, encoding='utf-8-sig')
        
        print(f"Créé: {output_file.name} ({len(df_split)} lignes)")
        
        start_idx = end_idx
    
    print(f"\n✓ Division terminée! {num_files} fichiers créés dans '{output_dir}/'")
    print(f"Total de lignes distribuées: {start_idx}")
    
    # Créer un fichier README pour les traducteurs
    readme_content = f"""# Instructions de Traduction - Mina

## Fichiers
Ce dossier contient {num_files} fichiers CSV extraits de Mina.xlsx.
Chaque fichier contient environ {rows_per_file} lignes à traduire.

## Comment traduire
1. Ouvrez le fichier CSV qui vous a été attribué avec Excel, LibreOffice ou Google Sheets
2. Traduisez le texte dans la colonne 'traduction'
3. Sauvegardez le fichier en gardant le même nom
4. Retournez le fichier traduit

## Important
- Ne modifiez PAS les autres colonnes
- Gardez le format CSV
- Utilisez l'encodage UTF-8

## Fichiers
"""
    
    for i in range(num_files):
        readme_content += f"- mina_part_{i+1:03d}_of_{num_files}.csv\n"
    
    with open(output_path / "README.txt", "w", encoding="utf-8") as f:
        f.write(readme_content)
    
    print(f"✓ README créé: {output_path / 'README.txt'}")

if __name__ == "__main__":
    split_excel_for_translation("Mina.xlsx", num_files=100)
