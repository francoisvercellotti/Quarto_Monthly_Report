import yaml
import subprocess
import sys
import os
from datetime import datetime
from pathlib import Path

def get_data_month(delay_months: int = 3) -> str:
    """
    Retourne le mois (YYYY-MM) disponible avec un décalage de `delay_months` mois.
    Par exemple en mai 2025, delay_months=3 → '2025-02'.
    """
    today = datetime.today()
    year = today.year
    month = today.month - delay_months
    # Ajustement si on passe en année précédente
    while month <= 0:
        month += 12
        year -= 1
    return f"{year}-{month:02d}"

def ensure_directory_exists(directory_path):
    """Crée un répertoire s'il n'existe pas déjà."""
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)
        print(f"✅ Répertoire créé: {directory_path}")

def extract_section(section_name):
    """
    Simule l'exécution d'une section d'extraction.
    Dans un cas réel, cette fonction exécuterait un script d'extraction.
    """
    print(f"⏳ Exécution de la section d'extraction: {section_name}")
    # Dans un cas réel, on exécuterait par exemple:
    # subprocess.run(['python', f'scripts/extract_{section_name}.py'], check=True)
    print(f"✅ Extraction '{section_name}' terminée avec succès")

if __name__ == "__main__":
    # Création des répertoires nécessaires
    ensure_directory_exists('data')
    ensure_directory_exists('config')

    # 1️⃣ Extraction et nettoyage local
    extract_section('extract')
    # La partie d'extraction des données météo a été supprimée

    # 2️⃣ Calcul et mise à jour du mois dans settings.yaml
    month = get_data_month(delay_months=3)

    # Création du fichier settings.yaml s'il n'existe pas
    settings_path = Path('config/settings.yaml')
    if not settings_path.exists():
        with open(settings_path, 'w') as f:
            yaml.dump({'report_month': month}, f)
        print(f"✅ Fichier settings.yaml créé avec report_month = {month}")
    else:
        # Mise à jour du fichier existant
        try:
            cfg = yaml.safe_load(open(settings_path))
            if not cfg:
                cfg = {}
        except:
            cfg = {}

        cfg['report_month'] = month
        with open(settings_path, 'w') as f:
            yaml.dump(cfg, f)
        print(f"ℹ️  report_month mis à jour dans config/settings.yaml → {month}")

    # 3️⃣ Génération du rapport Quarto
    cmd = [
        'quarto', 'render', 'rapport.qmd',
        '--output', f'report-{month}.html'
    ]

    try:
        print("⏳ Génération du rapport Quarto...")
        subprocess.run(cmd, check=True)
    except FileNotFoundError:
        print("⚠️  La commande `quarto` n'a pas été trouvée. Veuillez installer Quarto CLI ou vérifier votre PATH.")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"❌  Erreur lors de l'exécution de Quarto (code {e.returncode})")
        sys.exit(e.returncode)

    print(f"✅ Rapport généré : report-{month}.html")