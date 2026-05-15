"""Tema visual unificado para todos los gráficos del proyecto."""
import matplotlib.pyplot as plt
import seaborn as sns

# Paleta inspirada en los colores del BCCh
COLOR_IPC   = "#C8102E"   # rojo
COLOR_TPM   = "#003DA5"   # azul institucional
COLOR_USD   = "#2E7D32"   # verde
COLOR_META  = "#666666"   # gris para referencias
COLOR_GRID  = "#E5E5E5"


def apply_theme():
    """Aplica el tema base. Llamar al inicio del notebook."""
    sns.set_style("whitegrid")
    plt.rcParams.update({
        "figure.figsize": (11, 5),
        "figure.dpi": 100,
        "savefig.dpi": 150,
        "savefig.bbox": "tight",
        "font.family": "DejaVu Sans",
        "font.size": 10,
        "axes.titlesize": 13,
        "axes.titleweight": "bold",
        "axes.labelsize": 10,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.color": COLOR_GRID,
        "grid.linewidth": 0.5,
        "legend.frameon": False,
        "legend.fontsize": 9,
    })