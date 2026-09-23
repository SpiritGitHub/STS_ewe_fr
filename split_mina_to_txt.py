"""
Script pour diviser le fichier Mina.xlsx en 100 fichiers texte pour traduction
"""
import pandas as pd
import os
from pathlib import Path

def split_excel_to_txt(input_file, num_files=100, output_dir="mina_translation_txt"):
    """
    Divise un fichier Excel en plusieurs fichiers texte pour faciliter la traduction
    
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
        
        # Nom du fichier de sortie
        output_file = output_path / f"mina_part_{i+1:03d}_of_{num_files}.txt"
        
        # Sauvegarder en fichier texte
        with open(output_file, 'w', encoding='utf-8') as f:
            # En-tête
            f.write(f"=" * 80 + "\n")
            f.write(f"FICHIER DE TRADUCTION - Partie {i+1} sur {num_files}\n")
            f.write(f"=" * 80 + "\n\n")
            
            # Écrire chaque ligne
            for idx, row in df_split.iterrows():
                f.write(f"--- Ligne {idx + 1} ---\n")
                
                # Écrire toutes les colonnes
                for col in df_split.columns:
                    value = row[col]
                    if pd.notna(value):  # Si la valeur n'est pas NaN
                        f.write(f"{col}: {value}\n")
                
                # Ajouter un espace pour la traduction
                f.write(f"\n[TRADUCTION]:\n\n")
                f.write("-" * 80 + "\n\n")
        
        print(f"Créé: {output_file.name} ({len(df_split)} lignes)")
        
        start_idx = end_idx
    
    print(f"\n✓ Division terminée! {num_files} fichiers créés dans '{output_dir}/'")
    print(f"Total de lignes distribuées: {start_idx}")
    
    # Créer un fichier README pour les traducteurs
    readme_content = f"""# Instructions de Traduction - Mina

## Fichiers
Ce dossier contient {num_files} fichiers texte extraits de Mina.xlsx.
Chaque fichier contient environ {rows_per_file} lignes à traduire.

## Comment traduire
1. Ouvrez le fichier .txt qui vous a été attribué avec n'importe quel éditeur de texte
2. Pour chaque entrée, écrivez la traduction dans la section [TRADUCTION]
3. Sauvegardez le fichier en gardant le même nom
4. Retournez le fichier traduit

## Format
Chaque entrée est délimitée par des lignes de tirets (---)
Écrivez votre traduction après la mention [TRADUCTION]:

## Important
- Gardez le format du fichier
- Utilisez l'encodage UTF-8
- Ne modifiez pas les numéros de ligne

## Liste des fichiers
"""
    
    for i in range(num_files):
        readme_content += f"- mina_part_{i+1:03d}_of_{num_files}.txt\n"
    
    with open(output_path / "README.txt", "w", encoding="utf-8") as f:
        f.write(readme_content)
    
    print(f"✓ README créé: {output_path / 'README.txt'}")

if __name__ == "__main__":
    split_excel_to_txt("Mina.xlsx", num_files=100)
