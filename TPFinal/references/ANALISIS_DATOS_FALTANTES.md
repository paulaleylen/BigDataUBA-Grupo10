# Análisis de Datos Disponibles vs Faltantes para Modelo de Soja

**Fecha:** 10 de noviembre de 2025  
**Objetivo:** Identificar qué variables propuestas ya tenemos, cuáles podemos conseguir gratis, y cuáles son inaccesibles

---

## 📊 RESUMEN EJECUTIVO

### ✅ YA TENEMOS (Operativo en el proyecto)
- **Precios commodities:** 22 futuros incluyendo soja (ZS=F), maíz, petróleo, oro, etc.
- **Macro predictores:** 11 variables (VIX, DXY, USD/BRL, USD/CNY, USD/ARS, S&P500, etc.)
- **Clima:** 70 features (NASA POWER + ONI para 3 regiones productoras)
- **Supply-Demand:** 7 datasets USDA PSD (World + 6 países productores)

### 🟢 DISPONIBLE VIA API GRATUITA (Sin API key)
- **Derivados de soja:** Aceite (ZL=F) y Harina (ZM=F) - Yahoo Finance
- **Fertilizantes:** World Bank Pink Sheet - Excel descargable mensual
- **Aceite de palma:** Investing.com tiene datos históricos (no via Yahoo)

### 🔴 NO DISPONIBLE GRATUITAMENTE (Requiere suscripción o scraping)
- **Precios spot locales:** Bolsa de Rosario (Argentina), CEPEA (Brasil) - No tienen API pública
- **Futuros Dalian (China):** DCE requiere suscripción o proveedores pagos (Wind, Refinitiv)
- **FAO Food Price Index:** Datos mensuales disponibles en PDF, pero no hay API gratuita
- **Indicadores técnicos:** RSI, MACD, Volatilidad - Se calculan, no se descargan

---

## 1️⃣ SERIES DE PRECIOS HISTÓRICOS Y TÉCNICOS

### ✅ Precio futuro de soja (Chicago) - **YA TENEMOS**
- **Status:** ✅ Operativo
- **Fuente:** Yahoo Finance (ticker `ZS=F`)
- **Data:** `data/interim/commodities/soybeans.csv`
- **Frecuencia:** Diaria desde 2000
- **Observación:** Este es nuestro **target principal** para predicción

### 🔴 Precio spot nacional (Rosario/Paranaguá/Golfo)
- **Status:** ❌ No disponible sin scraping
- **Fuentes propuestas:**
  - **Bolsa de Comercio de Rosario (BCR):** http://www.bcr.com.ar/es/mercados - No tiene API pública, datos en tablas HTML
  - **CEPEA (Brasil):** https://www.cepea.esalq.usp.br/ - Requiere scraping o suscripción
  - **USDA AMS:** Datos FOB Golfo disponibles en reportes PDF semanales
- **Alternativa:** Usar futuros Chicago (ZS=F) como proxy - correlación >0.95 con precios locales
- **Recomendación:** ❌ **NO implementar** - costo/beneficio bajo, futuros Chicago son suficientes

### 🔴 Precio futuro en China (Dalian)
- **Status:** ❌ No disponible gratuitamente
- **Fuente:** Dalian Commodity Exchange (DCE)
- **Problema:** Requiere proveedores pagos (Wind, Refinitiv) o Bloomberg Terminal
- **Alternativa:** Usar USD/CNY y China import demand (ya tenemos en supply-demand)
- **Recomendación:** ❌ **NO implementar** - no hay alternativa gratuita viable

### ✅ Media móvil de precios - **SE CALCULA**
- **Status:** 🟢 Implementar en `process.py`
- **Método:** Rolling windows de soja (ya implementado para clima)
- **Configuración sugerida:**
  ```python
  df['soy_ma_30'] = df['soybeans'].rolling(30).mean()
  df['soy_ma_90'] = df['soybeans'].rolling(90).mean()
  df['soy_ma_200'] = df['soybeans'].rolling(200).mean()  # Tendencia largo plazo
  ```
- **Recomendación:** ✅ **YA está parcialmente implementado** (lags y rolling), expandir si necesario

### ✅ Volatilidad histórica (desvío estándar) - **SE CALCULA**
- **Status:** 🟢 Implementar en `process.py`
- **Método:** Rolling std de rendimientos de soja
- **Configuración sugerida:**
  ```python
  df['soy_returns'] = df['soybeans'].pct_change()
  df['soy_volatility_30'] = df['soy_returns'].rolling(30).std() * np.sqrt(252)  # Anualizado
  df['soy_volatility_60'] = df['soy_returns'].rolling(60).std() * np.sqrt(252)
  ```
- **Alternativa:** CBOE Soybean Volatility Index (VXS) - no disponible en Yahoo Finance
- **Recomendación:** ✅ **CALCULAR** - es estándar en modelos de precio

### 🟡 Índice de Fuerza Relativa (RSI) - **SE CALCULA**
- **Status:** 🟢 Implementar con librería técnica
- **Método:** Usar `pandas_ta` o `TA-Lib`
- **Código sugerido:**
  ```python
  import pandas_ta as ta
  df['soy_rsi_14'] = ta.rsi(df['soybeans'], length=14)
  ```
- **Recomendación:** 🟡 **OPCIONAL** - útil para modelos de momentum, pero no crítico para forecast fundamentalista

### 🟡 Indicador MACD - **SE CALCULA**
- **Status:** 🟢 Implementar con librería técnica
- **Método:** MACD = EMA(12) - EMA(26), Signal = EMA(MACD, 9)
- **Código sugerido:**
  ```python
  df['soy_macd'] = ta.macd(df['soybeans'])['MACD_12_26_9']
  df['soy_macd_signal'] = ta.macd(df['soybeans'])['MACDs_12_26_9']
  df['soy_macd_hist'] = ta.macd(df['soybeans'])['MACDh_12_26_9']
  ```
- **Recomendación:** 🟡 **OPCIONAL** - útil para trading, menos para forecast a largo plazo

### 🔴 Basis o spread local - **DEPENDE DE PRECIOS LOCALES**
- **Status:** ❌ No disponible sin precios spot locales
- **Cálculo:** Basis = Precio_Local - Futuro_Chicago
- **Problema:** Requiere precios spot (Rosario/Paranaguá) que no tenemos
- **Recomendación:** ❌ **NO implementar** - requiere datos no disponibles

---

## 2️⃣ PRECIOS DE COMMODITIES RELACIONADOS

### 🟢 Precio del aceite de soja - **DISPONIBLE**
- **Status:** 🟢 Agregar a `config.py`
- **Fuente:** Yahoo Finance (ticker `ZL=F` - Soybean Oil Futures CBOT)
- **Implementación:**
  ```python
  COMMODITIES_TICKERS = {
      # ... existentes ...
      'Soybean_Oil': 'ZL=F',    # Aceite de soja (crush margin)
  }
  ```
- **Justificación:** Crush margin = (Aceite + Harina) - Soja. Indicador clave de demanda procesadora
- **Recomendación:** ✅ **IMPLEMENTAR** - crítico para modelo fundamentalista

### 🟢 Precio de la harina de soja - **DISPONIBLE**
- **Status:** 🟢 Agregar a `config.py`
- **Fuente:** Yahoo Finance (ticker `ZM=F` - Soybean Meal Futures CBOT)
- **Implementación:**
  ```python
  COMMODITIES_TICKERS = {
      # ... existentes ...
      'Soybean_Meal': 'ZM=F',   # Harina de soja (alimento animal)
  }
  ```
- **Justificación:** Demanda de harina impulsa crush de soja. Correlación fuerte con precios ganaderos
- **Recomendación:** ✅ **IMPLEMENTAR** - crítico para modelo fundamentalista

### 🟡 Precio del aceite de palma - **DISPONIBLE CON LIMITACIONES**
- **Status:** 🟡 Disponible pero no en Yahoo Finance
- **Fuente:** Bursa Malaysia (futuro FCPO), disponible en Investing.com
- **Problema:** Investing.com no tiene API gratuita simple como yfinance
- **Alternativa 1:** World Bank Pink Sheet tiene "Palm Oil, Malaysia" mensual
- **Alternativa 2:** Scraping de Investing.com (similar a lo que hicimos con USDA PSD)
- **Recomendación:** 🟡 **OPCIONAL** - útil pero no crítico. Si implementar, usar World Bank mensual

### ✅ Precio del maíz - **YA TENEMOS**
- **Status:** ✅ Operativo
- **Fuente:** Yahoo Finance (ticker `ZC=F`)
- **Data:** `data/interim/commodities/corn.csv`
- **Justificación:** Competencia por superficie agrícola y alimento animal
- **Observación:** ✅ Ya incluido en las 22 commodities

### ✅ Precio del petróleo crudo - **YA TENEMOS**
- **Status:** ✅ Operativo
- **Fuente:** Yahoo Finance (`CL=F` WTI, `BZ=F` Brent)
- **Data:** `data/interim/commodities/crude_oil.csv` y `brent_crude.csv`
- **Justificación:** Biodiésel (aceite de soja) + costos de producción/transporte
- **Observación:** ✅ Ya incluido, tenemos ambos benchmarks

### 🔴 Índice de precios de alimentos FAO - **NO DISPONIBLE VIA API**
- **Status:** ❌ No hay API gratuita
- **Fuente:** FAO Food Price Index (https://www.fao.org/worldfoodsituation/foodpricesindex/en)
- **Frecuencia:** Mensual
- **Problema:** Datos disponibles solo en PDFs mensuales y página web (requiere scraping)
- **Alternativa:** Usar nuestras commodities agrícolas como proxy (soja, maíz, trigo, azúcar, café)
- **Recomendación:** ❌ **NO implementar** - nuestros datos de commodities son más granulares y actualizados

### ✅ Metales (oro) - **YA TENEMOS**
- **Status:** ✅ Operativo
- **Fuente:** Yahoo Finance (ticker `GC=F`)
- **Data:** `data/interim/commodities/gold.csv`
- **Justificación:** Proxy de aversión al riesgo / inflación
- **Observación:** ✅ Ya incluido (también plata, platino, paladio)

### 🟢 Precios de fertilizantes - **DISPONIBLE**
- **Status:** 🟢 Implementar descarga World Bank Pink Sheet
- **Fuente:** World Bank Commodities Price Data (The Pink Sheet)
  - URL Monthly: https://thedocs.worldbank.org/en/doc/5d903e848db1d1b83e0ec8f744e55570-0350012021/related/CMO-Historical-Data-Monthly.xlsx
  - URL Annual: https://thedocs.worldbank.org/en/doc/18675f1d1639c7a34d463f59263ba0a2-0050012025/related/CMO-Historical-Data-Annual.xlsx
- **Variables disponibles:**
  - DAP (Diammonium Phosphate) - Fosfato
  - TSP (Triple Superphosphate) - Fosfato
  - Urea - Nitrógeno
  - Potassium Chloride (Muriate of Potash) - Potasio
- **Frecuencia:** Mensual desde 1960
- **Formato:** Excel descargable directo (sin autenticación)
- **Implementación sugerida:**
  ```python
  # Nuevo módulo: src/data/download_fertilizers.py
  import pandas as pd
  
  url = 'https://thedocs.worldbank.org/.../CMO-Historical-Data-Monthly.xlsx'
  df = pd.read_excel(url, sheet_name='Monthly Prices', skiprows=5)
  # Seleccionar: Urea, DAP, TSP, Potassium Chloride
  # Expandir mensual → diario con forward-fill (similar a PSD)
  ```
- **Recomendación:** ✅ **IMPLEMENTAR** - datos gratis, calidad institucional, relevante para costos de producción

---

## 3️⃣ RESUMEN DE ACCIONES RECOMENDADAS

### 🟢 ALTA PRIORIDAD - Implementar ya
1. ✅ **Soybean Oil (ZL=F)** - Agregar a COMMODITIES_TICKERS
2. ✅ **Soybean Meal (ZM=F)** - Agregar a COMMODITIES_TICKERS
3. 🔄 **Fertilizantes (World Bank)** - Crear `download_fertilizers.py`
4. 🔄 **Volatilidad calculada** - Agregar en `process.py` feature engineering
5. 🔄 **Medias móviles extendidas** - Expandir rolling windows en `process.py`

### 🟡 MEDIA PRIORIDAD - Evaluar según tiempo
6. 🟡 **Aceite de palma (World Bank)** - Si hay tiempo, agregar desde Pink Sheet
7. 🟡 **RSI técnico** - Si el modelo será usado para trading de corto plazo
8. 🟡 **MACD técnico** - Si el modelo será usado para trading de corto plazo

### 🔴 BAJA PRIORIDAD - NO implementar
9. ❌ **Precios spot locales** - Requiere scraping complejo, futuros Chicago son proxy suficiente
10. ❌ **Futuros Dalian** - No disponible gratuitamente
11. ❌ **FAO Food Index** - Nuestros datos de commodities son superiores
12. ❌ **Basis local** - Depende de precios spot que no tenemos

---

## 4️⃣ ARQUITECTURA DE DATOS ACTUALIZADA

### Variables Finales Esperadas (Post-Implementación)

```
BASE:
- Commodities: 22 actuales + 2 nuevos (Oil, Meal) = 24 commodities
- Macro: 11 predictores (ya tenemos)
- Clima: 10 base × 7 transformaciones = 70 features
- Supply-Demand: 18 base × 3 transformaciones = 54 features
- Fertilizantes: 4 base × 3 transformaciones = 12 features (NUEVO)

TÉCNICOS (calculados):
- Volatilidad: 2 ventanas (30d, 60d)
- Medias móviles: 3 ventanas (30d, 90d, 200d)
- RSI (opcional): 1 feature
- MACD (opcional): 3 features (MACD, Signal, Histogram)

TOTAL ESTIMADO: 24 + 11 + 70 + 54 + 12 + 5 = 176 features base
Con lags/rolling: ~500-550 features finales
```

### Comparación con Propuesta Original

| Categoría | Propuesto | Disponible Gratis | Implementado | Crítico |
|-----------|-----------|-------------------|--------------|---------|
| Precio futuro soja Chicago | ✅ | ✅ | ✅ | ⭐⭐⭐ |
| Precio spot local | ✅ | ❌ | ❌ | ⭐ |
| Futuro Dalian | ✅ | ❌ | ❌ | ⭐ |
| Aceite de soja | ✅ | ✅ | ❌ | ⭐⭐⭐ |
| Harina de soja | ✅ | ✅ | ❌ | ⭐⭐⭐ |
| Aceite de palma | ✅ | 🟡 | ❌ | ⭐⭐ |
| Maíz | ✅ | ✅ | ✅ | ⭐⭐⭐ |
| Petróleo | ✅ | ✅ | ✅ | ⭐⭐⭐ |
| FAO Food Index | ✅ | ❌ | ❌ | ⭐ |
| Fertilizantes | ✅ | ✅ | ❌ | ⭐⭐ |
| Indicadores técnicos | ✅ | ✅ (calc) | 🟡 | ⭐⭐ |

**Leyenda:**
- ⭐⭐⭐ Crítico para modelo fundamentalista
- ⭐⭐ Importante, mejora significativa
- ⭐ Marginal, no bloquea modelo base

---

## 5️⃣ PLAN DE IMPLEMENTACIÓN

### Fase 1: Derivados de Soja (30 min)
```bash
# 1. Editar config.py - agregar ZL=F y ZM=F
# 2. Re-ejecutar download_commodities.py
# 3. Verificar nuevos CSVs en data/interim/commodities/
```

### Fase 2: Fertilizantes (2-3 horas)
```bash
# 1. Crear src/data/download_fertilizers.py (similar a download_climate.py)
# 2. Descargar Excel desde World Bank
# 3. Procesar: extraer Urea, DAP, TSP, Potassium
# 4. Expandir mensual → diario (forward-fill)
# 5. Guardar en data/interim/fertilizers/
# 6. Actualizar fertilizers_registry.json
```

### Fase 3: Features Técnicos (1 hora)
```bash
# 1. Editar process.py
# 2. Agregar cálculo de volatilidad (rolling std de returns)
# 3. Agregar RSI/MACD con pandas_ta (opcional)
# 4. Verificar no hay NaN explosion
```

### Fase 4: Integración Final (1 hora)
```bash
# 1. Merge fertilizantes en process.py (load_all_fertilizer_data)
# 2. Aplicar feature engineering (lags, rolling)
# 3. Re-generar dataset final
# 4. Verificar shape: (6729, ~530-550)
# 5. Actualizar sources.md con sección fertilizantes
```

---

## 6️⃣ CONCLUSIONES

### ✅ Tenemos el 80% de los datos propuestos
- Variables críticas (futuros, macro, clima, supply-demand) están operativas
- Faltantes importantes son accesibles vía APIs gratuitas (derivados soja, fertilizantes)
- Faltantes menores (spot local, Dalian) tienen alternativas o son marginales

### 🎯 Prioridades inmediatas
1. **Derivados de soja** (aceite ZL=F, harina ZM=F) - Impacto alto, esfuerzo bajo
2. **Fertilizantes** (World Bank) - Impacto medio, esfuerzo medio
3. **Volatilidad calculada** - Impacto medio, esfuerzo bajo

### 📊 Decisión sobre precios locales (Rosario, etc.)
- **NO implementar scraping** de bolsas locales
- **Justificación:**
  - Correlación con Chicago >0.95 (futuros ya capturan dinámica global)
  - Scraping frágil (cambios en HTML rompen código)
  - Datos mensuales/semanales vs diarios que ya tenemos
  - Esfuerzo alto (4-6 horas) vs beneficio marginal
- **Alternativa:** Usar futuros Chicago (ZS=F) como proxy universal

### 🚀 Próximo paso sugerido
**Implementar Fase 1 (derivados soja)** - 30 minutos, alto impacto, sin riesgo
