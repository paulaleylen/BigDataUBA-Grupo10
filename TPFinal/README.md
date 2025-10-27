# TPFinal - Proyecto de Commodities

**Taller de Programación - UBA FCE | Grupo JLP**

Base de datos escalable de commodities y predictores macro para análisis y modelado. Estructura modular que facilita colaboración y mantenimiento.

## Overview

Pipeline automatizado que:

1. **Descarga** 22 commodities desde Yahoo Finance (granos, energía, metales)
2. **Descarga** 5 predictores macro (VIX, DXY, S&P500, tasas, índices)
3. **Procesa** y limpia automáticamente
4. **Genera** 216 features para ML (lags, rolling stats, returns)
5. **Exporta** dataset final: `commodities_base_daily.csv` (6,537×250, 25MB)

---

## Setup Inicial

### Primera vez trabajando en el proyecto:

```bash
# Activar entorno
conda activate ds

# Instalar paquete en modo editable
pip install -e .
```

**Qué hace:** Instala `src/` como paquete Python para poder importar: `from src.data import process`

### Generar la base de datos:

```bash
# Pipeline completo (ejecutar en orden)
python src/data/download_commodities.py  # ~2 min
python src/data/download_predictors.py   # ~1 min  
python src/data/process.py               # ~30 seg
```

**Output:**
- `data/interim/commodities/` → 22 CSVs individuales
- `data/interim/predictors/` → 5 CSVs individuales
- `data/processed/commodities_base_daily.csv` → **Base final** (25 MB)

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
│   ├── interim/                   # Datos intermedios procesados
│   │   ├── commodities/           # 22 archivos CSV (corn.csv, gold.csv, etc.)
│   │   └── predictors/            # 6 archivos CSV (vix.csv, dxy.csv, etc.)
│   └── processed/                 # Datos finales listos para modelado
│       └── commodities_base_daily.csv  # Dataset final con 250 columnas
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
│       ├── download_commodities.py   # Descarga commodities
│       ├── download_predictors.py    # Descarga predictores
│       └── process.py                # Procesa y genera features
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

Ejecutá estos comandos **en orden**:

```bash
# 1. Descargar commodities (22 commodities desde Yahoo Finance)
python src/data/download_commodities.py

# 2. Descargar predictores (VIX, DXY, S&P 500, etc.)
python src/data/download_predictors.py

# 3. Procesar todo y generar features
python src/data/process.py
```

**Salida esperada:**
- `data/interim/commodities/` → 22 archivos CSV
- `data/interim/predictors/` → 6 archivos CSV
- `data/processed/commodities_base_daily.csv` → **Dataset final** (25 MB, 6,537 filas × 250 columnas)

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
