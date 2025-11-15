# Análisis de Datos Adicionales: Factores de Mercado y Geopolíticos

**Fecha:** 10 de noviembre de 2025  
**Objetivo:** Evaluar viabilidad de integrar variables de sentimiento de mercado, logística y políticas

---

## 📊 RESUMEN EJECUTIVO

### ✅ DISPONIBLE GRATUITAMENTE
- **Baltic Dry Index:** Yahoo Finance (ticker `BDI` o `^BDI`)
- **USDA Crop Conditions:** Reportes semanales PDF (scraping viable)

### 🟡 DISPONIBLE CON LIMITACIONES
- **CFTC COT Reports:** Datos públicos semanales (scraping CSV)
- **CME Open Interest/Volume:** Datos públicos pero requiere scraping

### 🔴 NO RECOMENDADO PARA IMPLEMENTACIÓN
- **Políticas gubernamentales:** Requiere construcción manual de dummies
- **Eventos geopolíticos:** Datos cualitativos, difícil automatizar
- **Indicadores China específicos:** APIs pagos o datos dispersos

---

## 1️⃣ POSICIONES DE ESPECULADORES (CFTC)

### 📋 Commitments of Traders (COT) Report

**Status:** 🟡 Disponible público pero requiere scraping

**Descripción:**
- Reporte semanal de posiciones netas de fondos especulativos, comerciales y pequeños traders
- Publica todos los viernes (datos al martes anterior)
- Categorías: Managed Money (especuladores), Producers/Merchants, Swap Dealers

**Variables útiles:**
- Net Long Positions (Managed Money) - Especulación alcista
- Net Short Positions - Especulación bajista
- Open Interest Total - Interés en el mercado
- Change from Previous Week - Momentum

**Fuentes:**
1. **CFTC Official:** https://www.cftc.gov/dea/futures/deacmesf.htm
   - Formato: TXT delimitado por espacios (difícil de parsear)
   - Histórico disponible en ZIP: https://www.cftc.gov/MarketReports/CommitmentsofTraders/HistoricalCompressed/index.htm
   
2. **Alternativa - Quandl/Nasdaq Data Link:**
   - Dataset: `CFTC/SOYBEAN_FO_L_ALL` (Soybeans - Legacy Format)
   - Requiere API key (gratuita con límite)
   
3. **Python Library:**
   ```bash
   pip install cftc-api
   ```
   - Librería no oficial que parsea los reportes CFTC
   - Última actualización: 2023 (puede estar desactualizada)

**Implementación recomendada:**

```python
# Opción 1: Scraping directo del CSV comprimido
import pandas as pd
import zipfile
import requests
from io import BytesIO

url = 'https://www.cftc.gov/files/dea/history/fut_fin_txt_2025.zip'
response = requests.get(url)
with zipfile.ZipFile(BytesIO(response.content)) as z:
    with z.open('annual.txt') as f:
        df = pd.read_csv(f, delimiter=',')

# Filtrar Soybeans (CFTC Code: 005602)
df_soy = df[df['CFTC_Contract_Market_Code'] == '005602']
```

**Frecuencia:** Semanal (actualización cada viernes)

**Valor agregado:**
- ⭐⭐⭐ Sentimiento de mercado (contrarian indicator)
- Útil para modelos de momentum/timing
- Menos crítico para forecast fundamentalista de largo plazo

**Recomendación:** 🟡 **IMPLEMENTAR SI HAY TIEMPO** - Alta señal pero complejidad media de scraping

---

## 2️⃣ VOLUMEN Y OPEN INTEREST

### 📊 CME/CBOT Market Data

**Status:** 🟡 Disponible público vía CME Group

**Descripción:**
- Volumen diario de contratos operados
- Open Interest (contratos abiertos totales al cierre)
- Regla: OI↑ + Precio↑ = Tendencia alcista confirmada

**Fuentes:**
1. **CME Group Official:** https://www.cmegroup.com/markets/agriculture/oilseeds/soybean.html
   - Datos diarios disponibles
   - Requiere scraping HTML/JavaScript rendering
   
2. **Barchart:** https://www.barchart.com/futures/quotes/ZSH25/interactive-chart
   - Datos históricos disponibles
   - Requiere suscripción para API

3. **Yahoo Finance:** Incluye Volume en datos de futuros
   - Ticker: `ZS=F` (Soybean Futures)
   - Ya lo tenemos descargado! ✅

**Implementación:**

```python
# YA DISPONIBLE EN NUESTROS DATOS
df_soy = pd.read_csv('data/interim/commodities/soybeans.csv')
# Columnas: date, open, high, low, close, volume, commodity
# Volume ya está incluido!
```

**Valor agregado:**
- ⭐⭐ Confirmación técnica de tendencias
- Útil para modelos de trading de corto plazo
- Menos relevante para forecast fundamentalista

**Recomendación:** ✅ **YA DISPONIBLE** - Volume está en nuestros datos de Yahoo Finance

---

## 3️⃣ ÍNDICE BALTIC DRY (FLETES)

### 🚢 Baltic Dry Index (BDI)

**Status:** 🟢 Disponible vía Yahoo Finance

**Descripción:**
- Índice de costos de flete marítimo de carga seca (granos, minerales)
- Proxy de demanda global de commodities
- Soja exportada vía marítimo → fletes altos encarecen logística

**Ticker:** `^BDI` o `BDI` (Yahoo Finance)

**Implementación:**

```python
# Agregar a config.py
COMMODITIES_TICKERS = {
    # ... existentes ...
    'Baltic_Dry_Index': '^BDI',  # Costo de fletes marítimos
}
```

**Frecuencia:** Diaria

**Valor agregado:**
- ⭐⭐⭐ Proxy de demanda global y salud comercio
- Afecta competitividad de exportadores (Argentina, Brasil)
- Correlacionado con ciclo económico global

**Recomendación:** ✅ **IMPLEMENTAR** - Fácil (30 min), alto impacto

---

## 4️⃣ POLÍTICAS GUBERNAMENTALES

### 📜 Export Taxes, Biodiésel Mandates, Trade Restrictions

**Status:** 🔴 No automatizable - Requiere construcción manual

**Variables típicas:**
- **Retenciones Argentina:** 33% (2018-2019), 0% (2019), 30% (2020-2023)
- **Biodiésel mandates USA:** B2 (2004), B5 (2010), B10 (2015+)
- **China import quotas:** Cupos TRQ (tariff-rate quota)

**Implementación:**

```python
# Ejemplo: Dummy de retenciones argentinas
df['arg_export_tax'] = 0
df.loc[(df['date'] >= '2018-09-01') & (df['date'] < '2019-12-10'), 'arg_export_tax'] = 33
df.loc[(df['date'] >= '2020-12-15'), 'arg_export_tax'] = 30

# Ejemplo: Dummy guerra comercial USA-China
df['us_china_trade_war'] = 0
df.loc[(df['date'] >= '2018-07-06') & (df['date'] < '2020-01-15'), 'us_china_trade_war'] = 1
```

**Fuentes:**
- **Argentina:** Boletín Oficial (https://www.boletinoficial.gob.ar/)
- **USA:** RFA (Renewable Fuels Association) para biodiésel
- **China:** USDA FAS GAIN Reports (Global Agricultural Information Network)

**Valor agregado:**
- ⭐⭐⭐ Alto impacto en precios cuando ocurren
- Variables cualitativas tipo evento
- Dificultad: construcción manual de timeline

**Recomendación:** 🟡 **OPCIONAL** - Alto impacto pero requiere research manual extenso (5-10 horas)

---

## 5️⃣ EVENTOS GEOPOLÍTICOS

### 🌍 Trade Wars, Conflicts, Sanctions

**Status:** 🔴 No automatizable - Eventos cualitativos

**Eventos históricos relevantes:**
- **2018-2020:** Guerra comercial USA-China (aranceles 25% soja USA)
- **2022-2025:** Invasión Ucrania (disrupts aceite girasol → sube aceite soja)
- **2019:** Fiebre porcina africana China (reduce demanda harina soja)

**Implementación:**

```python
# Timeline de eventos clave (construcción manual)
geopolitical_events = {
    'us_china_trade_war': ('2018-07-06', '2020-01-15'),
    'ukraine_war': ('2022-02-24', None),  # Ongoing
    'african_swine_fever': ('2018-08-01', '2020-12-31')
}

for event, (start, end) in geopolitical_events.items():
    df[event] = 0
    mask = df['date'] >= start
    if end:
        mask &= df['date'] <= end
    df.loc[mask, event] = 1
```

**Fuentes:**
- Bloomberg/Reuters timeline
- USDA FAS Attaché Reports
- Research manual de papers académicos

**Valor agregado:**
- ⭐⭐⭐ Impacto estructural en mercados
- Captura shocks exógenos
- Dificultad: identificar fechas exactas y cuantificar impacto

**Recomendación:** 🟡 **OPCIONAL** - Alto valor pero requiere research histórico (5-8 horas)

---

## 6️⃣ OTROS GRANOS (ARROZ, CEBADA)

### 🌾 Rice, Barley Prices

**Status:** 🟢 Disponible pero poco útil para soja

**Justificación NO implementar:**
- Arroz y cebada tienen poca correlación con soja
- Arroz: mercados asiáticos, consumo humano directo
- Cebada: cervecería + alimento animal (compite con maíz, no soja)
- Ya tenemos maíz y trigo que capturan dinámica de granos

**Si se requiere:**
- FAO Rice Price Index: https://www.fao.org/worldfoodsituation/foodpricesindex/en
- Euronext Barley Futures: No disponible en Yahoo Finance

**Recomendación:** ❌ **NO IMPLEMENTAR** - Bajo valor agregado, ya tenemos granos principales

---

## 7️⃣ INDICADORES ECONÓMICOS DE CHINA

### 🇨🇳 China GDP, Pork Production, FX Reserves

**Status:** 🟡 Disponible pero disperso

**Variables potenciales:**
- **GDP China:** Trimestral, NBS China o World Bank
- **Pork Production:** Mensual, NBS China (afecta demanda harina soja)
- **FX Reserves:** Mensual, PBOC (capacidad de importación)

**Problema:** 
- Frecuencia baja (trimestral/mensual)
- Ya tenemos USD/CNY que captura dinámica FX
- China imports en supply-demand captura demanda

**Fuentes:**
- **NBS China:** http://www.stats.gov.cn/english/ (oficial)
- **World Bank:** GDP trimestral
- **USDA PSD:** Ya tenemos China imports!

**Implementación si se requiere:**

```python
# Ejemplo: GDP China trimestral
import pandas_datareader as pdr
china_gdp = pdr.get_data_fred('MKTGDPCNA646NWDB', start='2000')  # World Bank via FRED
# Expandir trimestral → diario con forward-fill
```

**Valor agregado:**
- ⭐⭐ Moderado - demanda China ya capturada en imports (PSD)
- USD/CNY ya refleja condiciones macroeconómicas

**Recomendación:** ❌ **NO IMPLEMENTAR** - Ya tenemos proxies suficientes (USD/CNY, China imports)

---

## 8️⃣ USDA CROP CONDITION INDEX

### 🌱 Good/Excellent Percentage - Weekly

**Status:** 🟡 Disponible público (scraping PDF/TXT)

**Descripción:**
- USDA NASS publica semanalmente % de cultivo en condiciones "Good" o "Excellent"
- Ejemplo: "65% soybean good-to-excellent" (vs 67% año anterior)
- Deterioro indica probable recorte de producción → precio sube

**Fuente:** 
- USDA NASS Crop Progress: https://usda.library.cornell.edu/concern/publications/8336h188j
- Formato: PDF semanal (lunes afternoon)
- También disponible en Quick Stats: https://quickstats.nass.usda.gov/

**Implementación:**

**Opción 1: Scraping PDF**
```python
import pdfplumber
import requests

url = 'https://release.nass.usda.gov/reports/prog3925.pdf'  # Ejemplo Sept 29
with pdfplumber.open(requests.get(url, stream=True).raw) as pdf:
    text = pdf.pages[0].extract_text()
    # Parse: "Soybeans ... 65 percent good to excellent"
```

**Opción 2: Quick Stats API**
```python
# USDA NASS Quick Stats API (requiere API key gratuita)
api_key = 'YOUR_KEY'
url = f'https://quickstats.nass.usda.gov/api/api_GET/?key={api_key}&commodity_desc=SOYBEANS&statisticcat_desc=CONDITION&freq_desc=WEEKLY'
```

**Frecuencia:** Semanal (abril-octubre)

**Valor agregado:**
- ⭐⭐⭐ Predictor líder de rendimiento final
- Correlación histórica fuerte con precio
- Útil para modelos de cosecha (mayo-septiembre)

**Dificultad:** Media - scraping PDF o API registration

**Recomendación:** 🟡 **IMPLEMENTAR SI HAY TIEMPO** - Alto valor durante temporada de cultivo

---

## 3️⃣ RESUMEN DE PRIORIDADES

### 🟢 ALTA PRIORIDAD - Implementar ya (1-2 horas cada uno)

1. ✅ **Baltic Dry Index (^BDI)** 
   - Agregar a COMMODITIES_TICKERS
   - 30 minutos, impacto alto

**Código:**
```python
# config.py
COMMODITIES_TICKERS = {
    # ... existentes ...
    'Baltic_Dry_Index': '^BDI',  # Fletes marítimos
}
```

### 🟡 MEDIA PRIORIDAD - Evaluar según tiempo (3-5 horas cada uno)

2. 🟡 **CFTC Commitments of Traders**
   - Sentimiento de especuladores
   - Requiere scraping CSV semanal
   - Útil para modelos de momentum

3. 🟡 **USDA Crop Conditions**
   - Predictor líder de rendimiento
   - Requiere scraping PDF o API registration
   - Útil abril-octubre (temporada cultivo)

### 🔴 BAJA PRIORIDAD - NO implementar ahora

4. ❌ **Políticas gubernamentales** - Construcción manual (5-10 horas)
5. ❌ **Eventos geopolíticos** - Research histórico (5-8 horas)
6. ❌ **Otros granos** (arroz, cebada) - Bajo valor agregado
7. ❌ **Indicadores China** - Ya tenemos proxies (USD/CNY, imports)
8. ✅ **Volume/Open Interest** - YA DISPONIBLE en datos actuales

---

## 4️⃣ PLAN DE IMPLEMENTACIÓN RECOMENDADO

### Fase 1: Baltic Dry Index (30 min) ⭐⭐⭐

```bash
# 1. Agregar ^BDI a config.py
# 2. Re-ejecutar download_commodities.py
# 3. Verificar nuevo CSV en data/interim/commodities/
# 4. Process.py automáticamente lo incluirá
```

**Impacto:** +1 commodity, +~5 features (lag, rolling, return)  
**Dataset final:** 6,729 × 597 (de 592)

### Fase 2: CFTC COT (si hay tiempo, 3-4 horas)

```bash
# 1. Crear download_cftc_cot.py
# 2. Descargar ZIP histórico desde CFTC
# 3. Parsear TXT → CSV, filtrar Soybeans
# 4. Resamplear semanal → diario (forward-fill)
# 5. Agregar Net Long/Short positions
# 6. Integrar en process.py
```

**Impacto:** +4 variables base × 6 transformaciones = +24 features  
**Dataset final:** 6,729 × 621

### Fase 3: USDA Crop Conditions (si hay tiempo, 3-4 horas)

```bash
# 1. Registrar API key en USDA NASS Quick Stats
# 2. Crear download_crop_conditions.py
# 3. Descargar Good/Excellent % semanal
# 4. Resamplear semanal → diario (forward-fill)
# 5. Agregar a process.py como "Crop_Condition_Pct"
```

**Impacto:** +1 variable × 6 transformaciones = +6 features  
**Dataset final:** 6,729 × 627

---

## 5️⃣ ARQUITECTURA FINAL ESTIMADA

### Con Baltic Dry Index (mínimo)

```
DATASET FINAL:
- Filas: 6,729 (2000-01-03 a 2025-11-10)
- Columnas: 597
  * 25 commodities (24 actuales + BDI)
  * 11 macro
  * 10 climate
  * 20 supply-demand
  * 6 temporales
  = 72 variables base × ~8 transformaciones = 576 features
  + 6 temporales + 1 date
  = 597 columnas
```

### Con CFTC + Crop Conditions (completo)

```
DATASET FINAL:
- Filas: 6,729
- Columnas: 627
  * 25 commodities
  * 11 macro
  * 10 climate
  * 20 supply-demand
  * 4 CFTC (Net Long, Net Short, Open Interest, Change)
  * 1 Crop Condition
  * 6 temporales
  = 77 variables base × ~8 transformaciones = 616 features
  + 6 temporales + 1 date + 4 CFTC no-transformed
  = 627 columnas
```

---

## 6️⃣ CONCLUSIONES

### ✅ Implementar Inmediatamente

1. **Baltic Dry Index** - 30 min, bajo riesgo, alto impacto
   - Captura costos logísticos globales
   - Proxy de demanda commodities
   - Trivial de integrar (Yahoo Finance)

### 🟡 Considerar Si Hay Tiempo

2. **CFTC COT** - Si modelo incluye sentiment/momentum
   - Útil para trading de corto plazo
   - Menos crítico para forecast fundamentalista
   - Scraping medio complejo

3. **USDA Crop Conditions** - Si modelo es intra-año (abril-octubre)
   - Predictor líder de rendimiento
   - Útil solo durante temporada cultivo
   - API registration required

### ❌ NO Implementar Ahora

4. **Políticas/Geopolítica** - Requiere research manual extenso
5. **Indicadores China específicos** - Ya tenemos proxies
6. **Otros granos secundarios** - Bajo valor agregado
7. **Volume/OI** - Ya disponible en datos actuales ✅

---

## 7️⃣ RECOMENDACIÓN FINAL

**Opción A: Minimalista (30 min)**
- Agregar solo Baltic Dry Index
- Dataset: 6,729 × 597
- Listo para modelado

**Opción B: Completo (8-10 horas)**
- BDI + CFTC + Crop Conditions
- Dataset: 6,729 × 627
- Máximo poder predictivo

**Mi sugerencia:** **Opción A primero**, luego evaluar importancia de features. Si BDI no agrega valor, no tiene sentido agregar CFTC/Crop Conditions.

---

**¿Procedemos con Opción A (Baltic Dry Index)?** Es 30 minutos y bajo riesgo.
