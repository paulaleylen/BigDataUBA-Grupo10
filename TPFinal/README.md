# TPFinal - Proyecto de Commodities

**Taller de Programación - UBA FCE | Grupo JLP**

Base de datos escalable de commodities y predictores macro para análisis y modelado. Estructura modular que facilita colaboración y mantenimiento.

## Overview

Pipeline automatizado que:

1. **Descarga** 22 commodities desde Yahoo Finance (granos, energía, metales)
2. **Descarga** 7 predictores macro (VIX, DXY, S&P500, tasas, índices)
3. **Descarga** datos climáticos (NOAA/NASA APIs)
4. **Descarga** features académicas:
   - CFTC Commitments of Traders (11 features)
   - GDELT News Sentiment (10 features, 1979-2025, 46 años)
     - Pre-2014: GDELT 1.0 (archivo MASTERREDUCEDV2.TXT, descarga manual)
     - Post-2014: GDELT 2.0 (BigQuery API, descarga automática)
   - Baltic Dry Index (8 features)
   - Crop Conditions USDA (15 features)
   - Government Stocks USDA ERS (9 features)
   - FRED Economic Indicators (33 features)
5. **Procesa** y limpia automáticamente
6. **Genera** 3,239 features para ML (lags, rolling stats, returns, sentiment, fundamentals)
7. **Exporta** dataset final: `features_final_modeling.csv` (6,731×3,239)

---

## Setup Inicial

### Primera vez trabajando en el proyecto:

```bash
# Instalar paquete en modo editable
pip install -e .
```

**Qué hace:** Instala `src/` como paquete Python para poder importar: `from src.data import process`

### Generar la base de datos:

**Opción 1: Pipeline completo automatizado (recomendado)**

```bash
make data  # Ejecuta TODOS los scripts en orden correcto (~15-20 min)
```

**Opción 2: Ejecutar manualmente**

```bash
# Fase 1: Datos Core
python -m src.data.download_commodities      # ~2 min
python -m src.data.download_predictors       # ~1 min
python -m src.data.download_climate          # ~3 min

# Fase 2: Features Académicas
python -m src.data.download_cftc_cot         # ~2 min
python -m src.data.download_sentiment_gdelt --bigquery  # ~30 seg (GDELT 2.0 vía BigQuery)
# NOTA: GDELT 1.0 pre-2014 requiere descarga manual de MASTERREDUCEDV2.TXT
python -m src.data.download_bdi              # ~10 seg (requiere CSV manual)
python -m src.data.download_crop_conditions  # ~30 seg (requiere NASS_API_KEY)
python -m src.data.download_government_stocks_ers  # ~20 seg
python -m src.data.download_fred             # ~30 seg (requiere FRED_API_KEY)

# Fase 3: Procesamiento
python -m src.data.process                   # ~1 min
```

**Output:**
- `data/interim/commodities/` → 22 CSVs individuales
- `data/interim/predictors/` → 7 CSVs macro
- `data/interim/climate/` → Features climáticas
- `data/external/cftc/` → CFTC features (11 cols)
- `data/external/sentiment/` → GDELT sentiment consolidado (10 cols, 1979-2025)
  - `sentiment_features_1979_2025.csv` (16,753 días, 46.9 años)
- `data/interim/bdi/` → BDI features (8 cols)
- `data/interim/supply_demand/` → Crop + Gov Stocks (24 cols)
- `data/interim/fred/` → Economic indicators (33 cols)
- `data/processed/features_final_modeling.csv` → **Base final** (6,731×3,239)

### Explorar:

Notebooks en `notebooks/1.0-exploratory/`:
- `1.0-initial-exploration.ipynb` - EDA básico
- `2.0-correlation-analysis.ipynb` - Correlaciones y heatmaps

---

```
TPFinal/
│
├── data/                          # TODOS LOS DATOS (no se suben a Git)
│   ├── raw/                       # Datos crudos descargados
│   ├── external/                  # Datos de APIs externas
│   │   ├── cftc/                  # CFTC Commitments of Traders
│   │   └── sentiment/             # GDELT News Sentiment (1979-2025, consolidado)
│   ├── interim/                   # Datos intermedios procesados
│   │   ├── commodities/           # 22 archivos CSV (corn.csv, gold.csv, etc.)
│   │   ├── predictors/            # 7 archivos CSV (vix.csv, dxy.csv, etc.)
│   │   ├── climate/               # Features climáticas (NOAA/NASA)
│   │   ├── bdi/                   # Baltic Dry Index features
│   │   ├── fred/                  # FRED economic indicators
│   │   └── supply_demand/         # Crop conditions + Gov stocks (USDA)
│   └── processed/                 # Datos finales listos para modelado
│       └── features_final_modeling.csv  # Dataset final con 3,239 columnas
│
├── notebooks/                     # NOTEBOOKS PARA EXPLORACIÓN
│   ├── 1.0-exploratory/           # Notebooks de análisis
│   │   ├── 1.0-initial-exploration.ipynb
│   │   └── 2.0-correlation-analysis.ipynb
│   └── legacy/                    # Notebooks antiguos (referencia)
│
├── src/                           # CÓDIGO REUTILIZABLE
│   ├── config.py                  # Configuración centralizada (IMPORTANTE!)
│   └── data/                      # Módulos de datos
│       ├── download_commodities.py           # Descarga commodities (Yahoo)
│       ├── download_predictors.py            # Descarga predictores macro (Yahoo)
│       ├── download_climate.py               # Descarga clima (NOAA/NASA)
│       ├── download_cftc_cot.py              # CFTC Commitments of Traders
│       ├── download_sentiment_gdelt.py       # GDELT News Sentiment
│       ├── download_bdi.py                   # Baltic Dry Index
│       ├── download_crop_conditions.py       # Crop Conditions (NASS API)
│       ├── download_government_stocks_ers.py # Gov Stocks (USDA ERS)
│       ├── download_fred.py                  # Economic indicators (FRED API)
│       └── process.py                        # Procesa y genera features
│
├── reports/                       # VISUALIZACIONES
│   └── figures/                   # Gráficos generados (.png)
│
├── references/                    # DOCUMENTACIÓN
│   ├── data_dictionary.md         # Diccionario de variables
│   └── sources.md                 # Fuentes de datos
│
├── setup.py                       # Instalación del paquete
├── requirements.txt               # Dependencias Python
└── Makefile                       # Comandos automatizados (Windows: no funciona)
```

---

## 🚀 Cómo Empezar (Guía Paso a Paso)

### Paso 1: Instalar el paquete

Abrí una terminal en esta carpeta y ejecutá:

```bash
# Activar tu entorno conda
conda activate ds

# Instalar el paquete en modo editable
pip install -e .
```

**¿Por qué esto?** Instala el código de `src/` como un paquete Python, permitiéndote hacer `from src.data import process` desde cualquier notebook.

---

### Paso 2: Descargar los datos

**Opción recomendada: Pipeline automatizado**

```bash
make data
```

Esto ejecuta automáticamente:
- ✅ Fase 1: Commodities + Predictors + Climate (~6 min)
- ✅ Fase 2: CFTC + GDELT (BigQuery) + BDI + Crop + Gov Stocks + FRED (~5 min)
- ✅ Fase 3: Procesamiento y consolidación GDELT 1.0+2.0 (~3 min)
- ✅ Fase 4: Feature engineering final (~1 min)

**Opción manual:** Ver sección "Generar la base de datos" arriba

**Salida esperada:**
- `data/interim/` → Múltiples carpetas con features intermedias
- `data/external/` → CFTC y GDELT (sentiment consolidado 1979-2025)
- `data/processed/features_final_modeling.csv` → **Dataset final** (6,731 × 3,239)

**Archivos GDELT generados:**
- `sentiment_daily_1979_2025_merged.csv` - Datos diarios agregados (GDELT 1.0 + 2.0)
- `sentiment_features_1979_2025.csv` - Features finales para modelado

**Nota:** Necesitás API keys en `.env` para:
- `NASS_API_KEY` (crop conditions)
- `FRED_API_KEY` (economic indicators)

---

### Paso 3: Explorar con notebooks

Abrí los notebooks en orden:

1. **`notebooks/1.0-exploratory/1.0-initial-exploration.ipynb`**
   - Carga datos
   - Analiza cobertura temporal
   - Visualiza series de precios

2. **`notebooks/1.0-exploratory/2.0-correlation-analysis.ipynb`**
   - Matrices de correlación
   - Heatmaps
   - Relaciones commodities-predictores

**Los notebooks son "delgados":** Solo llaman funciones de `src/`, no repiten código.

---

## ⚙️ Archivo de Configuración (MUY IMPORTANTE)

Todo se configura en **`src/config.py`**. Este archivo define:

### 📍 Paths del proyecto

```python
BASE_DIR = Path(__file__).resolve().parents[1]  # Raíz del proyecto
DATA_DIR = BASE_DIR / 'data'
INTERIM_COMMODITIES_DIR = INTERIM_DIR / 'commodities'
PROCESSED_DIR = DATA_DIR / 'processed'
FIGURES_DIR = REPORTS_DIR / 'figures'
```

**Beneficio:** Los paths se calculan automáticamente, no importa dónde esté el proyecto.

### Commodities a descargar

```python
COMMODITIES_TICKERS = {
    # Granos
    'Corn': 'ZC=F',
    'Soybeans': 'ZS=F',
    'Wheat': 'ZW=F',
    
    # Energía
    'Crude_Oil': 'CL=F',
    'Natural_Gas': 'NG=F',
    
    # Metales
    'Gold': 'GC=F',
    'Silver': 'SI=F',
    'Copper': 'HG=F',
    
    # ... total 22 commodities
}
```

### Predictores a descargar

```python
PREDICTORS_TICKERS = {
    'VIX': '^VIX',                # Volatilidad
    'DXY': 'DX-Y.NYB',            # Índice dólar
    'SP500': '^GSPC',             # S&P 500
    'Treasury_10Y': '^TNX',       # Tasas 10 años
    'Energy_Index': '^GSPE',      # Sector energía
}
```

---

## Cómo Modificar el Proyecto

### Agregar un nuevo commodity

**Paso 1:** Editá `src/config.py`, agregá el ticker:

```python
COMMODITIES_TICKERS = {
    # ... existentes ...
    'Rice': 'ZR=F',  # Agregar nuevo commodity
}
```

**Paso 2:** Regenerá la base:

```bash
python src/data/download_commodities.py  # Descarga solo los nuevos
python src/data/process.py               # Regenera base completa
```

---

### Agregar un nuevo predictor

**Paso 1:** Editá `src/config.py`:

```python
PREDICTORS_TICKERS = {
    # ... existentes ...
    'Bitcoin': 'BTC-USD',  # Agregar nuevo predictor
}
```

**Paso 2:** Regenerá:

```bash
python src/data/download_predictors.py
python src/data/process.py
```

---

### Modificar features generadas

En `src/data/process.py`, función `main()`, cambiá los parámetros:

```python
# Cambiar lags (línea ~350)
df_base = add_lag_features(df_base, price_cols, lags=[1, 5, 10, 20])

# Cambiar ventanas rolling (línea ~355)
df_base = add_rolling_features(df_base, price_cols, windows=[14, 30, 60])

# Cambiar períodos de retorno (línea ~360)
df_base = add_return_features(df_base, price_cols, periods=[1, 5, 10, 20])
```

Regenerá:

```bash
python src/data/process.py  # Solo este, no hace falta redescargar
```

---

## Filosofía del Proyecto

### Por qué estructura modular (no solo notebooks)

**Antes (solo notebooks):**
- Código duplicado en múltiples notebooks
- Si hay un bug → arreglar en N lugares
- Difícil de mantener y colaborar

**Ahora (src/ + notebooks):**
- Código de descarga/limpieza en `src/` (1 sola versión)
- Notebooks solo **usan** el código, no lo duplican
- Cambios centralizados → todos se benefician

### Qué va en `src/` vs notebooks

**En `src/`:**
- Descarga y limpieza de datos
- Feature engineering genérico
- Funciones que se reutilizan

**En notebooks:**
- Exploración y visualización
- Análisis específicos
- Prototipos de modelos
- Reportes

**Regla:** Si usaste el mismo código en 2+ notebooks → movelo a `src/`

---

## Workflow del Equipo

### Cuando trabajás en un análisis nuevo:

1. **Actualizá tu copia:**
   ```bash
   git pull
   python src/data/process.py  # Si hubo cambios en src/
   ```

2. **Creá tu notebook:**
   ```bash
   # Convención: [número].[orden]-[descripción].ipynb
   notebooks/1.0-exploratory/3.0-mi-analisis.ipynb
   ```

3. **Importá desde src:**
   ```python
   from src.data import process
   from src.config import PROCESSED_DIR, FIGURES_DIR
   import pandas as pd
   
   df = pd.read_csv(PROCESSED_DIR / 'commodities_base_daily.csv')
   ```

4. **Si creaste una función útil → movela a `src/`** para que el equipo la use

---

### Cuando modificás código en `src/`:

1. **Editá el archivo** (`src/data/process.py`, `src/config.py`, etc.)

2. **Probá en un notebook:**
   ```python
   import importlib
   from src.data import process
   importlib.reload(process)  # Importante si ya lo importaste
   
   result = process.tu_funcion()
   ```

3. **Regenerá la base:**
   ```bash
   python src/data/process.py
   ```

4. **Commiteá:**
   ```bash
   git add src/
   git commit -m "feat: agregar función para limpiar outliers"
   git push
   ```

5. **Avisá al equipo** en el grupo para que hagan `git pull`

---

## Troubleshooting

### Error: `ModuleNotFoundError: No module named 'src'`

**Solución:** No instalaste el paquete. Ejecutá:

```bash
pip install -e .
```

---

### Error: `FileNotFoundError` al guardar gráficos

**Causa:** El directorio `reports/figures/` no existe.

**Solución:** Los directorios se crean automáticamente en `src/config.py`. Si no funcionó, ejecutá:

```bash
mkdir -p reports/figures
```

---

### Los datos no se descargan

**Causa:** Problemas de conexión con Yahoo Finance.

**Solución:** 
1. Verificá tu conexión a internet
2. Yahoo Finance a veces bloquea requests. Esperá unos minutos e intentá de nuevo.

---

### Warning: `DataFrame is highly fragmented`

**No es un error.** Es solo un warning de performance de pandas. Los datos se procesan correctamente.

---

## Recursos de Aprendizaje

Para entender mejor la estructura:

- **Cookiecutter Data Science:** https://drivendata.github.io/cookiecutter-data-science/
- **Packaging Python projects:** https://packaging.python.org/tutorials/packaging-projects/

---

## FAQ del Equipo

### Yahoo Finance falla al descargar, ¿qué hago?

A veces Yahoo bloquea requests. Esperá 5 min e intentá de nuevo. Si persiste, verificá el ticker en https://finance.yahoo.com (puede estar delisted).

---

### ¿Cómo agrego datos de otra fuente (no Yahoo)?

1. Creá `src/data/download_mifuente.py` siguiendo el patrón existente
2. Guardá CSVs en `data/interim/mifuente/`
3. Modificá `src/data/process.py` para cargar tus archivos

---

### Alguien cambió `src/config.py`, ¿qué hago?

```bash
git pull
python src/data/download_commodities.py  # Si cambiaron tickers
python src/data/download_predictors.py   # Si cambiaron tickers
python src/data/process.py               # Siempre
```

---

### ¿Cómo manejo merge conflicts en notebooks?

Los notebooks son JSONs, los conflicts son complicados. **Estrategia:**
1. Evitá editar el mismo notebook simultáneamente
2. Si hay conflict: `git checkout --theirs archivo.ipynb` y rehacé cambios
3. Mejor: notebooks separados y luego consolidar

---

## Dataset Final

El archivo `data/processed/commodities_base_daily.csv` contiene:

- **6,537 filas** (días de trading, desde que hay datos disponibles en Yahoo Finance)
- **250 columnas:**
  - 1 columna `date`
  - 22 commodities (precios de cierre)
  - 5 predictores (VIX, DXY, SP500, Treasury_10Y, Energy_Index)
  - 6 features temporales (year, month, quarter, day_of_week, etc.)
  - 54 lags (1 y 7 días para cada precio)
  - 108 rolling statistics (media móvil y desviación para ventanas 7 y 30)
  - 54 retornos porcentuales (1 y 7 días)

**Tamaño:** ~25 MB

---

## Créditos

**UBA - Facultad de Ciencias Económicas**  
Taller de Programación | Grupo 10

**Estructura:** [Cookiecutter Data Science](https://drivendata.github.io/cookiecutter-data-science/)
