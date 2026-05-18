"""Versiones Plotly de los gráficos para el dashboard interactivo.

Las funciones de `charts.py` (matplotlib) se mantienen para generar los
PNG estáticos que van al README. Estas son sus contrapartes con hover
tooltips, zoom y pan nativos, pensadas para usarse en Streamlit.
"""
from __future__ import annotations

import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Paleta consistente con src/visualization/style.py
COLOR_IPC  = "#C8102E"
COLOR_TPM  = "#003DA5"
COLOR_USD  = "#2E7D32"
COLOR_META = "#888888"
COLOR_BAND = "rgba(255, 152, 0, 0.20)"
COLOR_MA   = "#1B5E20"

LAYOUT_BASE = dict(
    template="plotly_white",
    margin=dict(l=50, r=40, t=60, b=40),
    hovermode="x unified",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    font=dict(family="sans-serif", size=12),
)


def plot_ipc_yoy_interactive(df, date_col="fecha", yoy_col="yoy",
                             meta=3.0, banda=1.0, show_band=True):
    """IPC y/y con banda de meta del BCCh — interactivo."""
    fig = go.Figure()

    if show_band and banda > 0:
        fig.add_hrect(
            y0=meta - banda, y1=meta + banda,
            fillcolor=COLOR_META, opacity=0.12, line_width=0,
            annotation_text=f"Meta {meta:.0f}% ± {banda:.0f} pp",
            annotation_position="top left",
            annotation_font_size=10,
        )
    fig.add_hline(y=meta, line=dict(color=COLOR_META, width=1, dash="dash"))
    fig.add_hline(y=0, line=dict(color="black", width=0.4))

    fig.add_trace(go.Scatter(
        x=df[date_col], y=df[yoy_col],
        mode="lines", name="IPC y/y",
        line=dict(color=COLOR_IPC, width=2),
        hovertemplate="%{x|%b %Y}<br>IPC y/y: <b>%{y:.2f}%</b><extra></extra>",
    ))

    fig.update_layout(
        title="Inflación anual y meta del BCCh",
        yaxis_title="Variación interanual (%)",
        xaxis_title="",
        **LAYOUT_BASE,
    )
    return fig


def plot_ipc_tpm_twinx_interactive(df_ipc, df_tpm,
                                   date_col="fecha", yoy_col="yoy", tpm_col="valor"):
    """IPC y/y y TPM en doble eje Y — interactivo."""
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(
        go.Scatter(
            x=df_ipc[date_col], y=df_ipc[yoy_col],
            mode="lines", name="IPC y/y (izq.)",
            line=dict(color=COLOR_IPC, width=2),
            hovertemplate="IPC y/y: <b>%{y:.2f}%</b><extra></extra>",
        ),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=df_tpm[date_col], y=df_tpm[tpm_col],
            mode="lines", name="TPM (der.)",
            line=dict(color=COLOR_TPM, width=2, shape="hv"),
            hovertemplate="TPM: <b>%{y:.2f}%</b><extra></extra>",
        ),
        secondary_y=True,
    )

    fig.update_yaxes(title_text="IPC y/y (%)", color=COLOR_IPC,
                     secondary_y=False)
    fig.update_yaxes(title_text="TPM (%)", color=COLOR_TPM,
                     secondary_y=True, showgrid=False)
    fig.update_layout(
        title="Inflación vs. política monetaria",
        xaxis_title="",
        **LAYOUT_BASE,
    )
    return fig


def plot_usd_clp_interactive(df, window=30,
                             date_col="fecha", value_col="valor",
                             ma_col="ma_nd", vol_col="vol_nd"):
    """USD/CLP con MA y banda ±2σ — interactivo."""
    fig = go.Figure()

    if ma_col in df.columns and vol_col in df.columns:
        vol_frac = df[vol_col] / 100
        upper = df[ma_col] * (1 + 2 * vol_frac)
        lower = df[ma_col] * (1 - 2 * vol_frac)

        # Banda como área entre dos traces invisibles
        fig.add_trace(go.Scatter(
            x=df[date_col], y=upper, mode="lines",
            line=dict(width=0), showlegend=False, hoverinfo="skip",
        ))
        fig.add_trace(go.Scatter(
            x=df[date_col], y=lower, mode="lines",
            line=dict(width=0), fill="tonexty", fillcolor=COLOR_BAND,
            name=f"MA{window} ±2σ", hoverinfo="skip",
        ))
        fig.add_trace(go.Scatter(
            x=df[date_col], y=df[ma_col],
            mode="lines", name=f"MA {window}d",
            line=dict(color=COLOR_MA, width=1.5, dash="dash"),
            hovertemplate="MA: <b>$%{y:,.1f}</b><extra></extra>",
        ))

    fig.add_trace(go.Scatter(
        x=df[date_col], y=df[value_col],
        mode="lines", name="USD/CLP",
        line=dict(color=COLOR_USD, width=1.8),
        hovertemplate="%{x|%d-%b-%Y}<br>USD/CLP: <b>$%{y:,.1f}</b><extra></extra>",
    ))

    fig.update_layout(
        title="Tipo de cambio observado USD/CLP",
        yaxis_title="CLP por USD",
        xaxis_title="",
        **LAYOUT_BASE,
    )
    return fig