"""Persistencia de observaciones económicas en SQLite."""
import sqlite3
from datetime import date
from pathlib import Path
from typing import Optional

import pandas as pd

class SQLiteStorage:
    """Maneja la persistencia de series económicas en SQLite."""

    PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
    DEFAULT_DB = PROJECT_ROOT / "data" / "bcch.db"

    SCHEMA = """
    CREATE TABLE IF NOT EXISTS observations (
        serie TEXT NOT NULL,
        fecha DATE NOT NULL,
        valor REAL,
        codigo TEXT NOT NULL,
        extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (serie, fecha)
    );

    CREATE INDEX IF NOT EXISTS idx_observations_fecha
        ON observations(fecha);
    """

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = Path(db_path) if db_path else self.DEFAULT_DB
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(self.SCHEMA)

    def save_observations(self, df: pd.DataFrame) -> int:
        """Inserta o actualiza observaciones. Idempotente por (serie, fecha)."""
        required = {"serie", "fecha", "valor", "codigo"}
        missing = required - set(df.columns)
        if missing:
            raise ValueError(f"Faltan columnas en el DataFrame: {missing}")

        df_to_save = df[["serie", "fecha", "valor", "codigo"]].copy()
        df_to_save["fecha"] = pd.to_datetime(df_to_save["fecha"]).dt.strftime("%Y-%m-%d")
        records = df_to_save.to_records(index=False).tolist()

        with self._connect() as conn:
            conn.executemany(
                """INSERT OR REPLACE INTO observations
                   (serie, fecha, valor, codigo)
                   VALUES (?, ?, ?, ?)""",
                records,
            )
        return len(records)

    def load_series(
        self,
        serie: str,
        start: Optional[date] = None,
        end: Optional[date] = None,
    ) -> pd.DataFrame:
        """Carga una serie como DataFrame, con filtro opcional de fechas."""
        query = "SELECT fecha, valor FROM observations WHERE serie = ?"
        params: list = [serie]

        if start:
            query += " AND fecha >= ?"
            params.append(start.isoformat())
        if end:
            query += " AND fecha <= ?"
            params.append(end.isoformat())

        query += " ORDER BY fecha"

        with self._connect() as conn:
            return pd.read_sql_query(query, conn, params=params, parse_dates=["fecha"])

    def summary(self) -> pd.DataFrame:
        """Reporte de estado: cuántas obs y rango de fechas por serie."""
        query = """
        SELECT
            serie,
            COUNT(*) AS n_obs,
            MIN(fecha) AS primera_fecha,
            MAX(fecha) AS ultima_fecha
        FROM observations
        GROUP BY serie
        ORDER BY serie
        """
        with self._connect() as conn:
            return pd.read_sql_query(query, conn)