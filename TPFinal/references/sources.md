# Fuentes de Datos - Base de Commodities

**Proyecto:** Base de Datos Unificada para Análisis de Commodities  
**Universidad de Buenos Aires - Facultad de Ciencias Económicas**  
**Última actualización:** Octubre 2025

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

## Contacto y Mantenimiento

**Proyecto:** BigDataUBA-Grupo10  
**Repositorio:** https://github.com/paulaleylen/BigDataUBA-GrupoJLP  
**Universidad:** UBA - Facultad de Ciencias Económicas  
**Año:** 2025

**Mantenedores:**
- Paula Leylén Ramirez (@paulaleylen)
- Juan Ignacio Pintos (@juanpintoselso33)
- Luis Mella

---

## 3. Fuentes de Datos Académicas (Diciembre 2025)

### 3.1. CFTC - Commitments of Traders (COT)
**URL:** https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm  
**Descripción:** Reportes semanales de posiciones de futuros y opciones  
**Cobertura:** 2000-2025  
**Frecuencia:** Semanal (martes, publicado viernes)  
**Formato:** Legacy Reports TXT (fixed-width)  

**Commodities:**
- Corn (CBOT, código 002602)
- Soybeans (CBOT, código 005602)
- Wheat (CBOT, código 001602)

**Variables extraídas:**
- Commercial long/short (hedgers)
- Non-commercial long/short (especuladores)
- Open interest total
- Ratios y cambios semanales

**Script:** `src/data/download_cftc_cot.py`  
**Output:** `data/external/cftc/cftc_features_2000_2025.csv` (6,731 × 11)

---

### 3.2. GDELT - Global Database of Events, Language and Tone
**URL:** https://www.gdeltproject.org/  
**Descripción:** Base de datos global de eventos y sentimiento de noticias  
**Cobertura:** 
- v1.0 (2000-2013): Historical files
- v2.0 (2015-2025): Real-time files  
**Frecuencia:** 15 minutos (agregado a diario)  
**Formato:** CSV comprimidos (GZip)  

**Queries por commodity:**
- "corn AND (agriculture OR grain OR futures)"
- "soybeans AND (agriculture OR oilseed OR futures)"
- "wheat AND (agriculture OR grain OR futures)"

**Variables extraídas:**
- Tone promedio diario (-1 a +1)
- Event count (número de menciones)
- Moving averages (7 días)

**Script:** `src/data/download_sentiment_gdelt.py`  
**Output:** `data/external/gdelt/sentiment_features_2000_2025.csv` (6,731 × 10)  
**Nota:** Gap 2014 (transición v1→v2), imputado con median(2013, 2015)

---

### 3.3. Baltic Dry Index (BDI)
**URL:** https://www.investing.com/indices/baltic-dry-historical-data  
**Descripción:** Índice de costos de transporte marítimo global  
**Cobertura:** 2000-2025  
**Frecuencia:** Diaria (días hábiles)  
**Formato:** CSV (descarga manual)  

**Variables:**
- BDI level (puntos)
- Lags (7, 30, 90 días)
- Rolling means (30 días)
- Returns y volatilidad
- Spike indicator (>2σ)

**Script:** `src/data/download_bdi.py`  
**Input manual:** `data/external/bdi/baltic_dry_index.csv`  
**Output:** `data/interim/bdi/bdi_features.csv` (6,456 × 8)

---

### 3.4. USDA NASS - Crop Conditions
**URL:** https://quickstats.nass.usda.gov/api  
**API Key:** Requerida (gratis)  
**Descripción:** Condiciones semanales de cultivos (Good/Excellent %)  
**Cobertura:** 2024-2025 (limitación API)  
**Frecuencia:** Semanal  
**Formato:** JSON API  

**Commodities:**
- Corn, Soybeans, Wheat

**Variables extraídas:**
- % Good + Excellent semanal
- Week-over-week change
- Moving average 4 semanas
- Deviation de promedio histórico
- Binary indicator (>60% = good conditions)

**Script:** `src/data/download_crop_conditions.py`  
**Output:** `data/interim/supply_demand/crop_conditions_all_features.csv` (337 × 15)  
**API Key:** `.env` → `NASS_API_KEY`

---

### 3.5. USDA ERS - Government Stocks (Ending Stocks)
**URLs directas (sin API):**
- Corn: https://www.ers.usda.gov/webdocs/DataFiles/50048/FeedGrainsYearbook.csv
- Soybeans: https://www.ers.usda.gov/webdocs/DataFiles/50594/oilcropsyearbook.csv
- Wheat: https://www.ers.usda.gov/webdocs/DataFiles/53786/WheatYearbookTable04.xlsx

**Descripción:** Stocks gubernamentales de fin de año comercial  
**Cobertura:**
- Corn: 1960-2025 (66 años)
- Soybeans: 1980-2024 (45 años)
- Wheat: 1960-2025 (66 años)  
**Frecuencia:** Anual (forward-fill a diario)  
**Formato:** CSV (Corn, Soy) y XLSX multi-sheet (Wheat)  

**Variables extraídas:**
- Ending stocks absolutos (bushels)
- Year-over-year change (bushels)
- YoY percentage change

**Script:** `src/data/download_government_stocks_ers.py`  
**Output:** `data/interim/supply_demand/government_stocks_ers_all_features.csv` (23,834 × 9)  
**Nota:** Wheat requiere parser custom para XLSX Table04

---

### 3.6. FRED - Federal Reserve Economic Data
**URL:** https://fred.stlouisfed.org/docs/api/  
**API Key:** Requerida (gratis)  
**Descripción:** Indicadores macroeconómicos de la Reserva Federal  
**Cobertura:** 2000-2025  
**Frecuencia:** Daily, Monthly, Quarterly (según serie)  
**Formato:** JSON API  

**Series descargadas:**
1. **FEDFUNDS** - Federal Funds Effective Rate (% monthly)
2. **DFF** - Federal Funds Rate Daily (% daily)
3. **UNRATE** - Unemployment Rate (% monthly)
4. **CPIAUCSL** - Consumer Price Index (index monthly)
5. **GDP** - Gross Domestic Product (billions quarterly)

**Variables extraídas por serie:**
- Base value
- Change (diff)
- Percentage change
- Lags (7, 30 días)
- Moving averages (30, 90 días)

**Script:** `src/data/download_fred.py`  
**Output:** `data/interim/fred/fred_all_features.csv` (9,470 × 33)  
**API Key:** `.env` → `FRED_API_KEY`  
**Resampling:** Monthly/quarterly → daily via forward-fill

---

## API Keys Necesarias

Crear archivo `.env` en raíz del proyecto:

```bash
# USDA NASS Quick Stats API (crop conditions)
NASS_API_KEY=tu_key_aqui

# Federal Reserve Economic Data API (economic indicators)
FRED_API_KEY=tu_key_aqui
```

**Obtener keys (gratis):**
- NASS: https://quickstats.nass.usda.gov/api (registro simple)
- FRED: https://fred.stlouisfed.org/docs/api/api_key.html (crear cuenta)

---

## Feature Count Total

| Categoría | Features | Script |
|-----------|----------|--------|
| Baseline (Step 4) | 3,186 | download_commodities, download_predictors, download_climate |
| CFTC (Step 5) | +11 | download_cftc_cot |
| GDELT (Step 6) | +10 | download_sentiment_gdelt |
| BDI (Step 7) | +8 | download_bdi |
| Crop Conditions (Step 8) | +15 | download_crop_conditions |
| Gov Stocks (Step 9) | +9 | download_government_stocks_ers |
| **TOTAL** | **3,239** | `make data` (ejecuta todos) |

**Dataset final:** `data/processed/features_final_modeling.csv` (6,731 × 3,239)

---

**Última revisión de fuentes:** Diciembre 2025
