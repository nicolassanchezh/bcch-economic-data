"""Dashboard interactivo de series económicas del Banco Central de Chile."""
from datetime import date

import matplotlib.pyplot as plt
import streamlit as st

from src.visualization import style as st_theme
from src.visualization import charts
from src.dashboard import services as svc

from src.visualization import charts_interactive as ci # agregado para gráficos Plotly interactivos, sin afectar los estáticos de charts.py



st_theme.apply_theme()

st.set_page_config(
    page_title="BCCh Economic Dashboard",
    page_icon="📊",
    layout="wide",
)

st.title("📊 BCCh Economic Dashboard")
st.caption(
    "Inflación, tasa de política monetaria y tipo de cambio observado. "
    "Datos: API de Estadísticas Económicas del Banco Central de Chile."
)

# ── Sidebar ──────────────────────────────────────────────────────────
st.sidebar.header("Controles")

# Cargar primero para conocer el rango disponible
df_ipc = svc.load_ipc()
df_tpm = svc.load_tpm()

min_date = df_ipc["fecha"].min().date()
max_date = df_tpm["fecha"].max().date()
default_start = date(max_date.year - 5, 1, 1)

start_date, end_date = st.sidebar.date_input(
    "Rango de fechas",
    value=(default_start, max_date),
    min_value=min_date,
    max_value=max_date,
)

show_meta_band = st.sidebar.checkbox("Mostrar banda de meta 3% ± 1pp", value=True)
usd_window = st.sidebar.slider("Ventana rolling USD/CLP (días)", 10, 90, 30, step=5)

st.sidebar.markdown("---")
st.sidebar.caption(
    f"Datos disponibles: **{min_date}** → **{max_date}**.  \n"
    "El cache se refresca cada hora."
)

# ── Datos filtrados ──────────────────────────────────────────────────
df_usd = svc.load_usd(window=usd_window)

ipc_f = svc.filter_dates(df_ipc, start_date, end_date)
tpm_f = svc.filter_dates(df_tpm, start_date, end_date)
usd_f = svc.filter_dates(df_usd, start_date, end_date)



# ── KPIs ─────────────────────────────────────────────────────────────
st.subheader("Última lectura")

def _delta(curr, prev, fmt="{:+.2f}", suffix=""):
    if prev is None or curr is None:
        return None
    return fmt.format(curr - prev) + suffix

ipc_last = ipc_f.dropna(subset=["yoy"]).iloc[-1] if not ipc_f.empty else None
tpm_last = tpm_f.iloc[-1] if not tpm_f.empty else None
usd_last = usd_f.iloc[-1] if not usd_f.empty else None

c1, c2, c3, c4 = st.columns(4)

if ipc_last is not None:
    ipc_prev = ipc_f.dropna(subset=["yoy"]).iloc[-2]
    c1.metric(
        "IPC y/y",
        f"{ipc_last['yoy']:.2f}%",
        _delta(ipc_last["yoy"], ipc_prev["yoy"], suffix=" pp"),
        help=f"Mes: {ipc_last['fecha'].strftime('%b %Y')}",
    )
    c2.metric(
        "IPC m/m",
        f"{ipc_last['mom']:.2f}%",
        _delta(ipc_last["mom"], ipc_prev["mom"], suffix=" pp"),
    )

if tpm_last is not None:
    cambios = tpm_f[tpm_f["diff_pp"].abs() > 1e-9]
    last_change = cambios.iloc[-1] if not cambios.empty else None
    c3.metric(
        "TPM",
        f"{tpm_last['valor']:.2f}%",
        f"{last_change['diff_pp']:+.2f} pp" if last_change is not None else None,
        help=f"Último cambio: {last_change['fecha'].date()}" if last_change is not None else None,
    )

if usd_last is not None:
    usd_prev = usd_f.iloc[-2] if len(usd_f) > 1 else None
    c4.metric(
        "USD/CLP",
        f"${usd_last['valor']:,.1f}",
        _delta(usd_last["valor"], usd_prev["valor"] if usd_prev is not None else None, fmt="{:+.1f}"),
    )

# ── Cuerpo: pestañas ─────────────────────────────────────────────────
tab_inf, tab_fx, tab_data = st.tabs(["📈 Inflación", "💱 Tipo de cambio", "📋 Datos"])

with tab_inf:
    st.markdown("### Inflación interanual y meta del BCCh")
    fig = ci.plot_ipc_yoy_interactive(
        ipc_f, meta=3.0, banda=1.0, show_band=show_meta_band,
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("### IPC y/y vs TPM (eje doble)")
    fig = ci.plot_ipc_tpm_twinx_interactive(ipc_f, tpm_f)
    st.plotly_chart(fig, use_container_width=True)

    st.caption(
        "Lectura: al subir, la TPM va detrás del IPC (política reactiva); "
        "una vez instalado el ciclo de alza, los efectos se transmiten a la "
        "inflación con rezago de 6-12 meses."
    )

with tab_fx:
    st.markdown(f"### USD/CLP con MA{usd_window} y banda ±2σ")
    fig = ci.plot_usd_clp_interactive(usd_f, window=usd_window)
    st.plotly_chart(fig, use_container_width=True)

    st.caption(
        f"Media móvil y volatilidad realizada calculadas sobre ventana de "
        f"{usd_window} días hábiles. La banda se ensancha en períodos de estrés cambiario."
    )


with tab_data:
    st.markdown("### Series filtradas")
    serie_sel = st.selectbox("Serie", ["IPC", "TPM", "USD/CLP"])
    dfs = {"IPC": ipc_f, "TPM": tpm_f, "USD/CLP": usd_f}
    df_show = dfs[serie_sel]

    st.dataframe(df_show, use_container_width=True, height=400)

    csv = df_show.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Descargar CSV",
        data=csv,
        file_name=f"{serie_sel.lower().replace('/', '_')}_{start_date}_{end_date}.csv",
        mime="text/csv",
    )