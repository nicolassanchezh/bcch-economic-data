"""Transformaciones analíticas sobre series económicas."""

from typing import Literal

import pandas as pd


def pct_change(df: pd.DataFrame, periods: int = 1, value_col: str = "valor") -> pd.Series:
    """Variación porcentual sobre N períodos, expresada en %.

    Sobre IPC mensual: periods=1 da m/m, periods=12 da y/y.
    Sobre USD/CLP diario: periods=1 da retorno diario.
    """
    df = df.sort_values("fecha")
    return df[value_col].pct_change(periods) * 100


def diff(df: pd.DataFrame, periods: int = 1, value_col: str = "valor") -> pd.Series:
    """Diferencia absoluta sobre N períodos.

    Útil para series que ya son tasas (TPM): el resultado son puntos porcentuales.
    """
    df = df.sort_values("fecha")
    return df[value_col].diff(periods)


def rolling_mean(df: pd.DataFrame, window: int, value_col: str = "valor") -> pd.Series:
    """Media móvil simple de N períodos."""
    df = df.sort_values("fecha")
    return df[value_col].rolling(window=window, min_periods=window).mean()


def rolling_std(df: pd.DataFrame, window: int, value_col: str = "valor") -> pd.Series:
    """Desviación estándar móvil — proxy de volatilidad."""
    df = df.sort_values("fecha")
    return df[value_col].rolling(window=window, min_periods=window).std()


def to_monthly(
    df: pd.DataFrame,
    method: Literal["last", "mean", "first"] = "last",
    value_col: str = "valor",
    date_col: str = "fecha",
) -> pd.DataFrame:
    """Reagrega una serie a frecuencia mensual.

    method:
        'last'  → valor del último día disponible del mes (cierre).
        'mean'  → promedio del mes.
        'first' → valor del primer día disponible del mes (apertura).

    El label de cada mes queda en el primer día (compatible con la convención
    del BCCh para IPC, que viene fechado al 1° de cada mes).
    """
    if method not in {"last", "mean", "first"}:
        raise ValueError(f"method debe ser 'last', 'mean' o 'first', no {method!r}")

    sub = df[[date_col, value_col]].sort_values(date_col).set_index(date_col)
    result = sub.resample("MS").agg(method)
    return result.reset_index()


def merge_wide(
    series: dict[str, pd.DataFrame],
    value_col: str = "valor",
    date_col: str = "fecha",
    how: str = "outer",
) -> pd.DataFrame:
    """Combina varias series long en un único DataFrame wide.

    series: {nombre_columna_final: dataframe_long}.
    Asume que todas las series están a la misma frecuencia.
    """
    out: pd.DataFrame | None = None
    for name, df in series.items():
        sub = (
            df[[date_col, value_col]]
            .rename(columns={value_col: name})
            .sort_values(date_col)
        )
        out = sub if out is None else out.merge(sub, on=date_col, how=how)
    return out.sort_values(date_col).reset_index(drop=True)