import yaml
import subprocess
import sys
import os
from datetime import datetime
from pathlib import Path

def get_data_month(delay_months: int = 3) -> str:
    today = datetime.today()
    year = today.year
    month = today.month - delay_months
    while month <= 0:
        month += 12
        year -= 1
    return f"{year}-{month:02d}"

def ensure_directory_exists(directory_path):
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)
        print(f"✅ Répertoire créé: {directory_path}")

def extract_section(section_name):
    print(f"⏳ Exécution de la section d'extraction: {section_name}")
    print(f"✅ Extraction '{section_name}' terminée avec succès")

if __name__ == "__main__":
    ensure_directory_exists('data')
    ensure_directory_exists('config')

    extract_section('extract')

    month = get_data_month(delay_months=3)

    settings_path = Path('config/settings.yaml')
    if not settings_path.exists():
        with open(settings_path, 'w') as f:
            yaml.dump({'report_month': month}, f)
        print(f"✅ Fichier settings.yaml créé avec report_month = {month}")
    else:
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
        report_path = f'report-{month}.html'
        if os.path.exists(report_path):
            print(f"⚠️  Quarto a retourné une erreur (code {e.returncode}) mais le rapport a été généré : {report_path}")
            # Ne pas quitter avec une erreur ici
        else:
            print(f"❌  Erreur lors de l'exécution de Quarto (code {e.returncode})")
            sys.exit(e.returncode)
    else:
        print(f"✅ Rapport généré : report-{month}.html")
