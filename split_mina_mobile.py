"""
Script pour diviser le fichier Mina.xlsx en 100 fichiers texte simples pour mobile
"""
import pandas as pd
from pathlib import Path

def split_excel_to_simple_txt(input_file, num_files=100, output_dir="mina_mobile_txt"):
    """
    Divise un fichier Excel en fichiers texte ultra-simples pour édition mobile
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
        output_file = output_path / f"mina_{i+1:03d}.txt"
        
        # Sauvegarder en fichier texte ultra-simple
        with open(output_file, 'w', encoding='utf-8') as f:
            # En-tête minimal
            f.write(f"MINA - Partie {i+1}/{num_files}\n")
            f.write(f"Lignes {start_idx + 1} à {end_idx}\n\n")
            
            # Écrire chaque ligne de façon simple
            for line_num, (idx, row) in enumerate(df_split.iterrows(), 1):
                # Numéro de ligne
                f.write(f"{line_num}.\n")
                
                # Texte original (première colonne non-vide)
                original_text = ""
                for col in df_split.columns:
                    if pd.notna(row[col]) and str(row[col]).strip():
                        original_text = str(row[col])
                        break
                
                f.write(f"{original_text}\n")
                f.write(f"→ \n\n")  # Espace pour la traduction
        
        print(f"Créé: {output_file.name} ({len(df_split)} lignes)")
        
        start_idx = end_idx
    
    print(f"\n✓ Division terminée! {num_files} fichiers créés dans '{output_dir}/'")
    
    # Créer un fichier README simple
    readme_content = f"""MINA - Instructions de Traduction

📱 POUR MOBILE

{num_files} fichiers: mina_001.txt à mina_{num_files:03d}.txt

COMMENT TRADUIRE:
1. Ouvrez votre fichier (.txt)
2. Pour chaque ligne, écrivez la traduction après →
3. Sauvegardez

EXEMPLE:
1.
Bonjour comment allez-vous?
→ Hello how are you?

2.
Je vais bien merci
→ I'm fine thanks

C'est tout! Simple et rapide 😊
"""
    
    with open(output_path / "README.txt", "w", encoding="utf-8") as f:
        f.write(readme_content)
    
    print(f"✓ README créé: {output_path / 'README.txt'}")

if __name__ == "__main__":
    split_excel_to_simple_txt("Mina.xlsx", num_files=100)
