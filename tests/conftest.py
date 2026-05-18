"""Fixtures compartidas para la suite de tests."""

from datetime import date

import pandas as pd
import pytest

from src.storage.sqlite_storage import SQLiteStorage


@pytest.fixture
def tmp_db(tmp_path):
    """SQLiteStorage apuntando a una DB temporal por test.

    tmp_path lo provee pytest: una carpeta única por test que se borra al final.
    Así los tests no se contaminan entre sí ni tocan tu data/bcch.db real.
    """
    db_path = tmp_path / "test_bcch.db"
    return SQLiteStorage(db_path=db_path)


@pytest.fixture
def df_ipc_mensual():
    """IPC mensual sintético: 24 meses, niveles ascendentes."""
    fechas = pd.date_range("2023-01-01", periods=24, freq="MS")
    valores = [100.0 + i * 0.3 for i in range(24)]
    return pd.DataFrame({
        "fecha": fechas,
        "valor": valores,
        "serie": "ipc",
        "codigo": "F074.IPC.IND.Z.EP23.C.M",
    })


@pytest.fixture
def df_tpm_diaria():
    """TPM diaria sintética: 30 días, dos cambios de 25pb."""
    fechas = pd.date_range("2024-01-01", periods=30, freq="D")
    valores = [5.50] * 10 + [5.25] * 10 + [5.00] * 10
    return pd.DataFrame({
        "fecha": fechas,
        "valor": valores,
        "serie": "tpm",
        "codigo": "F022.TPM.TIN.D001.NO.Z.D",
    })


@pytest.fixture
def df_usd_diario():
    """USD/CLP diario sintético: 60 días con tendencia + ruido leve."""
    fechas = pd.date_range("2024-01-01", periods=60, freq="D")
    valores = [900.0 + i * 0.5 + (i % 5) * 2 for i in range(60)]
    return pd.DataFrame({
        "fecha": fechas,
        "valor": valores,
        "serie": "usd_clp",
        "codigo": "F073.TCO.PRE.Z.D",
    })