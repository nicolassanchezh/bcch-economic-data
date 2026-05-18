"""Actualiza data/bcch.db con las últimas observaciones del BCCh.

Diseñado para correr desde GitHub Actions semanalmente. Re-descarga
los últimos 90 días para asegurar overlap y resilience: si el workflow
falla varios runs seguidos, al volver a correr cubre el hueco.
"""

import sys
from datetime import date, timedelta
from pathlib import Path

# Permitir imports relativos desde scripts/
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.extract.series_extractor import SeriesExtractor
from src.storage.sqlite_storage import SQLiteStorage


def main():
    end = date.today()
    start = end - timedelta(days=90)

    print(f"Ventana de actualización: {start} → {end}")

    extractor = SeriesExtractor()
    storage = SQLiteStorage()

    results = extractor.extract_all(start, end)
    total = 0
    for alias, df in results.items():
        n = storage.save_observations(df)
        total += n
        print(f"  {alias}: {n} obs procesadas")

    print(f"\nTotal: {total} obs procesadas")
    print("\nEstado final:")
    print(storage.summary().to_string(index=False))


if __name__ == "__main__":
    main()