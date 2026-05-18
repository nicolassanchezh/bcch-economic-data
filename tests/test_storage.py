"""Tests para src.storage.sqlite_storage."""

from datetime import date

import pandas as pd
import pytest


class TestSchema:
    def test_db_se_crea(self, tmp_db):
        """Al instanciar, el archivo .db debe existir."""
        assert tmp_db.db_path.exists()

    def test_tabla_observations(self, tmp_db):
        """La tabla observations debe estar creada con el schema esperado."""
        with tmp_db._connect() as conn:
            cur = conn.execute("PRAGMA table_info(observations)")
            cols = {row[1] for row in cur.fetchall()}
        assert {"serie", "fecha", "valor", "codigo", "extracted_at"}.issubset(cols)


class TestSave:
    def test_inserta_obs(self, tmp_db, df_ipc_mensual):
        """save_observations inserta el número correcto de filas."""
        n = tmp_db.save_observations(df_ipc_mensual)
        assert n == len(df_ipc_mensual)

    def test_idempotente(self, tmp_db, df_ipc_mensual):
        """Re-guardar el mismo DataFrame no genera duplicados."""
        tmp_db.save_observations(df_ipc_mensual)
        tmp_db.save_observations(df_ipc_mensual)
        loaded = tmp_db.load_series("ipc")
        assert len(loaded) == len(df_ipc_mensual)

    def test_falla_sin_columnas_requeridas(self, tmp_db):
        """Debe lanzar ValueError si falta una columna obligatoria."""
        df_malo = pd.DataFrame({"fecha": [date(2024, 1, 1)], "valor": [100.0]})
        with pytest.raises(ValueError, match="Faltan columnas"):
            tmp_db.save_observations(df_malo)

    def test_replace_actualiza_valores(self, tmp_db, df_ipc_mensual):
        """Si la (serie,fecha) ya existe, debe actualizar el valor (UPSERT)."""
        tmp_db.save_observations(df_ipc_mensual)
        df_modificado = df_ipc_mensual.copy()
        df_modificado.loc[0, "valor"] = 999.99
        tmp_db.save_observations(df_modificado)
        loaded = tmp_db.load_series("ipc")
        assert loaded.iloc[0]["valor"] == pytest.approx(999.99)


class TestLoad:
    def test_filtro_fechas(self, tmp_db, df_ipc_mensual):
        """load_series con start/end debe filtrar correctamente."""
        tmp_db.save_observations(df_ipc_mensual)
        loaded = tmp_db.load_series("ipc", start=date(2023, 6, 1), end=date(2023, 12, 31))
        assert len(loaded) == 7  # jun a dic 2023
        assert loaded["fecha"].min() >= pd.Timestamp("2023-06-01")
        assert loaded["fecha"].max() <= pd.Timestamp("2023-12-31")

    def test_serie_inexistente_vacia(self, tmp_db, df_ipc_mensual):
        """Serie sin datos devuelve DataFrame vacío, no error."""
        tmp_db.save_observations(df_ipc_mensual)
        loaded = tmp_db.load_series("no_existe")
        assert len(loaded) == 0
        assert "fecha" in loaded.columns
        assert "valor" in loaded.columns

    def test_fechas_parseadas_datetime(self, tmp_db, df_ipc_mensual):
        """La columna fecha del DataFrame cargado debe ser datetime, no string."""
        tmp_db.save_observations(df_ipc_mensual)
        loaded = tmp_db.load_series("ipc")
        assert pd.api.types.is_datetime64_any_dtype(loaded["fecha"])


class TestSummary:
    def test_summary_reporta_serie(self, tmp_db, df_ipc_mensual, df_tpm_diaria):
        """summary debe listar todas las series con sus conteos y rangos."""
        tmp_db.save_observations(df_ipc_mensual)
        tmp_db.save_observations(df_tpm_diaria)
        s = tmp_db.summary()
        assert set(s["serie"]) == {"ipc", "tpm"}
        ipc_row = s[s["serie"] == "ipc"].iloc[0]
        assert ipc_row["n_obs"] == len(df_ipc_mensual)