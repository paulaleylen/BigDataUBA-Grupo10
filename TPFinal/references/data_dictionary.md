# Diccionario de Datos - Super Base de Commodities

**Proyecto:** Base Unificada para Análisis de Commodities Agrícolas  
**Universidad de Buenos Aires - Facultad de Ciencias Económicas**  
**Última actualización:** Octubre 2025

---

## Estructura del Dataset Final

**Archivo:** `data/processed/commodities_base_daily.csv`  
**Granularidad:** Diaria  
**Período:** 2000-2025 (25 años de historia completa)  
**Observaciones:** ~150.000 registros (24 commodities × ~6.400 días)  
**Fuentes:** Kaggle (2000-2021) + Yahoo Finance (2021-2025)

---

## 1. Variables de Identificación

### date
- **Descripción:** Fecha de la observación
- **Tipo:** Datetime (YYYY-MM-DD)
- **Fuente:** Todas
- **Frecuencia:** Diaria
- **Zona horaria:** UTC
- **Notas:** Días hábiles de mercado (lunes-viernes excepto feriados CME)

### commodity
- **Descripción:** Nombre del commodity
- **Tipo:** String (categorical)
- **Valores posibles:** 
  - Granos: Corn, Soybeans, Wheat, Oat, Soybean_Oil, Soybean_Meal
  - Energía: Crude_Oil, Brent_Crude_Oil, Natural_Gas, Heating_Oil, RBOB_Gasoline
  - Metales: Gold, Silver, Platinum, Palladium, Copper
  - Softs: Coffee, Sugar, Cotton, Cocoa
  - Ganado: Live_Cattle, Feeder_Cattle, Lean_Hogs
  - Madera: Lumber
- **Total:** 24 commodities

---

## 2. Variables de Precios (OHLC)

## 2. Variables de Precios (OHLC)

### open
- **Descripción:** Precio de apertura de la sesión
- **Fuente:** Kaggle (histórico) / Yahoo Finance (reciente)
- **Unidad:** USD (varía según commodity - bushels, barrels, troy ounces, etc.)
- **Frecuencia:** Diaria
- **Cobertura:** 2000-2025
- **Nota:** Primer precio negociado del día

### high
- **Descripción:** Precio máximo de la sesión
- **Fuente:** Kaggle / Yahoo Finance
- **Unidad:** USD
- **Frecuencia:** Diaria
- **Cobertura:** 2000-2025
- **Uso:** Cálculo de rangos y volatilidad intradiaria

### low
- **Descripción:** Precio mínimo de la sesión
- **Fuente:** Kaggle / Yahoo Finance
- **Unidad:** USD
- **Frecuencia:** Diaria
- **Cobertura:** 2000-2025
- **Uso:** Cálculo de rangos y volatilidad intradiaria

### close
- **Descripción:** Precio de cierre de la sesión (último precio negociado)
- **Fuente:** Kaggle / Yahoo Finance
- **Unidad:** USD
- **Frecuencia:** Diaria
- **Cobertura:** 2000-2025
- **Nota:** Variable principal para cálculos de retornos y análisis técnico

### adj_close
- **Descripción:** Precio de cierre ajustado por splits y dividendos
- **Fuente:** Kaggle / Yahoo Finance
- **Unidad:** USD
- **Frecuencia:** Diaria
- **Cobertura:** 2000-2025
- **Nota:** Para futuros de commodities, generalmente igual a close (no hay splits/dividendos)

### volume
- **Descripción:** Volumen de contratos negociados en la sesión
- **Fuente:** Kaggle / Yahoo Finance
- **Unidad:** Número de contratos
- **Frecuencia:** Diaria
- **Cobertura:** 2000-2025
- **Nota:** Proxy de liquidez; valores faltantes rellenados con 0

---

## 3. Feature Engineering - Retornos Logarítmicos
## 3. Feature Engineering - Retornos Logarítmicos

### log_return_1d
- **Descripción:** Retorno logarítmico diario
- **Fórmula:** log(close_t / close_t-1)
- **Unidad:** Sin unidad (retorno continuo compuesto)
- **Frecuencia:** Diaria
- **Agrupación:** Por commodity
- **Uso:** Modelado de volatilidad, backtesting, propiedades estadísticas superiores a retornos simples
- **Nota:** Primer valor de cada commodity es NaN (requiere lag)

### log_return_5d
- **Descripción:** Retorno logarítmico semanal (5 días hábiles)
- **Fórmula:** log(close_t / close_t-5)
- **Unidad:** Sin unidad
- **Frecuencia:** Diaria (rolling)
- **Agrupación:** Por commodity
- **Uso:** Análisis de tendencias semanales

### log_return_20d
- **Descripción:** Retorno logarítmico mensual (~20 días hábiles)
- **Fórmula:** log(close_t / close_t-20)
- **Unidad:** Sin unidad
- **Frecuencia:** Diaria (rolling)
- **Agrupación:** Por commodity
- **Uso:** Análisis de tendencias mensuales

### log_return_60d
- **Descripción:** Retorno logarítmico trimestral (~60 días hábiles)
- **Fórmula:** log(close_t / close_t-60)
- **Unidad:** Sin unidad
- **Frecuencia:** Diaria (rolling)
- **Agrupación:** Por commodity
- **Uso:** Análisis de tendencias trimestrales

---

## 4. Feature Engineering - Medias Móviles Simples (SMA)

### sma_20
- **Descripción:** Media móvil simple de 20 días del precio de cierre
- **Fórmula:** mean(close[t-19:t])
- **Unidad:** USD (misma que close)
- **Ventana:** 20 días hábiles (~1 mes de trading)
- **Agrupación:** Por commodity
- **min_periods:** 1 (permite cálculo desde primer día)
- **Uso:** Señales de tendencia corto/medio plazo, cruces con precio

### sma_50
- **Descripción:** Media móvil simple de 50 días del precio de cierre
- **Fórmula:** mean(close[t-49:t])
- **Unidad:** USD
- **Ventana:** 50 días hábiles (~2.5 meses)
- **Agrupación:** Por commodity
- **min_periods:** 1
- **Uso:** Señales de tendencia medio plazo, cruces con SMA 20/200

### sma_200
- **Descripción:** Media móvil simple de 200 días del precio de cierre
- **Fórmula:** mean(close[t-199:t])
- **Unidad:** USD
- **Ventana:** 200 días hábiles (~10 meses)
- **Agrupación:** Por commodity
- **min_periods:** 1
- **Uso:** Tendencia de largo plazo, soporte/resistencia dinámico

---

## 5. Feature Engineering - Señales Técnicas

### price_vs_sma20
- **Descripción:** Desviación porcentual del precio respecto a SMA 20
- **Fórmula:** (close / sma_20 - 1) × 100
- **Unidad:** Porcentaje (%)
- **Frecuencia:** Diaria
- **Agrupación:** Por commodity
- **Interpretación:**
  - > 0: Precio sobre media móvil (momentum alcista)
  - < 0: Precio bajo media móvil (momentum bajista)
  - Valores extremos (±10%): Sobrecompra/sobreventa relativa
- **Uso:** Señales de reversión a la media, filtros de tendencia

### price_vs_sma50
- **Descripción:** Desviación porcentual del precio respecto a SMA 50
- **Fórmula:** (close / sma_50 - 1) × 100
- **Unidad:** Porcentaje (%)
- **Frecuencia:** Diaria
- **Agrupación:** Por commodity
- **Interpretación:** Similar a price_vs_sma20, menor sensibilidad

---

## 6. Feature Engineering - Volatilidad Histórica

### volatility_30d
- **Descripción:** Volatilidad histórica realizada anualizada (ventana 30 días)
- **Fórmula:** std(log_return_1d[t-29:t]) × sqrt(252)
- **Unidad:** Anualizada (decimal, convertir a % × 100)
- **Ventana:** 30 días hábiles
- **Agrupación:** Por commodity
- **min_periods:** 20 (requiere mínimo 20 observaciones para cálculo válido)
- **Frecuencia:** Diaria (rolling)
- **Uso:** 
  - Gestión de riesgo (VaR, position sizing)
  - Identificación de regímenes de volatilidad
  - Pricing de opciones (proxy de vol implícita)
- **Interpretación:**
  - Granos: 0.15-0.30 normal, > 0.40 alta volatilidad
  - Energía: 0.20-0.50 normal, > 0.60 alta volatilidad
  - Metales: 0.10-0.25 normal

### volatility_60d
- **Descripción:** Volatilidad histórica realizada anualizada (ventana 60 días)
- **Fórmula:** std(log_return_1d[t-59:t]) × sqrt(252)
- **Unidad:** Anualizada (decimal)
- **Ventana:** 60 días hábiles (~3 meses)
- **Agrupación:** Por commodity
- **min_periods:** 20
- **Frecuencia:** Diaria (rolling)
- **Uso:** Volatilidad de medio plazo, menos sensible a shocks puntuales

---

## 7. Metadatos y Convenciones

### Estructura de Columnas (orden en CSV)
1. **Identificación:** date, commodity (2 cols)
2. **Precios OHLC:** open, high, low, close, adj_close, volume (6 cols)
3. **Retornos:** log_return_1d, log_return_5d, log_return_20d, log_return_60d (4 cols)
4. **Medias móviles:** sma_20, sma_50, sma_200 (3 cols)
5. **Señales:** price_vs_sma20, price_vs_sma50 (2 cols)
6. **Volatilidad:** volatility_30d, volatility_60d (2 cols)

**Total:** 19 columnas

### Tratamiento de Missing Values

**NaN permitidos (por diseño):**
- Primeras observaciones de retornos (requieren lags)
- Primeras observaciones de SMAs (requieren ventanas)
- Primeras observaciones de volatilidad (requieren min 20 días)
- Días sin trading (weekends, feriados)

**NaN rellenados:**
- `volume`: 0 (asume no hubo trading)
- Precios OHLC: Forward-fill + Backward-fill por commodity (solo gaps < 5 días)

**NaN marcados (no rellenados):**
- Precios <= 0 detectados como outliers → convertidos a NaN

### Validaciones Implementadas

1. **Continuidad temporal:** Verificar gaps > 5 días hábiles
2. **Precios positivos:** Todos los OHLC > 0
3. **Volumen no negativo:** volume >= 0
4. **Retornos en rango:** |log_return_1d| < 0.20 (±20%) → flag outliers
5. **Volatilidad en rango:** 0 < volatility_30d < 2.0 (200%)
6. **SMAs ordenados:** Generalmente sma_20 más cercano a precio que sma_200

---

## 8. Unidades de Referencia por Commodity

### Granos (CBOT)
- **Corn, Soybeans, Wheat, Oat:** USD por bushel
- **Tamaño contrato:** 5.000 bushels
- **Conversión:** 1 bushel maíz ≈ 25.4 kg, 1 bushel soja ≈ 27.2 kg

### Energía (NYMEX/ICE)
- **Crude Oil, Brent:** USD por barril (42 galones)
- **Natural Gas:** USD por MMBtu (Million British Thermal Units)
- **Heating Oil, RBOB Gasoline:** USD por galón

### Metales (COMEX)
- **Gold, Silver, Platinum, Palladium:** USD por troy ounce
- **Copper:** USD por libra
- **Conversión:** 1 troy oz ≈ 31.1 gramos

### Softs (ICE)
- **Coffee:** USD cents por libra (contrato 37.500 lbs)
- **Sugar:** USD cents por libra (contrato 112.000 lbs)
- **Cotton:** USD cents por libra (contrato 50.000 lbs)
- **Cocoa:** USD por tonelada métrica (contrato 10 mt)

### Ganado (CME)
- **Live Cattle, Feeder Cattle:** USD cents por libra
- **Lean Hogs:** USD cents por libra

### Madera
- **Lumber:** USD por 1.000 board feet

---

## 9. Esquema de Exportación

## 9. Esquema de Exportación

### commodities_base_daily.csv
**Formato:** CSV (comma-separated)  
**Encoding:** UTF-8  
**Índice:** No (date es columna normal)

**Columnas (19 en total):**
1. `date` - Fecha (YYYY-MM-DD)
2. `commodity` - Nombre del commodity (string)
3. `open` - Precio apertura (float)
4. `high` - Precio máximo (float)
5. `low` - Precio mínimo (float)
6. `close` - Precio cierre (float)
7. `adj_close` - Precio cierre ajustado (float)
8. `volume` - Volumen (int64)
9. `log_return_1d` - Retorno log diario (float)
10. `log_return_5d` - Retorno log semanal (float)
11. `log_return_20d` - Retorno log mensual (float)
12. `log_return_60d` - Retorno log trimestral (float)
13. `sma_20` - Media móvil 20 días (float)
14. `sma_50` - Media móvil 50 días (float)
15. `sma_200` - Media móvil 200 días (float)
16. `price_vs_sma20` - Desviación % vs SMA20 (float)
17. `price_vs_sma50` - Desviación % vs SMA50 (float)
18. `volatility_30d` - Volatilidad 30d anualizada (float)
19. `volatility_60d` - Volatilidad 60d anualizada (float)

**Tamaño estimado:** ~20 MB (150.000 filas × 19 columnas)

### metadata.json
Archivo complementario con información técnica:

```json
{
  "dataset": "commodities_base_daily.csv",
  "created_at": "2025-10-27T...",
  "shape": {
    "rows": 150000,
    "columns": 19
  },
  "period": {
    "start": "2000-07-17",
    "end": "2025-10-27"
  },
  "commodities": [
    "Corn", "Soybeans", "Wheat", "Crude_Oil",
    "Gold", "Silver", "Natural_Gas", ...
  ],
  "columns": {
    "base": ["date", "commodity"],
    "prices": ["open", "high", "low", "close", "adj_close", "volume"],
    "returns": ["log_return_1d", "log_return_5d", "log_return_20d", "log_return_60d"],
    "moving_averages": ["sma_20", "sma_50", "sma_200", "price_vs_sma20", "price_vs_sma50"],
    "volatility": ["volatility_30d", "volatility_60d"]
  },
  "sources": {
    "kaggle": "mattiuzc/commodity-futures-price-history (2000-2021)",
    "yahoo_finance": "yfinance library (2021-2025)"
  },
  "processing": {
    "imputation": "Forward-fill + Backward-fill (prices), 0 (volume)",
    "outliers": "Prices <= 0 set to NaN",
    "features": [
      "Log returns (1d, 5d, 20d, 60d)",
      "Simple moving averages (20, 50, 200)",
      "Volatility (30d, 60d annualized, sqrt(252))",
      "Price deviations vs SMAs"
    ]
  }
}
```

---

## 10. Visualizaciones Generadas

El notebook `02_process_data.ipynb` genera 4 gráficos principales guardados en `graficos/`:

### evolucion_precios_principales.png
- **Tipo:** Serie temporal (6 subplots)
- **Commodities:** Corn, Soybeans, Wheat, Crude Oil, Gold, Silver
- **Período:** 2000-2025
- **Features:** Marca inicio Guerra Ucrania (Feb 2022) con banda roja
- **Formato:** 15×12 inches, 300 dpi

### volatilidad_historica.png
- **Tipo:** Serie temporal líneas
- **Métrica:** Promedio anual de volatility_30d por commodity
- **Features:** Marca eventos críticos (Crisis 2008, COVID-19, Guerra Ucrania)
- **Formato:** 14×6 inches, 300 dpi

### matriz_correlacion.png
- **Tipo:** Heatmap
- **Métrica:** Correlación de retornos log diarios (2000-2025)
- **Dimensiones:** 6×6 (commodities principales)
- **Escala:** -1 a +1 (colormap RdYlGn)
- **Valores:** Anotados en cada celda
- **Formato:** 10×8 inches, 300 dpi

### distribucion_retornos.png
- **Tipo:** Histogramas + curva normal (6 subplots)
- **Métrica:** Distribución de log_return_1d
- **Estadísticas:** μ, σ, skewness, kurtosis (anotadas)
- **Comparación:** Histograma real vs. distribución normal teórica
- **Formato:** 15×10 inches, 300 dpi

---

## 10. Predictores Macroeconómicos (Nuevos)

**Archivo separado:** `data/interim/predictors/*.csv` (11 archivos)  
**Integración:** Se merge con base de commodities por fecha en `process.py`  
**Fuente:** Yahoo Finance vía `yfinance`  
**Granularidad:** Diaria  
**Período:** 2000-2025 (según disponibilidad por ticker)

### Columnas comunes en archivos de predictores:
- `date` - Fecha de observación
- `predictor` - Nombre del predictor
- `open`, `high`, `low`, `close`, `adj_close` - Precios OHLC
- `volume` - Volumen (cuando aplica)

---

### 10.1 Volatilidad y Sentimiento

#### VIX (^VIX)
- **Nombre completo:** CBOE Volatility Index
- **Descripción:** Índice de volatilidad implícita del S&P 500 (30 días adelante)
- **Ticker Yahoo Finance:** ^VIX
- **Unidad:** Porcentaje anualizado (reportado como número, ej: 20 = 20%)
- **Rango típico:** 10-30 (normal), 40-80+ (pánico extremo)
- **Interpretación:**
  - VIX < 15: Complacencia, baja volatilidad esperada
  - VIX 15-30: Rango normal
  - VIX > 30: Incertidumbre elevada, aversión al riesgo
  - VIX > 40: Pánico (crisis 2008: 80+, COVID-19: 85+)
- **Relación con commodities:** Correlación negativa (~-0.3 a -0.5) - VIX alto → caída en commodities
- **Fuente:** Chicago Board Options Exchange (CBOE)
- **Cobertura:** 1990-presente (VIX original), 2004-presente (VIX moderno)
- **Archivo:** `data/interim/predictors/vix.csv`

#### SP500 (^GSPC)
- **Nombre completo:** S&P 500 Index
- **Descripción:** Índice bursátil ponderado por capitalización de 500 empresas de EE.UU.
- **Ticker Yahoo Finance:** ^GSPC
- **Unidad:** Puntos del índice (sin unidad monetaria directa)
- **Rango histórico:** 800 (2009) → 4.800 (2025)
- **Interpretación:**
  - S&P500 en alza: Optimismo económico, apetito por riesgo → positivo para commodities
  - S&P500 en baja: Recesión esperada, aversión al riesgo → negativo para commodities
- **Relación con commodities:** Correlación positiva moderada (~0.3-0.5) - ambos suben en expansión económica
- **Fuente:** Standard & Poor's Dow Jones Indices
- **Cobertura:** 1928-presente (histórico completo disponible)
- **Archivo:** `data/interim/predictors/sp500.csv`

---

### 10.2 Índice Dólar

#### DXY (DX-Y.NYB)
- **Nombre completo:** U.S. Dollar Index (USDX)
- **Descripción:** Valor del USD vs canasta de 6 monedas: EUR (57.6%), JPY (13.6%), GBP (11.9%), CAD (9.1%), SEK (4.2%), CHF (3.6%)
- **Ticker Yahoo Finance:** DX-Y.NYB
- **Unidad:** Puntos del índice (base 100 en marzo 1973)
- **Rango histórico:** 70 (2008, 2021) → 165 (1985, punto Volcker)
- **Rango reciente:** 90-105 (2020-2025)
- **Interpretación:**
  - DXY > 100: Dólar fuerte → commodities más caros en otras monedas → presión bajista
  - DXY < 90: Dólar débil → commodities más baratos en otras monedas → presión alcista
- **Relación con commodities:** **Correlación negativa fuerte** (~-0.5 a -0.7) - clave para predicción
- **Referencia académica:** Un aumento de 1% en DXY reduce precios de soja en ~0.3-0.5% ([TheBalance](https://www.thebalancemoney.com))
- **Fuente:** ICE (Intercontinental Exchange)
- **Cobertura:** 1973-presente (histórico completo disponible)
- **Archivo:** `data/interim/predictors/dxy.csv`

---

### 10.3 Tipos de Cambio (Exportadores/Importadores de Soja)

#### USD_BRL (BRL=X) 🇧🇷
- **Nombre completo:** USD/BRL - Dólar estadounidense / Real brasileño
- **Descripción:** Tipo de cambio spot del dólar frente al real de Brasil
- **País:** Brasil - **Exportador #1 mundial de soja** (50% producción global, ~140 millones ton/año)
- **Ticker Yahoo Finance:** BRL=X
- **Unidad:** Reales por 1 USD (ej: 5.00 = 5 reales por dólar)
- **Rango histórico:** 1.5 (2011) → 6.0 (2021, pandemia)
- **Rango reciente:** 4.5-5.5 (2023-2025)
- **Interpretación:**
  - USD/BRL alto (real débil): Costos locales menores en USD → incentivo exportación → mayor oferta global → presión bajista en precios
  - USD/BRL bajo (real fuerte): Costos locales más caros en USD → desincentivo exportación → menor oferta global → presión alcista
- **Mecanismo:** Productor brasileño recibe pago en USD pero tiene costos en BRL. Real débil mejora márgenes, incentiva plantar más soja.
- **Relación con commodities:** Correlación negativa con precio soja (~-0.3)
- **Fuente:** Banco Central do Brasil | FRED (serie DEXBZUS) | Yahoo Finance
- **Cobertura:** ~2000-presente (BRL flotante desde 1999)
- **Archivo:** `data/interim/predictors/usd_brl.csv`

#### USD_CNY (CNY=X) 🇨🇳
- **Nombre completo:** USD/CNY - Dólar estadounidense / Yuan renminbi chino
- **Descripción:** Tipo de cambio spot del dólar frente al yuan de China
- **País:** China - **Importador #1 mundial de soja** (60% importaciones globales, ~100 millones ton/año)
- **Ticker Yahoo Finance:** CNY=X
- **Unidad:** Yuanes por 1 USD (ej: 7.00 = 7 yuanes por dólar)
- **Rango histórico:** 6.0 (2014, yuan fuerte) → 7.3 (2023, yuan débil)
- **Rango reciente:** 6.8-7.3 (2020-2025)
- **Interpretación:**
  - USD/CNY bajo (yuan fuerte): Mayor poder de compra chino → aumento demanda importaciones soja → presión alcista
  - USD/CNY alto (yuan débil): Menor poder de compra chino → reducción demanda importaciones → presión bajista
- **Mecanismo:** China importa soja pagando en USD. Yuan fuerte hace soja más barata en términos locales, estimula demanda (crushing, alimento porcino).
- **Relación con commodities:** Correlación negativa con precio soja (~-0.2)
- **Fuente:** Banco Popular de China | Yahoo Finance
- **Nota:** China maneja tipo de cambio con banda flotante (no totalmente libre)
- **Cobertura:** ~2005-presente (dato confiable desde flotación parcial)
- **Archivo:** `data/interim/predictors/usd_cny.csv`

#### USD_ARS (ARS=X) 🇦🇷
- **Nombre completo:** USD/ARS - Dólar estadounidense / Peso argentino
- **Descripción:** Tipo de cambio spot del dólar frente al peso de Argentina
- **País:** Argentina - **Exportador #3 mundial de soja** (~7% producción global, ~50 millones ton/año)
- **Ticker Yahoo Finance:** ARS=X
- **Unidad:** Pesos por 1 USD (ej: 350 = 350 pesos por dólar)
- **Rango histórico:** 1.0 (convertibilidad 1991-2001) → 1.000+ (2023-2025, hiperinflación)
- **Interpretación:**
  - USD/ARS alto (peso depreciado): Mejora competitividad exportadora argentina → mayor oferta global
  - Complicación: Retenciones a la exportación (hasta 33%) reducen incentivo
  - Control cambiario ("cepo") distorsiona mercado oficial
- **ADVERTENCIA CRÍTICA:** ARS=X refleja **tipo de cambio oficial**, NO mercados paralelos:
  - **Dólar oficial:** Tipo de cambio regulado por BCRA (dato de ARS=X)
  - **Dólar blue:** Mercado informal
  - **Dólar MEP/CCL:** Tipos de cambio financieros (más altos que oficial)
  - **Brecha:** Puede ser 50-100% entre oficial y paralelos
- **Relación con commodities:** Correlación débil y compleja por distorsiones regulatorias
- **Fuente:** Banco Central de la República Argentina | Yahoo Finance
- **Cobertura:** ~2000-presente (con saltos por crisis cambiarias)
- **Nota:** Usar con precaución para modelado - preferir USD/BRL como proxy de competitividad sudamericana
- **Archivo:** `data/interim/predictors/usd_ars.csv`

---

### 10.4 Tasas de Interés de EE.UU.

#### Treasury_10Y (^TNX)
- **Nombre completo:** U.S. Treasury 10-Year Note Yield
- **Descripción:** Rendimiento (yield) de bonos del Tesoro de EE.UU. a 10 años
- **Ticker Yahoo Finance:** ^TNX
- **Unidad:** Porcentaje anual (reportado como número, ej: 4.25 = 4.25%)
- **Rango histórico:** 0.5% (2020, COVID) → 15.8% (1981, Volcker)
- **Rango reciente:** 1.5-5.0% (2020-2025)
- **Interpretación:**
  - Tasas altas (>4%): Mayor costo de carry (almacenamiento) + atractivo de renta fija → capital sale de commodities → presión bajista
  - Tasas bajas (<2%): Menor costo de carry + poco atractivo de renta fija → capital busca retorno en commodities → presión alcista
- **Mecanismo económico:**
  1. **Costo de carry:** Tasa alta encarece financiamiento de inventarios de granos/metales
  2. **Oportunidad:** Bonos 10Y con 5% compiten con retorno esperado de commodities
  3. **Recesión:** Tasas muy altas preceden recesiones (menor demanda futura)
- **Relación con commodities:** Correlación negativa (~-0.2 a -0.4)
- **Fuente:** U.S. Department of the Treasury | FRED (serie DGS10)
- **Cobertura:** 1962-presente (histórico completo disponible)
- **Archivo:** `data/interim/predictors/treasury_10y.csv`

#### Treasury_2Y (^IRX)
- **Nombre completo:** U.S. Treasury 2-Year Note Yield
- **Descripción:** Rendimiento de bonos del Tesoro a 2 años
- **Ticker Yahoo Finance:** ^IRX
- **Unidad:** Porcentaje anual
- **Rango reciente:** 0.1-5.0% (2020-2025)
- **Interpretación:**
  - **Curva de rendimiento (2Y vs 10Y):**
    - Normal: 10Y > 2Y (pendiente positiva) → expansión económica esperada
    - Invertida: 2Y > 10Y (pendiente negativa) → **recesión esperada** (históricamente predice recesiones con 12-18 meses anticipación)
  - Inversión de curva (2023-2024): 2Y en 5.0%, 10Y en 4.0% → recesión anticipada 2024-2025
- **Relación con commodities:** Curva invertida → menor demanda futura de commodities
- **Fuente:** U.S. Department of the Treasury
- **Cobertura:** 1976-presente
- **Uso:** Calcular pendiente de curva (10Y - 2Y) como predictor de ciclo
- **Archivo:** `data/interim/predictors/treasury_2y.csv`

---

### 10.5 Índices Sectoriales

#### Energy_Index (^GSPE)
- **Nombre completo:** S&P 500 Energy Sector Index
- **Descripción:** Índice de empresas del sector energético dentro del S&P 500 (Exxon, Chevron, ConocoPhillips, etc.)
- **Ticker Yahoo Finance:** ^GSPE
- **Unidad:** Puntos del índice
- **Rango histórico:** 200 (2020, COVID) → 800 (2022, guerra Ucrania)
- **Interpretación:**
  - Índice alto: Precio del petróleo alto → mayores costos de producción agrícola (combustible, transporte, fertilizantes) → presión alcista en commodities agrícolas
  - Índice bajo: Energía barata → menores costos de producción
- **Relación con commodities:**
  - **Correlación positiva** con petróleo/gas (~0.8-0.9, obvio)
  - **Correlación positiva débil** con granos (~0.2-0.3, vía costos)
- **Fuente:** S&P Dow Jones Indices
- **Cobertura:** 1989-presente
- **Archivo:** `data/interim/predictors/energy_index.csv`

#### Materials_Index (^GSPMS)
- **Nombre completo:** S&P 500 Materials Sector Index
- **Descripción:** Índice de empresas del sector materiales (minería, químicos, packaging, metales): Dow Chemical, Freeport-McMoRan, Newmont Mining, etc.
- **Ticker Yahoo Finance:** ^GSPMS
- **Unidad:** Puntos del índice
- **Interpretación:**
  - Índice alto: Demanda industrial fuerte (construcción, manufactura) → mayor demanda de metales industriales (cobre, aluminio)
  - Índice bajo: Desaceleración industrial → menor demanda de materias primas
- **Relación con commodities:**
  - **Correlación positiva fuerte** con metales industriales (~0.6-0.7)
  - **Correlación moderada** con metales preciosos (~0.3-0.4)
- **Fuente:** S&P Dow Jones Indices
- **Cobertura:** 1989-presente
- **Archivo:** `data/interim/predictors/materials_index.csv`

---

### 10.6 Inflación (Proxy)

#### TIPS (TIP)
- **Nombre completo:** iShares TIPS Bond ETF
- **Descripción:** ETF que invierte en bonos del Tesoro de EE.UU. protegidos contra inflación (Treasury Inflation-Protected Securities)
- **Ticker Yahoo Finance:** TIP
- **Unidad:** USD por share del ETF
- **Rango histórico:** 90-130 (2007-2025)
- **Interpretación:**
  - TIP en alza: Expectativas inflacionarias crecientes → inversionistas buscan protección
  - Inflación alta → commodities suben como hedge (cobertura)
  - TIP es **proxy** de expectativas inflacionarias, NO inflación realizada
- **Por qué TIPS y no IPC:**
  - Yahoo Finance **no ofrece** series de IPC (Consumer Price Index) directamente
  - FRED API tiene IPC oficial (serie CPIAUCSL), pero requiere API key separada
  - TIP capta expectativas de mercado en tiempo real (IPC es publicación mensual con rezago)
- **Relación con commodities:** Correlación positiva (~0.3-0.5) - inflación alta → commodities suben
- **Referencia académica:** Commodities como hedge inflacionario documentado en literatura ([ResearchGate](https://www.researchgate.net))
- **Fuente:** iShares by BlackRock (ETF inception 2003)
- **Cobertura:** 2003-presente
- **Limitación:** No disponible para período 2000-2003 (ETF no existía)
- **Alternativa futura:** Agregar FRED API y descargar serie CPIAUCSL (IPC oficial mensual)
- **Archivo:** `data/interim/predictors/tips.csv`

---

### 10.7 Variables Derivadas de Predictores (Feature Engineering)

Una vez descargados, los predictores permiten crear features adicionales:

#### spread_10y_2y
- **Descripción:** Pendiente de la curva de rendimiento (Treasury 10Y - Treasury 2Y)
- **Fórmula:** treasury_10y_close - treasury_2y_close
- **Unidad:** Puntos porcentuales (pp)
- **Interpretación:**
  - spread > 0: Curva normal → expansión económica esperada
  - spread < 0: Curva invertida → **recesión esperada** (señal muy confiable históricamente)
  - spread > 2: Expansión fuerte
  - spread < -0.5: Alta probabilidad recesión en 12-18 meses
- **Uso:** Predictor adelantado de ciclo económico

#### dxy_change_pct
- **Descripción:** Cambio porcentual diario del DXY
- **Fórmula:** (dxy_close - dxy_close_lag1) / dxy_close_lag1 × 100
- **Unidad:** Porcentaje
- **Uso:** Capturar movimientos bruscos del dólar (más relevante que nivel absoluto)

#### vix_regime
- **Descripción:** Régimen de volatilidad categórico
- **Fórmula:**
  - 'bajo': VIX < 15
  - 'normal': 15 <= VIX < 30
  - 'alto': 30 <= VIX < 40
  - 'panico': VIX >= 40
- **Tipo:** Categórico (para análisis segmentado)
- **Uso:** Feature para modelos de clasificación

---

### 10.8 Consideraciones de Integración

**Merge strategy en `process.py`:**
```python
# Cargar commodities base
df_commodities = pd.read_csv(PROCESSED_DIR / 'commodities_base_daily.csv')

# Cargar predictores
predictors_files = INTERIM_PREDICTORS_DIR.glob('*.csv')
df_predictors = pd.concat([pd.read_csv(f) for f in predictors_files], ignore_index=True)

# Pivot para tener 1 columna por predictor
df_predictors_pivot = df_predictors.pivot(index='date', columns='predictor', values='close')
df_predictors_pivot.columns = [f'pred_{col.lower()}' for col in df_predictors_pivot.columns]

# Merge por fecha (left join para preservar todas las observaciones de commodities)
df_final = df_commodities.merge(df_predictors_pivot, on='date', how='left')

# Forward-fill predictores (los feriados de mercado USA no afectan precios de commodities fuera de USA)
predictor_cols = [col for col in df_final.columns if col.startswith('pred_')]
df_final[predictor_cols] = df_final.groupby('commodity')[predictor_cols].ffill()
```

**Columnas resultantes en dataset final:**
- `pred_vix` - VIX close
- `pred_sp500` - S&P 500 close
- `pred_dxy` - Dollar Index close
- `pred_usd_brl` - USD/BRL close
- `pred_usd_cny` - USD/CNY close
- `pred_usd_ars` - USD/ARS close
- `pred_treasury_10y` - Treasury 10Y yield
- `pred_treasury_2y` - Treasury 2Y yield
- `pred_energy_index` - Energy Index close
- `pred_materials_index` - Materials Index close
- `pred_tips` - TIPS ETF close

**Total nuevo:** +11 columnas de predictores

**Dataset final:**
- **Columnas anteriores:** 19 (commodities + features)
- **Columnas nuevas:** 11 (predictores macro)
- **Total:** 30 columnas

---

## Referencias de Conversión

### Bushel a Tonelada Métrica
- **Maíz (Corn):** 1 mt = 39.368 bushels → 1 bushel = 0.0254 mt = 25.4 kg
- **Soja (Soybeans):** 1 mt = 36.744 bushels → 1 bushel = 0.0272 mt = 27.2 kg
- **Trigo (Wheat):** 1 mt = 36.744 bushels → 1 bushel = 0.0272 mt = 27.2 kg

### Tamaño de Contratos CME (indicativo)
- **Corn (ZC):** 5.000 bushels = 127 mt
- **Soybeans (ZS):** 5.000 bushels = 136 mt
- **Wheat (ZW):** 5.000 bushels = 136 mt
- **Crude Oil (CL):** 1.000 barrels
- **Gold (GC):** 100 troy ounces
- **Natural Gas (NG):** 10.000 MMBtu

---

## Contacto

**Proyecto:** BigDataUBA-GrupoJLP  
**Repositorio:** https://github.com/paulaleylen/BigDataUBA-GrupoJLP  
**Universidad:** UBA - Facultad de Ciencias Económicas  

**Mantenedores:**
- Paula Leylén Ramirez (@paulaleylen)
- Juan Ignacio Pintos (@juanpintoselso33)
- Luis Mella

**Última actualización:** Octubre 2025
