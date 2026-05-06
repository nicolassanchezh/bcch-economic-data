# BCCh Economic Data

Pipeline de extracción, almacenamiento y visualización de series económicas
del Banco Central de Chile (IPC, TPM, tipo de cambio observado).

## Setup

1. Clonar el repo
2. Crear entorno virtual: `python -m venv .venv`
3. Activar: `.venv\Scripts\Activate.ps1` (Windows) o `source .venv/bin/activate` (macOS/Linux)
4. Instalar dependencias: `pip install -r requirements.txt`
5. Copiar `.env.example` a `.env` y completar credenciales del BCCh

## Estructura

- `src/client/`: cliente HTTP para la API del BCCh
- `src/extract/`: lógica de ingesta
- `src/storage/`: persistencia
- `src/analysis/`: transformaciones y cálculos
- `config/series.yaml`: catálogo de series a seguir