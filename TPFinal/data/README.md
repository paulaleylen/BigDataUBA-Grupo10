# Directorio de Datos

**⚠️ IMPORTANTE:** Esta carpeta NO se sube a Git (incluida en `.gitignore`)

Los datos son generados localmente ejecutando los scripts de descarga.

---

## Estructura

```
data/
├── raw/                    # Datos crudos originales (opcional, no usado actualmente)
├── external/               # Datos de APIs externas
│   ├── cftc/              # CFTC Commitments of Traders
│   │   └── cftc_features_2000_2025.csv (6,731 × 11)
│   └── gdelt/             # GDELT News Sentiment
│       ├── gdelt_v1_raw_2000_2013.csv
│       ├── gdelt_v2_raw_2015_2025.csv
│       └── sentiment_features_2000_2025.csv (6,731 × 10)
│
├── interim/               # Datos intermedios procesados
│   ├── commodities/       # 22 CSVs individuales (corn.csv, gold.csv, etc.)
│   ├── predictors/        # 7 CSVs macro (vix.csv, dxy.csv, sp500.csv, etc.)
│   ├── climate/           # Features climáticas (NOAA/NASA)
│   ├── bdi/               # Baltic Dry Index
│   │   └── bdi_features.csv (6,456 × 8)
│   ├── fred/              # FRED economic indicators
│   │   ├── fedfunds_features.csv
│   │   ├── dff_features.csv
│   │   ├── unrate_features.csv
│   │   ├── cpiaucsl_features.csv
│   │   ├── gdp_features.csv
│   │   └── fred_all_features.csv (9,470 × 33)
│   └── supply_demand/     # Fundamentals agrícolas (USDA)
│       ├── crop_conditions_all_features.csv (337 × 15)
│       └── government_stocks_ers_all_features.csv (23,834 × 9)
│
└── processed/             # Datasets finales listos para modelado
    ├── commodities_base_daily.csv (6,537 × 250) - Base Step 4
    └── features_final_modeling.csv (6,731 × 3,239) - Dataset final Step 9
```

---

## Cómo Generar los Datos

### Opción 1: Pipeline Automatizado (Recomendado)

```bash
make data
```

Ejecuta automáticamente:
- ✅ Fase 1: Commodities + Predictors + Climate
- ✅ Fase 2: CFTC + GDELT + BDI + Crop + Gov Stocks + FRED
- ✅ Fase 3: Procesamiento y consolidación

**Tiempo total:** ~20 minutos

### Opción 2: Scripts Individuales

```bash
# Fase 1: Core (6 min)
python -m src.data.download_commodities      # ~2 min
python -m src.data.download_predictors       # ~1 min
python -m src.data.download_climate          # ~3 min

# Fase 2: Features Académicas (15 min)
python -m src.data.download_cftc_cot         # ~2 min
python -m src.data.download_sentiment_gdelt  # ~10 min
python -m src.data.download_bdi              # ~10 seg
python -m src.data.download_crop_conditions  # ~30 seg
python -m src.data.download_government_stocks_ers  # ~20 seg
python -m src.data.download_fred             # ~30 seg

# Fase 3: Procesamiento (1 min)
python -m src.data.process                   # ~1 min
```

---

## Requisitos Previos

### API Keys (archivo `.env` en raíz del proyecto)

```bash
NASS_API_KEY=tu_key_aqui     # Para crop conditions
FRED_API_KEY=tu_key_aqui     # Para economic indicators
```

**Obtener keys (gratis):**
- NASS: https://quickstats.nass.usda.gov/api
- FRED: https://fred.stlouisfed.org/docs/api/api_key.html

### Archivos Manuales

- **BDI CSV:** Descargar de Investing.com → `data/external/bdi/baltic_dry_index.csv`

---

## Datasets Clave

### 1. `commodities_base_daily.csv` (Step 4)
- **Dimensiones:** 6,537 filas × 250 columnas
- **Período:** 2000-2025
- **Contenido:** Commodities + Predictors + Climate
- **Uso:** Baseline para comparación con features académicas

### 2. `features_final_modeling.csv` (Step 9)
- **Dimensiones:** 6,731 filas × 3,239 columnas
- **Período:** 2000-2025
- **Contenido:** Base + CFTC + GDELT + BDI + Crop + Gov Stocks + FRED
- **Uso:** Dataset final para LSTM y modelos predictivos

---

## Feature Counts por Step

| Step | Descripción | Features | Acumulado |
|------|-------------|----------|-----------|
| 4 | Baseline (Commodities + Predictors + Climate) | 3,186 | 3,186 |
| 5 | + CFTC Commitments of Traders | +11 | 3,197 |
| 6 | + GDELT News Sentiment | +10 | 3,207 |
| 7 | + Baltic Dry Index | +8 | 3,215 |
| 8 | + Crop Conditions (USDA NASS) | +15 | 3,230 |
| 9 | + Government Stocks (USDA ERS) | +9 | **3,239** ✅ |

**Nota:** Step 9 incluye también FRED economic indicators (33 features ya contadas en baseline).

---

## Limpieza de Datos

### Limpiar datos intermedios (mantener raw)
```bash
make clean
```

### Limpiar TODO (incluyendo raw data)
```bash
make clean-all
```

⚠️ Después de `clean-all`, necesitarás volver a ejecutar `make data` (~20 min).

---

## Troubleshooting

### Error: "NASS_API_KEY not found"
- Crear archivo `.env` en raíz con tu API key
- O comentar `download_crop_conditions` en Makefile

### Error: "BDI CSV not found"
- Descargar manualmente de Investing.com
- O comentar `download_bdi` en Makefile

### Error: "GDELT download muy lento"
- Normal, descarga ~20 años de datos
- Esperar ~10 minutos o ejecutar en background

### Make no funciona en Windows
- Usar PowerShell y ejecutar scripts manualmente
- O instalar `make` con Chocolatey: `choco install make`

---

## Documentación Relacionada

- **Data Dictionary:** `references/data_dictionary.md` - Descripción de todas las variables
- **Progreso Features:** `references/PROGRESO_FEATURES_ACADEMICAS.md` - Status detallado
- **Sources:** `references/sources.md` - Fuentes de datos originales
- **Notebooks:** `notebooks/2.0-feature-engineering/` - Análisis de features individuales

---

**Última actualización:** Diciembre 2025  
**Mantenedores:** Grupo JLP - UBA FCE
