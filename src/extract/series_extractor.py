"""Orquestador de descargas: usa el cliente BCCh + el catálogo de series."""
from datetime import date
from pathlib import Path
from typing import Optional

import pandas as pd
import yaml

from src.client.bcch_client import BCChClient

class SeriesExtractor:
    """Descarga series según el catálogo en config/series.yaml."""

    PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
    DEFAULT_CONFIG = PROJECT_ROOT / "config" / "series.yaml"
    DEFAULT_OUTPUT = PROJECT_ROOT / "data" / "raw"

    def __init__(
        self,
        client: Optional[BCChClient] = None,
        config_path: Optional[Path] = None,
        output_dir: Optional[Path] = None,
    ):
        self.client = client or BCChClient()
        self.config_path = Path(config_path) if config_path else self.DEFAULT_CONFIG
        self.output_dir = Path(output_dir) if output_dir else self.DEFAULT_OUTPUT
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.config = self._load_config()

        
    def _load_config(self) -> dict:
        with open(self.config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def extract_one(self, alias: str, start: date, end: date) -> pd.DataFrame:
        """Descarga una serie por su alias en series.yaml."""
        if alias not in self.config["series"]:
            raise KeyError(f"Alias '{alias}' no existe en series.yaml")
        meta = self.config["series"][alias]
        df = self.client.get_series(meta["code"], start, end)
        df["serie"] = alias
        df["codigo"] = meta["code"]
        return df

    def extract_all(self, start: date, end: date) -> dict[str, pd.DataFrame]:
        """Descarga todas las series del catálogo. No falla si una falla."""
        results = {}
        for alias in self.config["series"]:
            print(f"Descargando {alias}...")
            try:
                df = self.extract_one(alias, start, end)
                results[alias] = df
                print(f"  ✓ {len(df)} observaciones")
            except Exception as e:
                print(f"  ✗ Error: {e}")
        return results

    def save_raw(self, alias: str, df: pd.DataFrame) -> Path:
        """Guarda un DataFrame en parquet con timestamp de extracción."""
        today = date.today().isoformat()
        path = self.output_dir / f"{alias}_{today}.parquet"
        df.to_parquet(path, index=False)
        return path

    def extract_and_save_all(
        self, start: date, end: date
    ) -> dict[str, Path]:
        """Pipeline completo: descarga + guarda. Devuelve rutas."""
        results = self.extract_all(start, end)
        saved = {}
        for alias, df in results.items():
            path = self.save_raw(alias, df)
            saved[alias] = path
            print(f"  → {path}")
        return saved
