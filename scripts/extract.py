# scripts/extract.py

import yaml
import requests
import io
import pandas as pd
import pyarrow.parquet as pq
import geopandas as gpd
from pathlib import Path
from requests.exceptions import HTTPError

# Mapping logique → réel des colonnes
COLUMN_MAP = {
    "pickup_datetime": "pickup_datetime",
    "dropoff_datetime": "dropoff_datetime",
    "trip_distance":      "trip_distance",
    "passenger_count":    "passenger_count",
    "payment_type":       "payment_type",
    "total_amount":       "total_amount",
    "PULocationID":       "PULocationID",
    "DOLocationID":       "DOLocationID",
    "tip_amount":        "tip_amount",
    "payment_method":       "payment_method"
}

# Mapping payment_type → libellé
PAYMENT_MAP = {
    0: "Flex Fare",
    1: "Credit card",
    2: "Cash",
    3: "No charge",
    4: "Dispute",
    5: "Unknown",
    6: "Voided trip"
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
    print(f"⬇️ Downloading {url}")

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
    # Colonnes à charger
    real_cols = [COLUMN_MAP[c] for c in COLUMN_MAP]

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
                         usecols=real_cols,
                         parse_dates=[
                             COLUMN_MAP["pickup_datetime"],
                             COLUMN_MAP["dropoff_datetime"]
                         ])

    # Renommer colonnes réelles en logiques
    rename_map = {v: k for k, v in COLUMN_MAP.items() if v in df.columns}
    df = df.rename(columns=rename_map)

    # Nettoyage spécifique taxi
    if section == 'extract':
        df = df[(df['trip_distance'] > 0) & (df['passenger_count'] > 0)]

    # → Charger et fusionner les zones géographiques
    #    (on suppose taxi_zones.json dans le repo racine)
    tz = gpd.read_file("data/taxi_zones.json")  # GeoDataFrame avec champ LocationID et zone
    zones = tz[['LocationID','zone']].set_index('LocationID')

    # Fusion pour PULocationID et DOLocationID
    df = df.merge(zones.rename(columns={'zone':'PU_zone'}), left_on='PULocationID', right_index=True, how='left')
    df = df.merge(zones.rename(columns={'zone':'DO_zone'}), left_on='DOLocationID', right_index=True, how='left')

    # Cartes de paiement
    df['payment_method'] = df['payment_type'].map(PAYMENT_MAP).fillna("Other")

    # Sauvegarde en CSV
    out_folder = Path('data')
    out_folder.mkdir(exist_ok=True)
    out_file = out_folder / f"{month}-taxi.csv"
    df.to_csv(out_file, index=False)
    print(f"✅ Saved cleaned data to {out_file}")

if __name__ == '__main__':
    extract_section('extract')
    # Weather extraction supprimée
