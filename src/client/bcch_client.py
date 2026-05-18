import os
from datetime import date
from typing import Optional

import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()

class BCChClient:
    """Cliente para el endpoint REST del BCCh (SieteRestWS)."""

    BASE_URL = "https://si3.bcentral.cl/SieteRestWS/SieteRestWS.ashx"
    VALID_FREQUENCIES = {"DAILY", "MONTHLY", "QUARTERLY", "ANNUAL"}  #limitador a frecuencias del BCCh

    def __init__(
        self,
        user: Optional[str] = None,
        password: Optional[str] = None,
    ):
        self.user = user or os.getenv("BCCH_USER")
        self.password = password or os.getenv("BCCH_PASSWORD")
        if not self.user or not self.password:
            raise ValueError(
                "Faltan credenciales. Define BCCH_USER y BCCH_PASSWORD en .env "
                
            )
        self.session = requests.Session()
    
    def _request(self, params: dict) -> dict:
        """Hace el GET, valida HTTP y código de negocio del BCCh."""
        full_params = {"user": self.user, "pass": self.password, **params}
        response = self.session.get(self.BASE_URL, params=full_params, timeout=30)
        response.raise_for_status()
        data = response.json()

        codigo = data.get("Codigo")
        if codigo != 0:
            descripcion = data.get("Descripcion", "sin descripción")
            raise RuntimeError(f"Error BCCh (código {codigo}): {descripcion}")
        return data
    
    def get_series(self, code: str, start: date, end: date) -> pd.DataFrame:
        """Descarga una serie y la devuelve como DataFrame limpio."""
        params = {
            "function": "GetSeries",
            "timeseries": code,
            "firstdate": start.strftime("%Y-%m-%d"),
            "lastdate": end.strftime("%Y-%m-%d"),
        }
        data = self._request(params)
        obs = data["Series"]["Obs"]

        df = pd.DataFrame(obs)
        df["indexDateString"] = pd.to_datetime(df["indexDateString"], format="%d-%m-%Y")  #Conversion valor fecha en string a formato datetime
        df["value"] = pd.to_numeric(df["value"], errors="coerce")   #Conversion valor a formato numerico, si no se puede convertir se asigna NaN
        df = df.rename(columns={"indexDateString": "fecha", "value": "valor"}) #Renombrar columnas a un formato mas facil de leer

        return (
            df[["fecha", "valor"]]
            .sort_values("fecha")
            .reset_index(drop=True)
        )
    
    def search_series(self, frequency: str = "DAILY") -> pd.DataFrame:
        """Devuelve el catálogo de series para una frecuencia dada."""
        if frequency not in self.VALID_FREQUENCIES:
            raise ValueError(
                f"frequency debe ser uno de {self.VALID_FREQUENCIES}, recibí: {frequency}"
            )
        data = self._request({"function": "SearchSeries", "frequency": frequency})
        return pd.DataFrame(data["SeriesInfos"])

