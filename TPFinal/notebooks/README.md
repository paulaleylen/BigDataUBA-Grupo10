# Notebooks

Notebooks exploratorios organizados según convenciones de Cookiecutter Data Science.

## Nomenclatura

Los notebooks siguen el patrón: `<número>.<iniciales-creador>-<descripción-corta>.ipynb`

Ejemplo: `1.0-jqp-initial-exploration.ipynb`

### Numeración

- **0.x**: Notebooks de prueba y experimentación rápida
- **1.x**: Exploración inicial de datos
- **2.x**: Análisis específicos (correlaciones, tendencias, etc.)
- **3.x**: Feature engineering y preparación de datos
- **4.x**: Modelado y machine learning
- **5.x**: Visualizaciones y reportes finales

## Estructura Actual

### Notebooks Disponibles

1. **`1.0-initial-exploration.ipynb`**
   - Carga de datos de commodities y predictores
   - Análisis de cobertura temporal
   - Valores faltantes
   - Series temporales y distribuciones
   - **Usa:** `src.data.process`, `src.config`

2. **`2.0-correlation-analysis.ipynb`**
   - Matrices de correlación
   - Identificación de relaciones fuertes
   - Análisis de predictores vs commodities
   - Clustermap con agrupación jerárquica
   - **Usa:** `src.data.process`, `src.config`

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
# Descarga de commodities
commodities_data = download_commodities.main()

# Descarga de predictores
predictors_data = download_predictors.main()

# Procesamiento y feature engineering
df_final = process.main()
```

### Cargar Datos Procesados

```python
import pandas as pd
from src.config import PROCESSED_DIR

df = pd.read_csv(PROCESSED_DIR / 'commodities_base_daily.csv', parse_dates=['date'])
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
