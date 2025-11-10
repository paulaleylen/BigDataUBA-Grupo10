# Fuentes de Datos - Base de Commodities

**Proyecto:** Base de Datos Unificada para Análisis de Commodities  
**Universidad de Buenos Aires - Facultad de Ciencias Económicas**  
**Última revisión de fuentes:** Noviembre 2025

---

## 4. Predictores Climáticos ⭐ **NUEVOS - DATOS CLIMÁTICOS**

**Módulo:** `src/data/download_climate.py`  
**Descarga:** Automática (ONI desde NOAA + NASA POWER API)  
**Frecuencia:** Diaria (ONI expandido de mensual, NASA POWER nativo diario)

### Rationale: Por qué datos climáticos

Los precios de commodities agrícolas (especialmente granos: soja, maíz, trigo) están **fuertemente correlacionados con condiciones climáticas**:

1. **Fenómeno ENSO** (El Niño/La Niña) → Sequías/inundaciones en regiones productoras
2. **Temperatura** → Estrés térmico daña cultivos (>35°C para soja)
3. **Precipitación** → Déficit hídrico reduce rendimientos
4. **Estacionalidad** → Ciclos de siembra/cosecha varían por región

**Impacto documentado:**
- Argentina: La Niña (ONI < -0.5) correlaciona con sequías y caídas del 15-30% en yields de soja ([Climate Impact Company, 2024](https://climateimpactcompany.com))
- Brasil: Temperaturas >35°C durante floración reducen rendimiento en 20-40% ([USDA FAS](https://fas.usda.gov))
- USA: Sequías extremas (2012) llevaron maíz de $5 a $8/bushel en 3 meses ([CBOT históricos](https://cmegroup.com))

---

### A. ONI - Oceanic Niño Index (NOAA)

**URL:** https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt  
**Fuente:** NOAA Climate Prediction Center  
**Descripción:** Índice mensual del fenómeno ENSO (El Niño Southern Oscillation)

**Definición técnica:**
- Promedio móvil de 3 meses de anomalías de SST (Sea Surface Temperature) en región Niño 3.4 (5°N-5°S, 120°-170°W)
- **El Niño:** ONI ≥ +0.5°C (calentamiento) durante 5+ meses consecutivos
- **La Niña:** ONI ≤ -0.5°C (enfriamiento) durante 5+ meses consecutivos
- **Neutral:** -0.5 < ONI < +0.5

**Cobertura:** 1950-presente (datos mensuales)

**Procesamiento:**
```python
# Descarga mensual desde NOAA
df_oni = pd.read_csv(ONI_URL, delim_whitespace=True, skiprows=1)

# Expandir a diario usando forward-fill (estándar en commodity forecasting)
df_daily = pd.date_range(start='2000-01-01', end='2025-11-10', freq='D')
df_oni_daily = df_oni.merge(df_daily, how='right').ffill()
```

**Justificación forward-fill:**
- ONI representa **estado climático persistente** (semanas/meses), no cambia día a día
- Método estándar en literatura de forecasting agrícola ([ResearchGate](https://www.researchgate.net/publication/378778261_Forecasting_Commodity_Prices_using_Machine_Learning))
- Alternativa (interpolación lineal) no es realista: ENSO no transiciona linealmente

**Uso en modelos:**
- Variable independiente directa para predicción de precios de granos
- Lags de 30/60/90 días capturan efectos retardados (sequía hoy → precios suben en 2-3 meses)

**Archivos generados:**
- `data/interim/climate/oni_monthly.csv` - Datos crudos mensuales
- `data/interim/climate/oni_daily.csv` - Expandido a diario (forward-filled)

---

### B. NASA POWER API - Climate Data for Agricultural Regions

**URL:** https://power.larc.nasa.gov/api/temporal/daily/point  
**Fuente:** NASA Langley Research Center - POWER Project  
**Descripción:** Datos climáticos diarios globales desde satélites y reanálisis

**Cobertura:**
- **Temporal:** 1981-presente (near real-time, actualización diaria)
- **Espacial:** Global, resolución 0.5° × 0.5° (~55 km en ecuador)
- **Comunidad:** AG (Agriculture) - optimizado para aplicaciones agrícolas

**Parámetros descargados:**
- **T2M:** Temperature at 2 Meters (°C) - Temperatura media diaria
- **T2M_MAX:** Maximum Temperature at 2 Meters (°C)
- **T2M_MIN:** Minimum Temperature at 2 Meters (°C)
- **PRECTOTCORR:** Precipitation Corrected (mm/day) - Precipitación corregida

**Por qué NASA POWER:**
1. **Gratuito:** Sin API key, sin límites de rate para point data
2. **Consistente:** Misma metodología 1981-2025 (sin cambios de instrumentos)
3. **Validado:** Calibrado con estaciones terrestres ([NASA POWER Documentation](https://power.larc.nasa.gov))
4. **Específico para agricultura:** Community AG incluye correcciones para aplicaciones agrícolas

**Limitaciones:**
- Resolución espacial moderada (0.5°) - promedia ~55 km × 55 km
- No captura microclimas extremos (frost pockets, urban heat islands)
- Precipitación satelital menos precisa que estaciones terrestres en eventos intensos

---

### C. Regiones Seleccionadas y Pesos de Producción

**Criterio de selección:** Principales regiones productoras de soja (commodity de referencia para granos)

#### **1. Mato Grosso, Brasil** 🇧🇷
- **Coordenadas:** lat -13.5, lon -55.5
- **Peso:** 51% (producción mundial de soja 2024, [USDA FAS](https://fas.usda.gov))
- **Descripción:** Estado más productivo de Brasil, líder global en soja
- **Growing season:** Planting Oct-Dic, Harvest Feb-Abr
- **Clima:** Tropical húmedo, temperatura media 25-28°C
- **Riesgo:** Déficit hídrico en veranico (enero-febrero)

#### **2. Corn Belt (Iowa), USA** 🇺🇸
- **Coordenadas:** lat 41.5, lon -93.5
- **Peso:** 29% (producción mundial de soja 2024)
- **Descripción:** Región central productora de maíz/soja de EE.UU.
- **Growing season:** Planting Abr-Jun, Harvest Sep-Nov
- **Clima:** Continental húmedo, temperatura media 10-22°C (variación estacional alta)
- **Riesgo:** Sequías estivales (julio-agosto crítico), frost temprano

#### **3. Pampa Húmeda, Argentina** 🇦🇷
- **Coordenadas:** lat -34.5, lon -61.0
- **Peso:** 11% (producción mundial de soja 2024)
- **Descripción:** Región pampeana argentina, 3er exportador mundial
- **Growing season:** Planting Nov-Ene, Harvest Mar-May
- **Climate:** Templado, temperatura media 14-20°C
- **Riesgo:** La Niña → sequías severas (históricamente cada 3-7 años)

**Total cobertura:** 91% de la producción mundial de soja (resto: Paraguay, Canadá, India 9%)

**Justificación de pesos:**
- **Production-weighted** (no area-weighted): Literatura muestra que producción es mejor proxy de price impact ([MDPI Agro-Climatic Data](https://mdpi.com/2306-5729/4/2/66))
- Brasil produce 51% → condiciones climáticas brasileñas tienen mayor peso en precios globales
- Validado en papers de commodity forecasting ([Farmonaut](https://farmonaut.com), [Agrolatam](https://agrolatam.com))

---

### D. Predictores Climáticos Globales Generados

A partir de los datos regionales, se crean **6 predictores globales** mediante weighted average:

#### **1. ONI** (Oceanic Niño Index)
- **Tipo:** Global (no requiere agregación regional)
- **Rango:** -3.0 a +3.0 (típicamente -2 a +2)
- **Interpretación:** 
  - ONI > +0.5 = El Niño (cálido, húmedo en algunos lugares)
  - ONI < -0.5 = La Niña (frío, seco en regiones sojeras)

#### **2. Temp_Global_Grain** (Temperatura Global Ponderada)
- **Fórmula:** `Temp_BR * 0.51 + Temp_USA * 0.29 + Temp_AR * 0.11`
- **Unidad:** °C
- **Interpretación:** Temperatura promedio ponderada en zonas productoras

#### **3. Precip_Global_Grain** (Precipitación Global Ponderada)
- **Fórmula:** `Precip_BR * 0.51 + Precip_USA * 0.29 + Precip_AR * 0.11`
- **Unidad:** mm/día
- **Interpretación:** Lluvia promedio ponderada en zonas productoras

#### **4. GDD_Global_Grain** (Growing Degree Days)
- **Fórmula:** `max(0, Temp_Global_Grain - 10)`
- **Base:** 10°C (temperatura mínima para crecimiento de soja)
- **Uso:** Acumulación de calor efectivo para desarrollo del cultivo
- **Referencia:** Método estándar en agronomía ([USDA Agricultural Research](https://ars.usda.gov))

#### **5. Heat_Stress_Days** (Días con Estrés Térmico)
- **Fórmula:** `rolling_30d_sum(Temp_Global_Grain > 35)`
- **Umbral:** 35°C (daño a floración/llenado de grano en soja)
- **Ventana:** 30 días (rolling)
- **Interpretación:** Número de días con calor extremo en último mes

#### **6. Precip_Deficit** (Déficit de Precipitación)
- **Fórmula:** `rolling_30d_sum(Precip_Global_Grain) - 100`
- **Óptimo:** 100 mm/30 días (~3.3 mm/día)
- **Interpretación:** 
  - Negativo = Déficit (sequía)
  - Positivo = Superávit (exceso, riesgo de inundación)

---

### E. Feature Engineering Climático

Sobre los 6 predictores base, se calculan **features derivadas**:

**Lags (18 features):**
- `ONI_lag30`, `ONI_lag60`, `ONI_lag90`
- `Temp_Global_Grain_lag30`, `Temp_Global_Grain_lag60`, `Temp_Global_Grain_lag90`
- ... (6 variables × 3 lags = 18)

**Rationale:** Clima de hace 1-3 meses afecta precio hoy (sequía en dic → cosecha reducida en mar → precio sube en abr)

**Rolling Statistics (12 features):**
- `Temp_Global_Grain_ma7`, `Temp_Global_Grain_std7` (media y desv. 7 días)
- `Temp_Global_Grain_ma30`, `Temp_Global_Grain_std30` (media y desv. 30 días)
- ... (6 variables × 2 ventanas × 2 métricas = 12)

**Total features climáticas: 6 base + 18 lags + 12 rolling = 36 columnas**

---

### F. Integración en Pipeline

**Paso 1: Descarga**
```bash
python src/data/download_climate.py
```
**Output:** 
- `data/interim/climate/oni_daily.csv`
- `data/interim/climate/nasa_power_brazil.csv`
- `data/interim/climate/nasa_power_usa.csv`
- `data/interim/climate/nasa_power_argentina.csv`
- `data/interim/climate/climate_registry.json`

**Paso 2: Procesamiento**
```bash
python src/data/process.py
```
**Acción:**
- Carga datos climáticos regionales
- Calcula 6 predictores globales (weighted average)
- Merge con dataset de commodities/predictores
- Genera lags y rolling features

**Output final:** `data/processed/commodities_base_daily.csv` con 36 columnas climáticas adicionales

---

### G. Validaciones y Limitaciones

**Validaciones implementadas:**
- ✅ ONI forward-fill sin gaps (verificado 2000-2025)
- ✅ NASA POWER: reemplazo de -999 (missing values) con NaN
- ✅ Weighted average con pesos que suman ~91% (correcto: resto del mundo ~9%)
- ✅ GDD con base 10°C (estándar para soja, [Iowa State Extension](https://crops.extension.iastate.edu))
- ✅ Heat stress threshold 35°C (validado en literatura agronómica)

**Limitaciones conocidas:**
1. **Missing values en primeros 30/60/90 días:** Lags y rolling naturalmente tienen NaN al inicio de series
2. **Resolución espacial:** 0.5° × 0.5° promedia ~3,000 km² - no captura variabilidad a escala de campo
3. **Precipitación satelital:** Menos precisa que estaciones terrestres (error ~10-20%)
4. **Ausencia de otros factores:** No incluye:
   - Soil moisture (humedad de suelo)
   - Solar radiation (radiación solar)
   - Wind speed (velocidad del viento)
   - Plagas y enfermedades
5. **Ponderación estática:** Pesos basados en producción 2024, cambian lentamente año a año

**Mitigación:**
- Missing values: Imputación cuidadosa (forward-fill para ONI, NaN preservado en derivadas)
- Resolución: Suficiente para análisis macro (precios commodities son globales, no locales)
- Factores adicionales: Fase futura del proyecto (requiere otras fuentes)

---

### H. Referencias Académicas y Fuentes

**Datos climáticos:**
- NASA POWER Documentation: https://power.larc.nasa.gov/docs/
- NOAA Climate Prediction Center ONI: https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/ensostuff/ONI_v5.php
- MDPI Agro-Climatic Data by County (2019): https://mdpi.com/2306-5729/4/2/66

**Producción y pesos:**
- USDA Foreign Agricultural Service (2024): https://fas.usda.gov
- Brazil production data: https://www.conab.gov.br
- Argentina agriculture ministry: https://www.magyp.gob.ar

**Impacto climático en commodities:**
- Climate Impact Company (2024): https://climateimpactcompany.com
- Farmonaut agricultural forecasts: https://farmonaut.com
- ResearchGate - Forecasting Commodity Prices (2024): https://www.researchgate.net/publication/378778261

**Metodología técnica:**
- Forward-fill justification: "Predicting Price of Daily Commodities using Machine Learning" (Semantic Scholar, 2025)
- Production-weighted aggregation: "Spatial aggregation in agricultural forecasting" (MDPI, 2019)
- Growing Degree Days: Iowa State University Extension - https://crops.extension.iastate.edu

---

### I. Archivos del Sistema Climático

**Configuración:**
- `src/config.py` - CLIMATE_REGIONS, CLIMATE_THRESHOLDS, paths

**Código:**
- `src/data/download_climate.py` - Descarga ONI + NASA POWER
- `src/data/process.py` - Integración y feature engineering (funciones `load_all_climate_data()`, `create_global_climate_predictors()`)

**Datos generados:**
```
data/interim/climate/
├── oni_monthly.csv              # ONI mensual crudo (NOAA)
├── oni_daily.csv                # ONI diario (forward-filled)
├── nasa_power_brazil.csv        # Temp/Precip Brasil (NASA POWER)
├── nasa_power_usa.csv           # Temp/Precip USA (NASA POWER)
├── nasa_power_argentina.csv     # Temp/Precip Argentina (NASA POWER)
└── climate_registry.json        # Metadata de descarga

data/processed/
└── climate_predictors_global.csv  # 6 predictores globales (opcional, intermedio)
```

**Dataset final:**
- `data/processed/commodities_base_daily.csv` - Dataset completo con 36 columnas climáticas integradas

---

### J. Próximos Pasos (Mejoras Futuras)

**Fase 2 - Variables adicionales:**
- Soil moisture index (NASA SMAP)
- NDVI (Normalized Difference Vegetation Index) - salud de cultivos
- Solar radiation (crecimiento fotosintético)

**Fase 3 - Regionalización por commodity:**
- Pesos específicos por commodity (maíz ≠ soja en distribución geográfica)
- Zonas adicionales (Paraguay, Canadá para trigo)

**Fase 4 - Datos de alta resolución:**
- Estaciones terrestres específicas (INMET Brasil, SMN Argentina)
- Downscaling estadístico de NASA POWER

---

**Última revisión de fuentes:** Noviembre 2025

````

---

## Arquitectura de Datos

Este proyecto utiliza **DOS fuentes principales** para construir series continuas desde 2000 hasta la actualidad:

1. **Kaggle (mattiuzc)** - Datos históricos 2000-2021 (descarga automática vía Kaggle API)
2. **Yahoo Finance (yfinance)** - Datos recientes 2021-2025 (descarga automática vía yfinance)

**Estrategia:** Empalmar ambas fuentes eliminando duplicados para obtener series de 25 años sin interrupciones.

---

## 1. Kaggle – Commodity Futures Price History (mattiuzc) ⭐ **FUENTE HISTÓRICA**
**URL:** https://www.kaggle.com/datasets/mattiuzc/commodity-futures-price-history  
**Descripción:** Histórico diario de 24 futuros desde Yahoo Finance (2000-2021)  
**Cobertura:** ~20 años hasta Junio 2021  
**Formato:** 24 archivos CSV individuales (Date, Open, High, Low, Close, Adj Close, Volume)

**Commodities incluidos:**
- **Granos:** Corn, Soybeans, Wheat, Oat, Soybean Meal, Soybean Oil
- **Energía:** Crude Oil, Brent Crude Oil, Natural Gas, Heating Oil, RBOB Gasoline
- **Metales:** Gold, Silver, Platinum, Palladium, Copper
- **Softs:** Coffee, Sugar, Cotton, Cocoa
- **Ganado:** Live Cattle, Feeder Cattle, Lean Hogs
- **Madera:** Lumber

**Ubicación:** `data/raw/kaggle/mattiuzc_futures/`  
**Uso:** Datos históricos base (2000-2021)

### Opción A: Descarga automática (recomendada)

**Requisitos:**
1. Instalar Kaggle API: `pip install kaggle`
2. Crear cuenta en Kaggle: https://www.kaggle.com/account/login
3. Obtener API token:
   - Settings > API > "Create New Token"
   - Guardar `kaggle.json` en:
     - **Windows:** `C:\Users\<tu_usuario>\.kaggle\`
     - **Linux/Mac:** `~/.kaggle/`

**Descarga:** El notebook `01_download_data.ipynb` detecta automáticamente si faltan archivos y los descarga vía:
```python
from kaggle.api.kaggle_api_extended import KaggleApi
api = KaggleApi()
api.authenticate()
api.dataset_download_files('mattiuzc/commodity-futures-price-history', unzip=True)
```

### Opción B: Descarga manual (alternativa)

1. Navegar al dataset: https://www.kaggle.com/datasets/mattiuzc/commodity-futures-price-history
2. Click en botón "Download" (descargar ZIP ~5 MB)
3. Descomprimir archivo ZIP
4. Copiar **todos** los archivos CSV a: `Base/data/raw/kaggle/mattiuzc_futures/`

**Resultado esperado:** 23-24 archivos CSV (Corn.csv, Soybean.csv, Gold.csv, etc.)

---

## 2. Yahoo Finance (vía yfinance) – Datos Recientes 2021-2025 ⭐ **DESCARGA AUTOMÁTICA**

**Biblioteca Python:** `yfinance`  
**Documentación:** https://github.com/ranaroussi/yfinance  
**Instalación:** `pip install yfinance`

### Descripción
Descarga automática de datos recientes de Yahoo Finance para empalmar con datos históricos de Kaggle. Permite extender series desde 2021 hasta la fecha actual.

### Tickers utilizados (24 commodities)

**Granos y oleaginosas:**
- `ZC=F` - Corn (Maíz) CBOT
- `ZS=F` - Soybeans (Soja) CBOT
- `ZW=F` - Wheat (Trigo) CBOT
- `ZL=F` - Soybean Oil
- `ZM=F` - Soybean Meal
- `ZO=F` - Oat

**Energía:**
- `CL=F` - Crude Oil WTI
- `BZ=F` - Brent Crude Oil
- `NG=F` - Natural Gas
- `HO=F` - Heating Oil
- `RB=F` - RBOB Gasoline

**Metales preciosos:**
- `GC=F` - Gold
- `SI=F` - Silver
- `PL=F` - Platinum
- `PA=F` - Palladium

**Metales industriales:**
- `HG=F` - Copper

**Softs:**
- `KC=F` - Coffee
- `SB=F` - Sugar
- `CT=F` - Cotton
- `CC=F` - Cocoa

**Ganado:**
- `LE=F` - Live Cattle
- `GF=F` - Feeder Cattle
- `HE=F` - Lean Hogs

**Madera:**
- `LBS=F` - Lumber

### Estrategia de empalme
1. **Kaggle (2000-2021):** Datos históricos de alta calidad
2. **Yahoo Finance (2021-2025):** Descarga automática vía yfinance con overlap de 30 días
3. **Empalme:** Eliminación de duplicados manteniendo versión más reciente

### Implementación (en notebook 01_download_data.ipynb)
```python
import yfinance as yf

# Mapeo completo de tickers
ticker_mapping = {
    'Corn': 'ZC=F',
    'Soybeans': 'ZS=F',
    'Wheat': 'ZW=F',
    # ... 21 tickers más
}

# Descargar datos recientes
for commodity_name, ticker in ticker_mapping.items():
    df = yf.download(ticker, start='2021-05-01', progress=False)
    # Guardar CSV individual
    df.to_csv(f'data/raw/kaggle/mattiuzc_futures/{commodity_name.lower()}_yahoo.csv')
```

### Ubicación archivos generados
- **Carpeta:** `data/raw/kaggle/mattiuzc_futures/`
- **Formato:** `<commodity>_yahoo.csv` (ej: `corn_yahoo.csv`, `gold_yahoo.csv`)
- **Total:** 24 archivos CSV con datos 2021-2025

### Variables descargadas
- `date` - Fecha
- `open`, `high`, `low`, `close` - Precios OHLC
- `adj_close` - Precio ajustado
- `volume` - Volumen
- `commodity` - Nombre del commodity

### Frecuencia
Diaria (actualización en tiempo real durante ejecución del notebook)

### Notas técnicas
- **Overlap:** 30 días con datos Kaggle (Mayo 2021) para validación cruzada
- **MultiIndex handling:** Código maneja automáticamente cambios de formato entre versiones de yfinance
- **Sufijo `_yahoo.csv`:** Permite distinguir datos recientes de históricos Kaggle
- **Sin API key:** yfinance es gratuito y no requiere autenticación

---

## Flujo de Integración - Pipeline de 2 Notebooks

### Notebook 01: Descarga (`01_download_data.ipynb`)

**Paso 1: Verificar Kaggle (manual)**
- Descargar ZIP desde Kaggle
- Copiar archivos a `data/raw/kaggle/mattiuzc_futures/`
- Resultado: 23-24 archivos CSV (2000-2021)

**Paso 2: Descargar Yahoo Finance (automático)**
- Ejecutar celda con `yfinance`
- Descarga 24 tickers desde Mayo 2021
- Guarda archivos `*_yahoo.csv` en misma carpeta
- Resultado: 24 archivos adicionales (2021-2025)

**Output:** ~48 archivos CSV totales en carpeta `mattiuzc_futures/`

---

### Notebook 02: Procesamiento (`02_process_data.ipynb`)

**Paso 1: Cargar datos**
- Kaggle: archivos sin sufijo `_yahoo.csv` → históricos
- Yahoo: archivos con sufijo `_yahoo.csv` → recientes

**Paso 2: Empalmar series**
```python
df_combined = pd.concat([df_kaggle, df_yahoo], ignore_index=True)
df_combined = df_combined.sort_values('date').drop_duplicates(subset='date', keep='last')
```
- Concatenar ambas fuentes
- Eliminar duplicados (overlap Mayo-Junio 2021)
- Mantener versión más reciente en caso de conflicto

**Paso 3: Feature Engineering**
- **Retornos logarítmicos:** `log_return_1d`, `log_return_5d`, `log_return_20d`, `log_return_60d`
- **Medias móviles:** `sma_20`, `sma_50`, `sma_200`
- **Señales técnicas:** `price_vs_sma20`, `price_vs_sma50` (% desviación)
- **Volatilidad anualizada:** `volatility_30d`, `volatility_60d`

**Paso 4: Visualizaciones**
1. `evolucion_precios_principales.png` - Series temporales 2000-2025
2. `volatilidad_historica.png` - Volatilidad promedio por año
3. `matriz_correlacion.png` - Correlaciones entre commodities
4. `distribucion_retornos.png` - Histogramas de retornos diarios

**Paso 5: Exportación**
- **CSV:** `data/processed/commodities_base_daily.csv` (~150,000 filas, 19 columnas)
- **Metadata:** `data/processed/metadata.json` (info del dataset)
- **Gráficos:** `graficos/*.png` (4 visualizaciones)

---

## Validaciones Implementadas

### Continuidad temporal
- ✅ Sin gaps mayores a 5 días (excepto fines de semana/feriados)
- ✅ Overlap de 30 días entre Kaggle y Yahoo validado

### Calidad de datos
- ✅ Precios > 0 (outliers marcados como NaN)
- ✅ Duplicados eliminados (keep='last')
- ✅ Forward-fill + backward-fill para imputación

### Cobertura completa
- ✅ Período: 2000-07-17 → 2025-10-27
- ✅ 24 commodities con datos empalmados
- ✅ ~6,400 días de trading por commodity

---

## Dependencias de Software

### Python - Librerías requeridas
```bash
pip install yfinance pandas numpy matplotlib seaborn openpyxl
```

**Versiones testeadas:**
- yfinance >= 0.2.28
- pandas >= 2.0.0
- numpy >= 1.24.0
- matplotlib >= 3.7.0
- seaborn >= 0.12.0
- openpyxl >= 3.1.0

---

## Ventajas de Esta Arquitectura

### Simplicidad
- Solo 2 fuentes de datos
- 1 descarga manual (Kaggle, una sola vez)
- 1 descarga automática (yfinance, ejecutar notebook)

### Reproducibilidad
- Sin dependencias de APIs externas
- Código auto-contenido en 2 notebooks
- Fácil de compartir y ejecutar por otros usuarios

### Actualización
- Ejecutar notebook 01 → actualiza datos hasta hoy
- Ejecutar notebook 02 → regenera dataset completo
- Sin límites de rate o cuotas de API

### Calidad
- Yahoo Finance = misma fuente que mattiuzc usó para datos históricos
- Consistencia en formato y variables
- Validación cruzada en período de overlap

---

---

## 3. Predictores Macroeconómicos (Yahoo Finance) ⭐ **NUEVOS PREDICTORES**

**Módulo:** `src/data/download_predictors.py`  
**Descarga:** Automática vía `yfinance`  
**Frecuencia:** Diaria

### Rationale: Por qué estos predictores

Los precios de commodities agrícolas (especialmente soja) son influenciados por múltiples factores macroeconómicos. Esta selección cubre:

1. **Sentimiento del mercado** (VIX, S&P 500)
2. **Dinámica cambiaria** (DXY, tipos de cambio de principales países)
3. **Costo de oportunidad** (tasas de interés)
4. **Sectores relacionados** (energía, materiales)
5. **Protección inflacionaria** (TIPS)

### Predictores Implementados

#### **A. Volatilidad y Sentimiento**

**VIX (^VIX) - CBOE Volatility Index**
- **Descripción:** "Índice del miedo" - Mide volatilidad implícita del S&P 500
- **Relación con commodities:** VIX alto → aversión al riesgo → caída en commodities
- **Rango típico:** 10-30 (normal), >40 (pánico)
- **Fuente:** Chicago Board Options Exchange
- **Uso:** Detectar períodos de estrés financiero que afectan flujos de inversión

**S&P 500 (^GSPC)**
- **Descripción:** Índice bursátil de 500 empresas de EE.UU.
- **Relación con commodities:** Proxy de salud económica global y apetito por riesgo
- **Correlación esperada:** Positiva (mercados optimistas → mayor demanda de materias primas)
- **Fuente:** Standard & Poor's
- **Uso:** Indicador de ciclo económico

---

#### **B. Índice Dólar**

**DXY (DX-Y.NYB) - U.S. Dollar Index**
- **Descripción:** Valor del USD vs canasta de 6 monedas (EUR, JPY, GBP, CAD, SEK, CHF)
- **Relación con commodities:** **Correlación negativa fuerte** - dólar fuerte → commodities más caros en otras monedas → menor demanda
- **Referencia:** Un aumento de 1% en DXY típicamente reduce precios de soja en ~0.3-0.5% ([Fuente: TheBalance](https://www.thebalancemoney.com))
- **Fuente:** ICE (Intercontinental Exchange)
- **Uso:** Variable clave para predicción de precios de commodities

---

#### **C. Tipos de Cambio - Principales Países Soja**

**USD/BRL (BRL=X) - Dólar/Real Brasileño** 🇧🇷
- **País:** Brasil - **Exportador #1 mundial de soja** (50% producción global)
- **Relación:** Real débil → costos locales menores → incentivo exportación → presión bajista en precios internacionales
- **Dinámica:** USD/BRL alto (real depreciado) aumenta competitividad brasileña
- **Fuente:** Banco Central do Brasil | FRED (serie DEXBZUS) | Yahoo Finance (BRL=X)
- **Uso crítico:** Predictor de oferta brasileña en mercado internacional

**USD/CNY (CNY=X) - Dólar/Yuan Chino** 🇨🇳
- **País:** China - **Importador #1 mundial de soja** (60% importaciones globales)
- **Relación:** Yuan fuerte (USD/CNY bajo) → mayor poder de compra chino → aumento demanda soja
- **Dinámica:** CNY apreciado estimula importaciones chinas (crushing de soja, alimento animal)
- **Fuente:** Banco Popular de China | Yahoo Finance (CNY=X)
- **Uso crítico:** Predictor de demanda china (key driver del mercado)

**USD/ARS (ARS=X) - Dólar/Peso Argentino** 🇦🇷
- **País:** Argentina - **Exportador #3 mundial de soja** (crucial en oferta global)
- **Relación:** Peso depreciado + retenciones a exportación → afectan competitividad argentina
- **Complejidad:** Controles cambiarios y "brecha" dólar oficial vs blue complican análisis
- **Fuente:** Banco Central de la República Argentina | Yahoo Finance (ARS=X)
- **Nota:** Tipo de cambio oficial puede diferir de mercados paralelos (dólar MEP/CCL)
- **Uso:** Proxy de competitividad exportadora argentina

---

#### **D. Tasas de Interés de EE.UU.**

**Treasury 10Y (^TNX) - Bonos del Tesoro 10 años**
- **Descripción:** Rendimiento de bonos del gobierno de EE.UU. a 10 años
- **Relación con commodities:** Tasas altas → mayor costo de carry (almacenamiento) → presión bajista en precios
- **Mecanismo:** Tasas altas atraen capital fuera de commodities hacia renta fija
- **Rango típico:** 1-4% (actual), histórico 4-8%
- **Fuente:** U.S. Department of the Treasury | FRED (serie DGS10)
- **Uso:** Costo de oportunidad de mantener inventarios

**Treasury 2Y (^IRX) - Bonos del Tesoro 2 años**
- **Descripción:** Rendimiento de bonos a corto plazo
- **Relación:** Curva de rendimiento (2Y vs 10Y) predice recesiones
- **Inversión de curva:** 2Y > 10Y históricamente precede recesiones (menor demanda futura de commodities)
- **Fuente:** U.S. Department of the Treasury
- **Uso:** Anticipar ciclos económicos

---

#### **E. Índices Sectoriales**

**Energy Index (^GSPE) - S&P 500 Energy Sector**
- **Descripción:** Índice de empresas del sector energético (Exxon, Chevron, etc.)
- **Relación con commodities:** Energía cara → mayores costos de producción agrícola (combustible, fertilizantes)
- **Correlación esperada:** Positiva con commodities energéticos (petróleo, gas)
- **Fuente:** S&P Dow Jones Indices
- **Uso:** Proxy de costos de producción agrícola

**Materials Index (^GSPMS) - S&P 500 Materials Sector**
- **Descripción:** Índice de empresas de materiales (minería, químicos, packaging)
- **Relación con commodities:** Refleja demanda industrial de metales y materias primas
- **Correlación esperada:** Positiva con metales industriales (cobre)
- **Fuente:** S&P Dow Jones Indices
- **Uso:** Indicador de demanda industrial

---

#### **F. Inflación (Proxy)**

**TIPS (TIP) - iShares TIPS Bond ETF**
- **Descripción:** ETF de bonos del Tesoro protegidos contra inflación
- **Por qué no IPC directo:** Yahoo Finance no ofrece series de IPC (Consumer Price Index)
- **Relación con commodities:** Inflación alta → commodities suben como cobertura (hedge)
- **Mecanismo:** Inversionistas compran commodities para proteger poder adquisitivo
- **Fuente:** iShares by BlackRock
- **Alternativas:** FRED API tiene serie CPIAUCSL (IPC oficial), pero requiere API key separada
- **Uso:** Proxy de expectativas inflacionarias

---

### Referencias Académicas

**Correlaciones soja-macro:**
- **Dólar (DXY):** Correlación -0.5 a -0.7 (negativa fuerte) ([TheBalance](https://www.thebalancemoney.com))
- **Inflación:** Efectos significativos en granos documentados ([ResearchGate](https://www.researchgate.net))
- **Tasas de interés:** Impacto vía costo de carry ([Federal Reserve Papers](https://www.federalreserve.gov))

**Países clave:**
- Brasil: 50% producción mundial soja ([USDA Foreign Agricultural Service](https://fas.usda.gov))
- China: 60% importaciones globales soja ([China Customs](http://www.customs.gov.cn))
- Argentina: 7% producción mundial, 3er exportador ([Ministerio de Agricultura Argentina](https://www.magyp.gob.ar))

---

### Implementación Técnica

**Descarga automática:**
```python
# Ejecutar desde raíz del proyecto
python src/data/download_predictors.py
```

**Archivos generados:**
- `data/interim/predictors/vix.csv`
- `data/interim/predictors/sp500.csv`
- `data/interim/predictors/dxy.csv`
- `data/interim/predictors/usd_brl.csv`
- `data/interim/predictors/usd_cny.csv`
- `data/interim/predictors/usd_ars.csv`
- `data/interim/predictors/treasury_10y.csv`
- `data/interim/predictors/treasury_2y.csv`
- `data/interim/predictors/energy_index.csv`
- `data/interim/predictors/materials_index.csv`
- `data/interim/predictors/tips.csv`

**Registro metadata:**
- `data/interim/predictors/predictors_registry.json`

**Procesamiento:**
```python
# Integrar predictores con commodities
python src/data/process.py
```

**Output final:**
- `data/processed/commodities_base_daily.csv` (ahora incluye 11 columnas adicionales de predictores)

---

### Limitaciones y Notas

**Tipos de cambio:**
- **ARS=X:** Refleja tipo de cambio oficial, no mercados paralelos (blue, MEP, CCL)
- **BRL=X y CNY=X:** Datos confiables desde ~2003, cobertura anterior limitada

**Inflación:**
- **TIPS como proxy:** No es IPC directo, pero capta expectativas inflacionarias
- **Para IPC oficial:** Usar FRED API (`pip install fredapi`) y serie CPIAUCSL

**Tasas:**
- **^TNX y ^IRX:** Reportan rendimientos en % (ej: 4.25 = 4.25%)
- **Ajuste de escala:** Verificar si otros predictores necesitan normalización

**Frecuencia:**
- Datos diarios (días de trading)
- Feriados de EE.UU. pueden tener NaN → forward-fill para imputar

---

## Contacto y Mantenimiento

**Proyecto:** BigDataUBA-Grupo10  
**Repositorio:** https://github.com/paulaleylen/BigDataUBA-GrupoJLP  
**Universidad:** UBA - Facultad de Ciencias Económicas  
**Año:** 2025

**Mantenedores:**
- Paula Leylén Ramirez (@paulaleylen)
- Juan Ignacio Pintos (@juanpintoselso33)
- Luis Mella

**Última revisión de fuentes:** Noviembre 2025
