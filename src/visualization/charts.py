"""Funciones reutilizables de gráficos para series económicas chilenas.

Cada función recibe un DataFrame, opcionalmente un `ax` para componer
paneles, y devuelve el `ax` para encadenar modificaciones.
"""
from __future__ import annotations
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd

from . import style as st


def plot_ipc_nivel(df, ax=None, date_col="fecha", value_col="valor"):
    """IPC nivel (base dic-2023 = 100)."""
    if ax is None:
        _, ax = plt.subplots()
    ax.plot(df[date_col], df[value_col],
            color=st.COLOR_IPC, linewidth=1.5, label="IPC nivel")
    ax.set_title("IPC empalmado (base dic-2023 = 100)")
    ax.set_xlabel("")
    ax.set_ylabel("Índice")
    ax.legend(loc="upper left")
    return ax


def plot_ipc_yoy(df, ax=None, date_col="fecha", yoy_col="yoy",
                 meta=3.0, banda=1.0):
    """Variación interanual del IPC con banda de meta del BCCh."""
    if ax is None:
        _, ax = plt.subplots()

    # Banda de meta 3% ± 1pp (la tolerancia operativa del BCCh)
    ax.axhspan(meta - banda, meta + banda,
               alpha=0.15, color=st.COLOR_META,
               label=f"Meta {meta:.0f}% ± {banda:.0f} pp")
    ax.axhline(meta, color=st.COLOR_META, linewidth=0.8, linestyle="--")
    ax.axhline(0, color="black", linewidth=0.4)

    # Serie
    ax.plot(df[date_col], df[yoy_col],
            color=st.COLOR_IPC, linewidth=1.5, label="IPC y/y")
    ax.set_title("Inflación anual y meta del BCCh")
    ax.set_xlabel("")
    ax.set_ylabel("Variación interanual (%)")
    ax.legend(loc="upper left")
    return ax


def plot_tpm(df, ax=None, date_col="fecha", value_col="valor"):
    """TPM como step function (cambia en escalones discretos)."""
    if ax is None:
        _, ax = plt.subplots()
    ax.step(df[date_col], df[value_col], where="post",
            color=st.COLOR_TPM, linewidth=1.5, label="TPM")
    ax.set_title("Tasa de Política Monetaria")
    ax.set_xlabel("")
    ax.set_ylabel("TPM (%)")
    ax.legend(loc="upper right")
    return ax


def plot_usd_clp(df, ax=None, date_col="fecha", value_col="valor",
                 ma_col="ma_30d", vol_col="vol_30d"):
    """USD/CLP nivel con MA 30d y banda ±1σ de volatilidad."""
    if ax is None:
        _, ax = plt.subplots()

    # Banda de volatilidad: MA ± (vol_diaria * MA)
    if ma_col in df.columns and vol_col in df.columns:
        # vol_30d está en puntos porcentuales (pct_change x100); convertir a fracción
        vol_frac = df[vol_col] / 100
        upper = df[ma_col] * (1 + 2 * vol_frac)
        lower = df[ma_col] * (1 - 2 * vol_frac)
        ax.fill_between(df[date_col], lower, upper,
                        alpha=0.25, color=st.COLOR_USD, label="MA30d ±2σ")
        ax.plot(df[date_col], df[ma_col],
                color=st.COLOR_USD, linewidth=1.0, alpha=0.6, label="MA 30d")

    ax.plot(df[date_col], df[value_col],
            color=st.COLOR_USD, linewidth=1.2, label="USD/CLP")
    ax.set_title("Tipo de cambio observado USD/CLP")
    ax.set_xlabel("")
    ax.set_ylabel("CLP por USD")
    ax.legend(loc="upper left")
    return ax


def plot_ipc_vs_tpm(df_ipc, df_tpm):
    """Panel apilado: IPC y/y arriba, TPM abajo, eje temporal compartido."""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 7), sharex=True)

    plot_ipc_yoy(df_ipc, ax=ax1)
    plot_tpm(df_tpm, ax=ax2)

    # Formato de fechas compartido en el eje X inferior
    ax2.xaxis.set_major_locator(mdates.YearLocator(base=2))
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))

    fig.suptitle("Inflación vs. política monetaria — Chile",
                 fontsize=14, fontweight="bold", y=1.00)
    fig.tight_layout()
    return fig


def save_figure(fig, path):
    """Guarda figura como PNG. Crea el directorio si no existe."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path)
    return path



def plot_ipc_tpm_twinx(df_ipc, df_tpm,
                       date_col="fecha", yoy_col="yoy", tpm_col="valor",
                       meta=3.0, banda=1.0):
    """IPC y/y y TPM en un solo panel con doble eje Y.
    
    IPC y/y en eje izquierdo (rojo), TPM en eje derecho (azul).
    """
    fig, ax1 = plt.subplots(figsize=(11, 5.5))

    # Banda de meta (en escala de IPC, eje izquierdo)
    ax1.axhspan(meta - banda, meta + banda,
                alpha=0.10, color=st.COLOR_META, zorder=0)
    ax1.axhline(meta, color=st.COLOR_META, linewidth=0.8, linestyle="--", zorder=1)

    # IPC y/y — eje izquierdo
    l1, = ax1.plot(df_ipc[date_col], df_ipc[yoy_col],
                   color=st.COLOR_IPC, linewidth=1.6, label="IPC y/y (izq.)")
    ax1.set_ylabel("IPC variación interanual (%)", color=st.COLOR_IPC)
    ax1.tick_params(axis="y", labelcolor=st.COLOR_IPC)

    # TPM — eje derecho
    ax2 = ax1.twinx()
    ax2.grid(False)  # evitar grilla doble
    l2, = ax2.step(df_tpm[date_col], df_tpm[tpm_col], where="post",
                   color=st.COLOR_TPM, linewidth=1.6, label="TPM (der.)")
    ax2.set_ylabel("TPM (%)", color=st.COLOR_TPM)
    ax2.tick_params(axis="y", labelcolor=st.COLOR_TPM)
    ax2.spines["top"].set_visible(False)  # mantener el estilo limpio

    # Leyenda unificada
    ax1.legend(handles=[l1, l2], loc="upper left")
    ax1.set_title("Inflación vs. política monetaria — Chile")
    ax1.set_xlabel("")

    fig.tight_layout()
    return fig