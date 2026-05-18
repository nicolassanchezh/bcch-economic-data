"""Accesores cacheados para el dashboard.

Streamlit re-ejecuta todo el script en cada interacción del usuario.
Sin cache, eso significaría re-abrir SQLite y recalcular variaciones
en cada click. `@st.cache_data` memoiza los resultados por argumentos.
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from src.storage.sqlite_storage import SQLiteStorage
from src.analysis import transformations as tx


@st.cache_resource
def get_storage() -> SQLiteStorage:
    """Singleton de la conexión a SQLite. cache_resource para objetos vivos."""
    return SQLiteStorage()


@st.cache_data(ttl=3600)
def load_ipc() -> pd.DataFrame:
    """IPC mensual con mom, yoy y ma_3m calculados."""
    df = get_storage().load_series("ipc").copy()
    df["mom"] = tx.pct_change(df, periods=1)
    df["yoy"] = tx.pct_change(df, periods=12)
    df["ma_3m"] = tx.rolling_mean(df, window=3, value_col="mom")
    return df


@st.cache_data(ttl=3600)
def load_tpm() -> pd.DataFrame:
    """TPM diaria con diff_pp."""
    df = get_storage().load_series("tpm").copy()
    df["diff_pp"] = tx.diff(df, periods=1)
    return df


@st.cache_data(ttl=3600)
def load_usd(window: int = 30) -> pd.DataFrame:
    """USD/CLP diario con retorno, MA y volatilidad rolling.

    Filtra filas no-hábiles (NaN en valor) antes de los cálculos rolling,
    para que la ventana opere sobre días de mercado y no sobre días calendario.
    """
    df = get_storage().load_series("usd_clp").copy()
    df = df.dropna(subset=["valor"]).reset_index(drop=True)
    df["ret_1d"] = tx.pct_change(df, periods=1)
    df["ma_nd"]  = tx.rolling_mean(df, window=window)
    df["vol_nd"] = tx.rolling_std(df, window=window, value_col="ret_1d")
    return df


def filter_dates(df: pd.DataFrame, start, end, col: str = "fecha") -> pd.DataFrame:
    """Filtro de rango aplicado en memoria sobre el DataFrame ya cacheado."""
    mask = (df[col] >= pd.Timestamp(start)) & (df[col] <= pd.Timestamp(end))
    return df.loc[mask].copy()