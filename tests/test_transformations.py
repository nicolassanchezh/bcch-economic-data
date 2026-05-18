"""Tests para src.analysis.transformations."""

import numpy as np
import pandas as pd
import pytest

from src.analysis import transformations as tx


class TestPctChange:
    def test_basico_mensual(self, df_ipc_mensual):
        """Una variación 100 → 100.3 da 0.3%."""
        mom = tx.pct_change(df_ipc_mensual, periods=1)
        assert pd.isna(mom.iloc[0])  # primera obs sin base
        assert mom.iloc[1] == pytest.approx(0.3, abs=1e-9)

    def test_yoy_necesita_12_periodos(self, df_ipc_mensual):
        """Las primeras 12 observaciones de y/y deben ser NaN."""
        yoy = tx.pct_change(df_ipc_mensual, periods=12)
        assert yoy.iloc[:12].isna().all()
        assert not pd.isna(yoy.iloc[12])

    def test_sort_implicito(self):
        """pct_change debe ordenar por fecha aunque venga desordenado."""
        df = pd.DataFrame({
            "fecha": pd.to_datetime(["2024-03-01", "2024-01-01", "2024-02-01"]),
            "valor": [102.0, 100.0, 101.0],
        })
        result = tx.pct_change(df, periods=1)
        # Después de ordenar: [100, 101, 102] → [NaN, 1.0, ~0.99]
        assert pd.isna(result.iloc[0])
        assert result.iloc[1] == pytest.approx(1.0, abs=1e-6)


class TestDiff:
    def test_tpm_diferencia_pp(self, df_tpm_diaria):
        """Sobre TPM (tasa), diff debe dar puntos porcentuales absolutos."""
        d = tx.diff(df_tpm_diaria, periods=1)
        # Hay un cambio de 5.50 → 5.25 en la posición 10
        assert d.iloc[10] == pytest.approx(-0.25)
        # Posiciones sin cambio son 0
        assert d.iloc[5] == pytest.approx(0.0)


class TestRolling:
    def test_rolling_mean_window_3(self):
        """Media móvil de ventana 3 sobre [1,2,3,4,5] da [NaN, NaN, 2, 3, 4]."""
        df = pd.DataFrame({
            "fecha": pd.date_range("2024-01-01", periods=5, freq="D"),
            "valor": [1.0, 2.0, 3.0, 4.0, 5.0],
        })
        ma = tx.rolling_mean(df, window=3)
        assert ma.iloc[:2].isna().all()
        assert ma.iloc[2] == pytest.approx(2.0)
        assert ma.iloc[3] == pytest.approx(3.0)
        assert ma.iloc[4] == pytest.approx(4.0)

    def test_rolling_std_positivo(self, df_usd_diario):
        """La volatilidad debe ser >= 0 donde está definida."""
        vol = tx.rolling_std(df_usd_diario, window=10)
        defined = vol.dropna()
        assert (defined >= 0).all()


class TestToMonthly:
    def test_last_de_mes(self, df_usd_diario):
        """method='last' debe tomar el último valor de cada mes."""
        monthly = tx.to_monthly(df_usd_diario, method="last")
        # Hay 60 días desde 2024-01-01 → debe haber 2-3 meses
        assert len(monthly) >= 2
        # Fechas mensualizadas etiquetadas al primer día del mes
        assert monthly["fecha"].iloc[0].day == 1

    def test_method_invalido(self, df_usd_diario):
        with pytest.raises(ValueError, match="method"):
            tx.to_monthly(df_usd_diario, method="median")


class TestMergeWide:
    def test_join_por_fecha(self, df_ipc_mensual, df_tpm_diaria):
        """merge_wide debe alinear por fecha con una columna por serie."""
        tpm_mensual = tx.to_monthly(df_tpm_diaria, method="last")
        wide = tx.merge_wide({"ipc": df_ipc_mensual, "tpm": tpm_mensual})
        assert "fecha" in wide.columns
        assert "ipc" in wide.columns
        assert "tpm" in wide.columns