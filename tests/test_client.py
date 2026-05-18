"""Tests para src.client.bcch_client (con mocking de HTTP)."""

from datetime import date

import pandas as pd
import pytest

from src.client.bcch_client import BCChClient


@pytest.fixture
def client(monkeypatch):
    """Cliente con credenciales fake — no pega a la API real."""
    monkeypatch.setenv("BCCH_USER", "fake_user")
    monkeypatch.setenv("BCCH_PASSWORD", "fake_pass")
    return BCChClient()


@pytest.fixture
def respuesta_ok():
    """Respuesta JSON canónica de la API del BCCh."""
    return {
        "Codigo": 0,
        "Descripcion": "Success",
        "Series": {
            "descripEsp": "Test serie",
            "seriesId": "F073.TCO.PRE.Z.D",
            "Obs": [
                {"indexDateString": "02-01-2024", "value": "884.10"},
                {"indexDateString": "03-01-2024", "value": "888.50"},
                {"indexDateString": "04-01-2024", "value": "NaN"},
                {"indexDateString": "05-01-2024", "value": "890.20"},
            ],
        },
    }


class TestCredenciales:
    def test_sin_credenciales_falla(self, monkeypatch):
        monkeypatch.delenv("BCCH_USER", raising=False)
        monkeypatch.delenv("BCCH_PASSWORD", raising=False)
        with pytest.raises(ValueError, match="Faltan credenciales"):
            BCChClient()

    def test_credenciales_explicitas(self, monkeypatch):
        monkeypatch.delenv("BCCH_USER", raising=False)
        monkeypatch.delenv("BCCH_PASSWORD", raising=False)
        c = BCChClient(user="u", password="p")
        assert c.user == "u"


class TestGetSeries:
    def test_parsea_fechas_ddmmyyyy(self, client, monkeypatch, respuesta_ok):
        """Las fechas del BCCh vienen dd-mm-yyyy; deben quedar como datetime."""
        monkeypatch.setattr(client, "_request", lambda params: respuesta_ok)
        df = client.get_series("F073.TCO.PRE.Z.D", date(2024, 1, 1), date(2024, 1, 31))
        assert pd.api.types.is_datetime64_any_dtype(df["fecha"])
        assert df["fecha"].iloc[0] == pd.Timestamp("2024-01-02")

    def test_valores_a_float(self, client, monkeypatch, respuesta_ok):
        """Los valores vienen como string; deben quedar como float."""
        monkeypatch.setattr(client, "_request", lambda params: respuesta_ok)
        df = client.get_series("F073.TCO.PRE.Z.D", date(2024, 1, 1), date(2024, 1, 31))
        assert df["valor"].dtype == float
        assert df["valor"].iloc[0] == pytest.approx(884.10)

    def test_nan_string_es_nan(self, client, monkeypatch, respuesta_ok):
        """El 'NaN' como string debe convertirse a NaN numérico."""
        monkeypatch.setattr(client, "_request", lambda params: respuesta_ok)
        df = client.get_series("F073.TCO.PRE.Z.D", date(2024, 1, 1), date(2024, 1, 31))
        # La tercera obs era "NaN"
        assert pd.isna(df["valor"].iloc[2])

    def test_ordenado_por_fecha(self, client, monkeypatch, respuesta_ok):
        """El DataFrame de salida debe venir ordenado ascendente por fecha."""
        monkeypatch.setattr(client, "_request", lambda params: respuesta_ok)
        df = client.get_series("F073.TCO.PRE.Z.D", date(2024, 1, 1), date(2024, 1, 31))
        assert df["fecha"].is_monotonic_increasing


    def test_error_de_negocio(self, client, monkeypatch):
        """Codigo != 0 en la respuesta debe levantar RuntimeError.

        Mockeamos session.get (no _request) para que la validación real
        del cliente corra contra la respuesta simulada.
        """
        class FakeResponse:
            status_code = 200
            def raise_for_status(self):
                pass
            def json(self):
                return {"Codigo": -5, "Descripcion": "Serie no existe"}

        monkeypatch.setattr(client.session, "get", lambda *a, **kw: FakeResponse())
        with pytest.raises(RuntimeError, match="Serie no existe"):
            client.get_series("INVALIDA", date(2024, 1, 1), date(2024, 1, 31))