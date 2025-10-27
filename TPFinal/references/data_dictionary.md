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
