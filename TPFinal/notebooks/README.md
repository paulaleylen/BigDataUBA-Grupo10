# Notebooks

Notebooks exploratorios organizados según convenciones de Cookiecutter Data Science.

## Nomenclatura

Los notebooks siguen el patrón: `<número>.<iniciales-creador>-<descripción-corta>.ipynb`

Ejemplo: `1.0-jqp-initial-exploration.ipynb`

### Numeración

- **0.x**: Notebooks de prueba y experimentación rápida
- **1.x**: Exploración inicial de datos (EDA)
- **2.x**: Feature engineering y preparación de datasets
  - 2.0-2.5: Features individuales (CFTC, GDELT, BDI, Crop, Gov Stocks)
  - 2.6: Merge final de todos los datasets
- **3.x**: Modelado y machine learning
  - 3.0-3.9: Modelos tradicionales
  - 3.10+: Walk-forward LSTM y modelos avanzados
- **4.x**: Evaluación y comparación de modelos
- **5.x**: Visualizaciones y reportes finales

## Estructura Actual

### Notebooks Disponibles

#### 1.0-exploratory/ - Exploración de Datos

1. **`1.0-initial-exploration.ipynb`**
   - Carga de datos de commodities y predictores
   - Análisis de cobertura temporal
   - Valores faltantes
   - Series temporales y distribuciones
   - **Usa:** `src.data.process`, `src.config`

#### 2.0-feature-engineering/ - Features Académicas

2. **`2.0-cftc-features.ipynb`**
   - CFTC Commitments of Traders (11 features)
   - Posiciones comerciales vs especuladoras
   - Open interest y ratios

3. **`2.1-gdelt-sentiment.ipynb`**
   - GDELT News Sentiment (10 features)
   - Tono y conteo de eventos
   - Batch download v1.0 + v2.0

4. **`2.2-bdi-features.ipynb`**
   - Baltic Dry Index (8 features)
   - Shipping costs proxy

5. **`2.3-crop-conditions.ipynb`**
   - USDA NASS Crop Conditions (15 features)
   - Good/Excellent percentages

6. **`2.4-government-stocks.ipynb`**
   - USDA ERS Government Stocks (9 features)
   - Ending stocks por commodity

7. **`2.5-fred-economic.ipynb`**
   - FRED Economic Indicators (33 features)
   - Fed Funds, CPI, GDP, Unemployment

8. **`2.6-final-dataset-preparation.ipynb`**
   - Merge de todos los features
   - Imputación de missing values
   - Dataset final: 6,731 × 3,239

#### 3.0-modeling/ - Machine Learning

9. **`3.10-walk-forward-lstm.ipynb`**
   - LSTM con walk-forward validation
   - Comparación Steps 4-9
   - Directional Accuracy metric

### Legacy

La carpeta `legacy/` contiene los notebooks originales del proyecto Base:
- `01_download_commodities.ipynb`
- `02_download_predictors.ipynb`
- `03_process_data.ipynb`

**No usar estos notebooks directamente.** La lógica ha sido refactorizada en módulos de `src/`.

## Uso

### Importar Módulos del Proyecto

```python
# En cualquier notebook
from src.data import download_commodities, download_predictors, process
from src.config import INTERIM_COMMODITIES_DIR, PROCESSED_DIR, FIGURES_DIR
```

### Ejecutar Pipeline Completo

```python
# Opción 1: Usar Makefile desde terminal
# !make data

# Opción 2: Ejecutar scripts individualmente
from src.data import (
    download_commodities, 
    download_predictors, 
    download_climate,
    download_cftc_cot,
    download_sentiment_gdelt,
    download_bdi,
    download_crop_conditions,
    download_government_stocks_ers,
    download_fred,
    process
)

# Fase 1: Core
commodities_data = download_commodities.main()
predictors_data = download_predictors.main()
climate_data = download_climate.main()

# Fase 2: Features académicas
cftc_data = download_cftc_cot.main()
gdelt_data = download_sentiment_gdelt.main()
# ... etc

# Fase 3: Procesamiento
df_final = process.main()
```

### Cargar Datos Procesados

```python
import pandas as pd
from src.config import PROCESSED_DIR, FINAL_MODELING_FILE

# Dataset final con todas las features (6,731 × 3,239)
df = pd.read_csv(FINAL_MODELING_FILE, parse_dates=['date'])

# O datasets intermedios
df_base = pd.read_csv(PROCESSED_DIR / 'commodities_base_daily.csv', parse_dates=['date'])
```

## Buenas Prácticas

### ✅ Hacer

- Usar funciones de `src/` en lugar de duplicar código
- Documentar análisis con Markdown explicativo
- Guardar figuras en `reports/figures/`
- Numerar notebooks secuencialmente según workflow
- Mantener notebooks cortos y enfocados (< 500 líneas)

### ❌ Evitar

- Código ETL complejo en notebooks (mover a `src/`)
- Hardcodear paths (usar `src.config`)
- Notebooks de 1000+ líneas
- Duplicar lógica que ya existe en `src/`
- Commitear notebooks con outputs grandes (limpiar antes de commit)

## Configuración de Kernel

Asegurarse de tener instalado el paquete del proyecto:

```bash
pip install -e .
```

Esto permite importar módulos de `src/` desde cualquier notebook.

## Referencias

- [Cookiecutter Data Science - Notebooks](https://drivendata.github.io/cookiecutter-data-science/#notebooks-are-for-exploration-and-communication)
- Convención de nomenclatura inspirada en [Fast.ai](https://docs.fast.ai/)
