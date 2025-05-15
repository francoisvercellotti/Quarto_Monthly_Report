# scripts/extract.py

import yaml
import requests
import io
import pandas as pd
import pyarrow.parquet as pq
from pathlib import Path
from requests.exceptions import HTTPError

# Mapping logique → réel des colonnes
COLUMN_MAP = {
    "pickup_datetime": "tpep_pickup_datetime",
    "dropoff_datetime": "tpep_dropoff_datetime",
    "trip_distance":      "trip_distance",
    "passenger_count":    "passenger_count"
}

def load_config(path: str, section: str) -> dict:
    cfg = yaml.safe_load(open(path))
    text = yaml.dump(cfg)
    for k, v in cfg.items():
        if isinstance(v, str):
            text = text.replace(f"${{{k}}}", v)
    cfg = yaml.safe_load(text)
    base = {k: v for k, v in cfg.items() if k not in ['extract', 'extract_weather']}
    base.update(cfg.get(section, {}))
    return base

def extract_section(section: str):
    cfg = load_config('config/settings.yaml', section)
    month = cfg['report_month']
    file_name = f"{cfg['file_prefix']}_{month}{cfg['file_extension']}"
    url = cfg['url_pattern'].format(file_name=file_name)
    print(f"⬇️  Downloading {url}")

    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
    except HTTPError as e:
        print(f"⚠️ Skip {url}: {e}")
        return
    except requests.RequestException as e:
        print(f"⚠️ Error fetching {url}: {e}")
        return

    data = r.content
    logical_cols = [f['name'] for f in cfg.get('fields', [])]
    real_cols = [COLUMN_MAP.get(c, c) for c in logical_cols]

    # Lecture des données
    if file_name.endswith('.parquet'):
        buf = io.BytesIO(data)
        try:
            table = pq.read_table(buf, columns=real_cols)
            df = table.to_pandas()
        except (KeyError, ValueError):
            buf.seek(0)
            df = pq.read_table(buf).to_pandas()
    else:
        df = pd.read_csv(io.BytesIO(data),
                         usecols=real_cols if real_cols else None,
                         parse_dates=[COLUMN_MAP.get("pickup_datetime"), COLUMN_MAP.get("dropoff_datetime")])

    # Renommer colonnes réelles en logiques
    rename_map = {v: k for k, v in COLUMN_MAP.items() if v in df.columns}
    df = df.rename(columns=rename_map)

    # Nettoyage spécifique taxi
    if section == 'extract':
        df = df[(df['trip_distance'] > 0) & (df['passenger_count'] > 0)]

    # Sauvegarde en CSV
    out_folder = Path('data')
    out_folder.mkdir(exist_ok=True)
    suffix = 'taxi' if section == 'extract' else 'meteo'
    out_file = out_folder / f"{month}-{suffix}.csv"
    df.to_csv(out_file, index=False)
    print(f"✅ Saved cleaned data to {out_file}")

if __name__ == '__main__':
    extract_section('extract')
    # La partie qui charge les données météo a été supprimée