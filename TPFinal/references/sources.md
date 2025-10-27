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

**Última revisión de fuentes:** Octubre 2025
