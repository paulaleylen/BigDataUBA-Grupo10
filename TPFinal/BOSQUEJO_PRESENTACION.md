# Bosquejo Presentación - Base de Datos de Commodities
## Trabajo Práctico Final | Taller de Programación | UBA - FCE

**Grupo JLP** | Fecha de presentación: Miércoles  
**Objetivo:** Presentar la construcción de una base de datos escalable para predicción de precios de commodities

---

## SLIDE 1: Portada
**Título:** Base de Datos de Commodities para Análisis Predictivo  
**Subtítulo:** Pipeline Automatizado de Descarga, Procesamiento y Feature Engineering  
**Integrantes:** [Nombres del grupo]  
**Materia:** Taller de Programación | UBA - Facultad de Ciencias Económicas  
**Fecha:** Noviembre 2025

---

## SLIDE 2: Contexto del Proyecto

### Motivación
- Los precios de commodities (granos, energía, metales) son críticos para la economía argentina
- Necesidad de herramientas cuantitativas para análisis y predicción
- Problema: datos dispersos en múltiples fuentes, formatos inconsistentes

### Objetivo del Trabajo
**Construir una base de datos consolidada, limpia y lista para modelado predictivo**

### Alcance
- 22 commodities (granos, energía, metales, softs, ganado, madera)
- 5 predictores macroeconómicos (VIX, DXY, S&P500, tasas, índices sectoriales)
- 25 años de historia (2000-2025)
- 6,537 días de trading
- 250 features (precios + lags + rolling stats + retornos)

---

## SLIDE 3: Arquitectura del Proyecto

### Estructura Modular - Cookiecutter Data Science
```
TPFinal/
├── src/                      # Código reutilizable
│   ├── config.py            # Configuración centralizada
│   └── data/                # Módulos de descarga y procesamiento
├── data/                    # Datos (raw → interim → processed)
├── notebooks/               # Exploración y análisis
├── reports/figures/         # Visualizaciones
└── references/              # Documentación
```

### Ventajas de la Estructura Modular
1. **Código DRY (Don't Repeat Yourself):** Funciones en `src/` reutilizables desde cualquier notebook
2. **Colaboración:** Cambios centralizados benefician a todo el equipo
3. **Reproducibilidad:** Pipeline automatizado ejecutable en cualquier entorno
4. **Escalabilidad:** Fácil agregar nuevos commodities o features

---

## SLIDE 4: Pipeline de Datos - Visión General

### 3 Etapas del Pipeline

**1. DESCARGA (Download)**
- `download_commodities.py` → 22 commodities desde Yahoo Finance
- `download_predictors.py` → 5 predictores macro desde Yahoo Finance
- **Output:** 27 archivos CSV individuales en `data/interim/`

**2. PROCESAMIENTO (Process)**
- `process.py` → Consolidación, limpieza, feature engineering
- **Output:** Dataset unificado `commodities_base_daily.csv` (6,537 × 250)

**3. EXPLORACIÓN (Explore)**
- Notebooks Jupyter → Análisis, correlaciones, visualizaciones
- **Output:** Insights y gráficos para toma de decisiones

### Tiempo de Ejecución
- Descarga completa: ~3 minutos
- Procesamiento: ~30 segundos
- **Total: < 5 minutos** para regenerar base completa

---

## SLIDE 5: Fuentes de Datos - Yahoo Finance

### ¿Por qué Yahoo Finance?
- **Gratuito:** Sin API keys ni límites de requests
- **Histórico completo:** Datos desde año 2000
- **Actualizado:** Datos hasta el día actual
- **Confiable:** Fuente estándar en la industria financiera

### Biblioteca yfinance
```python
import yfinance as yf

# Ejemplo: Descargar oro desde 2000
df = yf.download('GC=F', start='2000-01-01')
```

### Cobertura Temporal
- **Inicio:** 3 de enero de 2000 (primer día de trading del siglo XXI)
- **Fin:** 27 de octubre de 2025 (hoy)
- **Total:** 25 años, 9,429 días calendario, 6,537 días hábiles

---

## SLIDE 6: Commodities Descargados (22 en Total)

### Granos (CBOT - Chicago Board of Trade)
- **Corn (ZC=F):** Maíz - Fundamental para Argentina como exportador
- **Soybeans (ZS=F):** Soja - Principal commodity de exportación argentino
- **Wheat (ZW=F):** Trigo - Cultivo clave para el país
- **Oat (ZO=F):** Avena

### Energía (NYMEX/ICE)
- **Crude Oil (CL=F):** Petróleo WTI - Referencia global
- **Brent Crude (BZ=F):** Petróleo Brent - Benchmark europeo
- **Natural Gas (NG=F):** Gas natural - Energía y fertilizantes
- **Heating Oil (HO=F):** Gasoil
- **RBOB Gasoline (RB=F):** Nafta

### Metales Preciosos (COMEX)
- **Gold (GC=F):** Oro - Refugio de valor
- **Silver (SI=F):** Plata - Dual: industrial + reserva
- **Platinum (PL=F):** Platino
- **Palladium (PA=F):** Paladio

---

## SLIDE 7: Commodities (continuación) + Predictores

### Metales Industriales
- **Copper (HG=F):** Cobre - Indicador económico global (construcción, electrónica)

### Softs (ICE - Intercontinental Exchange)
- **Coffee (KC=F):** Café
- **Sugar (SB=F):** Azúcar
- **Cotton (CT=F):** Algodón
- **Cocoa (CC=F):** Cacao

### Ganado (CME)
- **Live Cattle (LE=F):** Ganado vivo
- **Feeder Cattle (GF=F):** Ganado para engorde
- **Lean Hogs (HE=F):** Cerdos magros

### Madera
- **Lumber (LBS=F):** Madera - Construcción

---

## SLIDE 8: Predictores Macroeconómicos (5)

### Variables Explicativas para Modelado

**1. VIX (^VIX) - Índice de Volatilidad**
- "Termómetro del miedo" del mercado
- Correlación inversa con commodities de refugio (oro)
- Predictor de turbulencia de precios

**2. DXY (DX-Y.NYB) - Dollar Index**
- Índice del dólar estadounidense vs canasta de monedas
- **Correlación fuerte:** Dólar sube → commodities bajan (denominados en USD)
- Correlación negativa con Platinum: **-0.81**

**3. S&P 500 (^GSPC)**
- Índice bursátil estadounidense - Proxy de salud económica global
- Correlación positiva con metales preciosos: Gold (0.85), Silver (0.57)

**4. Treasury 10Y (^TNX) - Tasas de Interés 10 años**
- Costo de oportunidad para inversión en commodities
- Tasas altas → commodities menos atractivos

**5. Energy Index (^GSPE) - Índice Sector Energía**
- Refleja salud del sector energético
- Correlación muy alta con petróleo: Heating Oil (0.82), RBOB (0.78)

---

## SLIDE 9: Procesamiento de Datos - Etapa 1

### Descarga Automática (download_commodities.py)

#### Proceso
1. **Conexión a Yahoo Finance** vía biblioteca `yfinance`
2. **Descarga paralela** de 22 tickers configurados en `config.py`
3. **Estandarización de columnas:** date, open, high, low, close, adj_close, volume
4. **Guardado individual:** Un CSV por commodity en `data/interim/commodities/`

#### Código Simplificado
```python
for name, ticker in COMMODITIES_TICKERS.items():
    df = yf.download(ticker, start='2000-01-01')
    df.to_csv(f'data/interim/commodities/{name.lower()}.csv')
```

#### Manejo de Errores
- **Timeout:** Reintentos automáticos
- **Ticker inexistente:** Log de error, continúa con siguiente
- **Datos incompletos:** Marca para revisión manual

---

## SLIDE 10: Procesamiento de Datos - Etapa 2

### Consolidación (process.py - Parte 1)

#### 1. Carga de Archivos Individuales
```python
commodity_files = Path('data/interim/commodities/').glob('*.csv')
dfs = [pd.read_csv(f, parse_dates=['date']) for f in commodity_files]
df_commodities = pd.concat(dfs, ignore_index=True)
```

#### 2. Formato Largo → Formato Ancho
**Formato Largo (inicial):**
```
date       | commodity  | close
2000-01-03 | Corn       | 234.5
2000-01-03 | Wheat      | 287.2
```

**Formato Ancho (final):**
```
date       | Corn  | Wheat | Soybeans | ...
2000-01-03 | 234.5 | 287.2 | 542.0    | ...
```

**Ventaja:** Cada commodity es una columna → Facilita cálculos de correlaciones y ML

---

## SLIDE 11: Procesamiento de Datos - Etapa 3

### Limpieza de Datos

#### Problemas Identificados y Soluciones

**1. Valores Faltantes (Missing Values)**
- **Origen:** Fines de semana, feriados, gaps en datos
- **Tratamiento:** 
  - Precios: Forward-fill + Backward-fill (máximo 5 días)
  - Volumen: Rellenar con 0 (asume no hubo trading)

**2. Valores Negativos/Inválidos**
- **Detección:** Precios ≤ 0 detectados como outliers
- **Acción:** Convertir a NaN, NO imputar (preserva integridad)

**3. Duplicados**
- **Causa:** Empalme de fuentes, ajustes corporativos
- **Solución:** `.drop_duplicates(subset='date', keep='last')`

#### Estadística Final de Missing Values
- **Brent_Crude:** 30.55% (inicio de trading en 2006)
- **Granos principales:** < 3.5%
- **Predictores:** < 1%

---

## SLIDE 12: Feature Engineering - Variables Temporales

### Features Calculadas (216 en total)

#### 1. Variables Temporales (6 features)
Añaden contexto de estacionalidad y ciclos:
```python
df['year'] = df['date'].dt.year
df['month'] = df['date'].dt.month          # 1-12
df['quarter'] = df['date'].dt.quarter      # 1-4
df['day_of_week'] = df['date'].dt.dayofweek  # 0=lunes
df['day_of_year'] = df['date'].dt.dayofyear  # 1-365
df['week_of_year'] = df['date'].dt.isocalendar().week
```

**Utilidad:** Capturar patrones estacionales (ej: cosechas en granos)

---

## SLIDE 13: Feature Engineering - Lags

#### 2. Lags (54 features: 27 variables × 2 períodos)
**Precios retrasados para capturar momentum e inercia**

```python
# Lag 1 día (precio de ayer)
df['Corn_lag1'] = df['Corn'].shift(1)

# Lag 7 días (precio de hace una semana)
df['Corn_lag7'] = df['Corn'].shift(7)
```

**Ejemplo práctico:**
```
date       | Corn  | Corn_lag1 | Corn_lag7
2025-10-27 | 420.5 | 418.2     | 412.0
```

**Interpretación:**
- Si `Corn` > `Corn_lag1` → Tendencia alcista de corto plazo
- Si `Corn` > `Corn_lag7` → Tendencia alcista semanal

**Uso en ML:** Features lagged permiten predecir precio futuro sin "leak" de información

---

## SLIDE 14: Feature Engineering - Rolling Statistics

#### 3. Medias Móviles (108 features: 27 × 2 ventanas × 2 métricas)

**Media Móvil Simple (SMA)**
```python
# Ventana 7 días
df['Corn_ma7'] = df['Corn'].rolling(window=7).mean()

# Ventana 30 días
df['Corn_ma30'] = df['Corn'].rolling(window=30).mean()
```

**Desviación Estándar Rolling**
```python
# Volatilidad 7 días
df['Corn_std7'] = df['Corn'].rolling(window=7).std()

# Volatilidad 30 días
df['Corn_std30'] = df['Corn'].rolling(window=30).std()
```

**Señales de Trading:**
- **Golden Cross:** Precio cruza por encima de MA30 → Señal alcista
- **Death Cross:** Precio cruza por debajo de MA30 → Señal bajista
- **Bollinger Bands:** Precio ± 2×std → Bandas de sobrecompra/sobreventa

---

## SLIDE 15: Feature Engineering - Retornos

#### 4. Retornos Porcentuales (54 features: 27 × 2 períodos)

**Retornos diarios y semanales**
```python
# Retorno 1 día (diario)
df['Corn_return1'] = df['Corn'].pct_change(periods=1) * 100

# Retorno 7 días (semanal)
df['Corn_return7'] = df['Corn'].pct_change(periods=7) * 100
```

**Ejemplo:**
```
date       | Corn  | Corn_return1 | Corn_return7
2025-10-27 | 420.5 | +0.55%       | +2.04%
```

**Ventajas de Retornos vs Precios:**
1. **Estacionariedad:** Retornos eliminan tendencias, facilitan modelado estadístico
2. **Normalización:** Comparables entre commodities de diferentes escalas
3. **Interpretabilidad:** Directamente expresan ganancia/pérdida

**Distribución:** Retornos aproximan distribución normal (útil para VaR, opciones)

---

## SLIDE 16: Dataset Final - Características

### Archivo: `commodities_base_daily.csv`

#### Dimensiones
- **Filas:** 6,537 (días de trading desde 2000-01-03)
- **Columnas:** 250 features totales
  - 1 fecha (`date`)
  - 27 precios de cierre (22 commodities + 5 predictores)
  - 6 temporales (year, month, quarter, etc.)
  - 54 lags (1 y 7 días × 27 variables)
  - 108 rolling (media y std, ventanas 7 y 30 × 27 variables)
  - 54 retornos (1 y 7 días × 27 variables)

#### Tamaño del Archivo
- **25 MB** en formato CSV
- **~10 MB** comprimido con gzip

#### Metadatos Complementarios
- `metadata.json`: Información técnica del dataset
- `predictors_registry.json`: Registro de predictores descargados
- `correlation_matrix.csv`: Matriz de correlaciones 27×27

---

## SLIDE 17: Análisis Exploratorio - Correlaciones Fuertes

### Correlaciones Más Altas Detectadas (>0.90)

#### Intra-Commodity (Misma Familia)
1. **Petróleo Brent vs WTI:** 0.97 → Commodities casi idénticos (misma naturaleza)
2. **Ganado Feeder vs Live Cattle:** 0.98 → Cadena productiva conectada
3. **Heating Oil vs RBOB Gasoline:** 0.96 → Derivados del petróleo

#### Inter-Commodity (Cross-Asset)
4. **Corn vs Soybeans:** 0.92 → Rotación de cultivos, competencia por tierra
5. **Gold vs Silver:** 0.88 → Metales preciosos con alta correlación histórica
6. **Corn vs Wheat:** 0.88 → Granos substitutos parciales

#### Commodity-Macro
7. **Gold vs S&P 500:** 0.85 → Ambos activos de riesgo en expansión
8. **Platinum vs DXY:** -0.81 → Correlación NEGATIVA fuerte (dólar fuerte → metales débiles)

**Implicancia para Modelado:** Multicolinealidad alta → Usar PCA o selección de features

---

## SLIDE 18: Análisis Exploratorio - Patrones Temporales

### Eventos Críticos Identificados en las Series

#### 1. Crisis Financiera 2008
- **Oro:** Subida de $600 → $1,900 (2008-2011) - Refugio de valor
- **Petróleo:** Caída de $147 → $30 en 6 meses - Colapso de demanda

#### 2. Pandemia COVID-19 (Marzo 2020)
- **Petróleo WTI:** Precio NEGATIVO (-$37) el 20 de abril 2020 (histórico)
- **VIX:** Pico de 82.69 (terror máximo)
- **Oro:** Rally hasta $2,067 (agosto 2020)

#### 3. Guerra Ucrania (Febrero 2022)
- **Wheat:** +50% en 2 semanas (Rusia y Ucrania = 30% exportaciones globales)
- **Natural Gas:** +300% en Europa
- **Fertilizantes:** Escasez crítica (Rusia es exportador clave)

### Visualizaciones Generadas
- `evolucion_precios_principales.png`: Series temporales 2000-2025 con marcadores de eventos
- `volatilidad_historica.png`: Spikes de volatilidad en crisis

---

## SLIDE 19: Calidad de Datos - Validaciones

### Métricas de Calidad Implementadas

#### 1. Cobertura Temporal
- **Sin gaps críticos:** Máximo 5 días consecutivos sin datos
- **Consistencia:** Todos los commodities cubren al menos 2000-2025

#### 2. Validación de Precios
- ✅ Todos los precios > 0 (outliers marcados, NO eliminados)
- ✅ High ≥ Low en el 99.9% de los casos
- ✅ Close dentro del rango [Low, High] en 99.8%

#### 3. Duplicados
- ✅ Cero duplicados en fecha (tras limpieza)

#### 4. Missing Values
- **Estratégicos:** NaNs en primeras filas de lags (esperado por diseño)
- **No estratégicos:** < 5% en commodities principales
- **Documentados:** Archivo `metadata.json` detalla % missing por columna

#### 5. Tipos de Datos
- ✅ Fecha: `datetime64[ns]`
- ✅ Precios: `float64`
- ✅ Temporales: `int32`

---

## SLIDE 20: Ventajas de Este Approach

### Escalabilidad
1. **Agregar commodity:** Editar `config.py`, agregar ticker, ejecutar pipeline (< 5 min)
2. **Cambiar features:** Modificar parámetros en `process.py` (lags, ventanas, etc.)
3. **Nuevos predictores:** Mismo flujo que commodities

### Reproducibilidad
- **Pipeline automatizado:** 3 comandos → dataset completo
- **Sin dependencias externas:** Solo Yahoo Finance (gratuito, sin API key)
- **Versionado:** Código en Git, datos regenerables

### Colaboración
- **Código centralizado:** Cambios en `src/` benefician a todos
- **Documentación:** README, data dictionary, sources.md
- **Notebooks limpios:** Solo análisis, sin código de descarga duplicado

### Profesionalismo
- **Estructura estándar:** Cookiecutter Data Science (usado en industria)
- **Logging:** Trazabilidad de errores y warnings
- **Metadatos:** JSON con info completa del dataset generado

---

## SLIDE 21: Limitaciones y Próximos Pasos

### Limitaciones Actuales

#### 1. Fuente Única
- **Dependencia de Yahoo Finance:** Si falla la fuente, pipeline se detiene
- **Solución futura:** Implementar fuentes alternativas (Alpha Vantage, Quandl)

#### 2. Datos Diarios Únicamente
- **No hay intraday:** Para HFT (High-Frequency Trading) se necesitaría minutely data
- **No hay futuros de diferentes vencimientos:** Solo continuous contract (roll más cercano)

#### 3. Missing Values No Imputados Agresivamente
- **Decisión de diseño:** Preferimos NaN antes que imputar valores inventados
- **Trade-off:** Algunos modelos requieren datos completos (usar KNN imputation si necesario)

#### 4. Sin Datos Fundamentales
- **Solo técnicos:** Precios y derivados (lags, MAs, retornos)
- **Falta contexto:** Inventarios, cosecha, producción, clima

---

## SLIDE 22: Próximos Pasos - Fase 2 del Proyecto

### Modelado Predictivo (Siguiente Entrega)

#### 1. Feature Selection
- **PCA:** Reducir 250 features → 50-100 componentes principales
- **Recursive Feature Elimination:** Identificar features más relevantes
- **Correlación threshold:** Eliminar features con r > 0.95

#### 2. Modelos a Implementar
- **Baseline:** Regresión lineal, ARIMA
- **Machine Learning:** Random Forest, XGBoost, LightGBM
- **Deep Learning:** LSTM (Long Short-Term Memory) para series temporales
- **Ensemble:** Combinar predicciones de múltiples modelos

#### 3. Target Variable
- **Precio futuro:** Predecir `Corn_t+1` (1 día adelante)
- **Dirección:** Clasificación binaria (sube/baja)
- **Volatilidad:** Predecir `Corn_std30` (útil para trading options)

#### 4. Evaluación
- **Métricas:** RMSE, MAE, R² para regresión | Accuracy, F1 para clasificación
- **Backtesting:** Simular estrategia de trading con predicciones históricas
- **Sharpe Ratio:** Evaluar performance ajustada por riesgo

---

## SLIDE 23: Aplicaciones Prácticas

### Casos de Uso del Dataset

#### 1. Trading Cuantitativo
- **Señales de entrada/salida:** Basadas en cruces de medias móviles
- **Pairs Trading:** Explotar correlaciones (ej: Corn-Wheat spread)
- **Mean Reversion:** Detectar desviaciones excesivas de MA y apostar a retorno

#### 2. Gestión de Riesgo
- **VaR (Value at Risk):** Calcular pérdida máxima esperada con distribución de retornos
- **Correlación dinámica:** Ajustar portfolio según cambios en correlaciones
- **Stress Testing:** Simular impacto de eventos extremos (guerra, pandemia)

#### 3. Análisis Macroeconómico
- **Inflación:** Commodities como proxy de presiones inflacionarias
- **Ciclo económico:** Copper (Doctor Copper) como indicador adelantado
- **Política monetaria:** Tasas altas → presión bajista en commodities

#### 4. Agricultura y Agronegocios
- **Cobertura (hedging):** Productores pueden usar predicciones para contratos forward
- **Decisiones de siembra:** Correlación Corn-Soybean informa rotación óptima

---

## SLIDE 24: Lecciones Aprendidas

### Desafíos Técnicos Superados

#### 1. Manejo de MultiIndex en Pandas
- **Problema:** `yfinance` devuelve MultiIndex cuando descarga múltiples tickers
- **Solución:** `.droplevel(1)` para aplanar columnas

#### 2. Memoria con 250 Columnas
- **Problema:** DataFrame de 6,537 × 250 consume ~150 MB en RAM
- **Solución:** Usar `dtype` eficientes (`int32` en vez de `int64`), procesar por chunks si escala

#### 3. Reproducibilidad de Descarga
- **Problema:** Yahoo Finance cambia formato de respuesta sin aviso
- **Solución:** Manejo robusto de errores, logging detallado, tests de integración

#### 4. Estacionalidad en Missing Values
- **Insight:** Lumber tiene 12.45% missing porque CME cambió contrato en 2011
- **Acción:** Documentar en `data_dictionary.md`, no es error de descarga

---

## SLIDE 25: Conclusiones

### Lo Que Construimos
1. **Base de datos profesional:** 25 años, 27 variables, 250 features, 25 MB
2. **Pipeline automatizado:** Regenerable en < 5 minutos desde cero
3. **Estructura modular:** Código reutilizable, escalable, colaborativo
4. **Documentación completa:** README, data dictionary, sources, metadata JSON

### Valor Agregado
- **Sin esta base:** Cada miembro del equipo descargaría datos manualmente → inconsistencias
- **Con esta base:** Una sola fuente de verdad, versionada, validada

### Estado Actual
✅ **Fase 1 completada:** Descarga, procesamiento, feature engineering, exploración  
⏳ **Fase 2 en desarrollo:** Modelado predictivo, backtesting, deployment

### Diferenciadores
- **No es un notebook:** Es un **proyecto de software** con arquitectura profesional
- **No son scripts sueltos:** Es un **pipeline orquestado** con flujo lógico
- **No es solo código:** Incluye **documentación técnica exhaustiva**

---

## SLIDE 26: Demo en Vivo (Opcional)

### Si Hay Tiempo: Ejecutar Pipeline

#### Comando 1: Descargar Commodities
```bash
python src/data/download_commodities.py
```
**Output esperado:** 22 archivos CSV en `data/interim/commodities/`

#### Comando 2: Descargar Predictores
```bash
python src/data/download_predictors.py
```
**Output esperado:** 5 archivos CSV + `predictors_registry.json`

#### Comando 3: Procesar y Generar Features
```bash
python src/data/process.py
```
**Output esperado:** 
- `commodities_base_daily.csv` (25 MB)
- `metadata.json`
- Log con métricas de calidad

#### Mostrar Dataset Final
```python
import pandas as pd
df = pd.read_csv('data/processed/commodities_base_daily.csv')
print(df.shape)  # (6537, 250)
print(df.head())
```

---

## SLIDE 27: Recursos y Referencias

### Repositorio del Proyecto
**GitHub:** https://github.com/paulaleylen/BigDataUBA-GrupoJLP  
**Carpeta:** `TPFinal/`

### Documentación Técnica
- `README.md` - Setup y guía de uso
- `references/data_dictionary.md` - Diccionario de variables (19 páginas)
- `references/sources.md` - Fuentes de datos y justificaciones
- `data/processed/metadata.json` - Metadatos del dataset

### Notebooks de Exploración
- `1.0-initial-exploration.ipynb` - EDA básico
- `2.0-correlation-analysis.ipynb` - Matrices de correlación y heatmaps

### Librerías Utilizadas
- `pandas` 2.0+ - Manipulación de datos
- `yfinance` 0.2.40 - Descarga desde Yahoo Finance
- `numpy` 1.24+ - Operaciones numéricas
- `matplotlib` + `seaborn` - Visualizaciones

---

## SLIDE 28: Agradecimientos y Cierre

### Agradecimientos
- **Profesor/a de Taller de Programación:** [Nombre] - Por la guía y feedback
- **Comunidad Open Source:** Mantenedores de `yfinance`, `pandas`, `cookiecutter-data-science`
- **Equipo:** Colaboración efectiva en arquitectura y desarrollo

### Contacto
**Grupo JLP**  
- Paula Leylén Ramirez - [@paulaleylen]
- Juan Ignacio Pintos - [@juanpintoselso33]
- Luis Mella

**Universidad:** UBA - Facultad de Ciencias Económicas  
**Materia:** Taller de Programación  
**Fecha:** Noviembre 2025

### Preguntas
**¿Preguntas o comentarios?**

---

## SLIDE 29: BACKUP - Detalles Técnicos Avanzados

### (Solo si preguntan en Q&A)

#### Configuración de Paths
```python
# src/config.py
BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / 'data'
INTERIM_DIR = DATA_DIR / 'interim'
PROCESSED_DIR = DATA_DIR / 'processed'
```
**Beneficio:** Paths relativos funcionen en cualquier SO (Windows, Mac, Linux)

#### Manejo de Errores en Descarga
```python
try:
    df = yf.download(ticker, start=START_DATE)
except Exception as e:
    logger.error(f"Error descargando {ticker}: {e}")
    return None
```

#### Feature Engineering Eficiente
```python
# Vectorizado con Pandas (rápido)
df['Corn_return1'] = df['Corn'].pct_change() * 100

# ❌ Loop (lento, NO hacer)
for i in range(1, len(df)):
    df.loc[i, 'return'] = (df.loc[i, 'Corn'] / df.loc[i-1, 'Corn'] - 1) * 100
```

---

## SLIDE 30: BACKUP - Preguntas Frecuentes

### ¿Por qué no usar Kaggle para datos históricos?
- **Actualización:** Datasets de Kaggle quedan desactualizados
- **Consistencia:** Yahoo Finance es nuestra única fuente → formato uniforme
- **Automatización:** Kaggle API requiere autenticación y permisos

### ¿Por qué formato ancho y no largo?
- **ML-friendly:** Scikit-learn, XGBoost esperan formato ancho (filas=obs, cols=features)
- **Correlaciones:** `.corr()` funciona directamente en formato ancho

### ¿Por qué no usar bases de datos SQL?
- **Volumen:** 6,537 × 250 = 1.6 millones de celdas → CSV es suficiente
- **Portabilidad:** CSV se abre en cualquier herramienta (Excel, R, Python, Julia)
- **Versionado:** Git maneja bien CSVs de < 50 MB

### ¿Cómo manejan cambios en contratos de futuros?
- **Yahoo Finance entrega continuous contracts:** Auto-roll al vencimiento más cercano
- **Limitación:** No capturamos term structure (curva de futuros)

---

## NOTAS PARA LOS PRESENTADORES

### Timing Sugerido (Presentación 15-20 minutos)
- **Slides 1-4:** Contexto y arquitectura (3 min)
- **Slides 5-8:** Fuentes de datos y commodities (3 min)
- **Slides 9-15:** Pipeline y feature engineering (5 min) ← **CORAZÓN**
- **Slides 16-18:** Dataset final y análisis (3 min)
- **Slides 19-25:** Calidad, conclusiones, próximos pasos (4 min)
- **Slides 26-28:** Demo (opcional) + cierre (2 min)
- **Slides 29-30:** BACKUP (solo si preguntan)

### Énfasis Clave
1. **Automatización:** Repetir que todo es reproducible en < 5 minutos
2. **Escalabilidad:** Mostrar cómo agregar un commodity editando solo `config.py`
3. **Profesionalismo:** Estructura modular > scripts sueltos
4. **Feature engineering:** 216 features calculadas automáticamente

### Visuales Recomendados
- **Slide 3:** Diagrama de árbol de la estructura `TPFinal/`
- **Slide 4:** Flowchart del pipeline (descarga → proceso → explore)
- **Slide 17:** Heatmap de correlaciones (usar `correlation_matrix.csv`)
- **Slide 18:** Gráfico de series temporales con marcadores de eventos
- **Slide 19:** Dashboard de métricas de calidad (barras de % missing)

### Tips de Presentación
- **NO leer slides:** Explicar con tus palabras
- **Contar historia:** "Imaginen que necesitan predecir maíz mañana..."
- **Anticipar preguntas:**
  - ¿Por qué Yahoo Finance? → Gratis, histórico completo, estándar industria
  - ¿Cómo agregamos más commodities? → Editar config.py, ejecutar 1 comando
  - ¿Qué pasa si Yahoo falla? → Logger registra error, continúa con resto

### Respuestas a Preguntas Difíciles
**"¿Por qué 250 features? ¿No es overkill?"**
→ Es para dar opciones al modelo. En Fase 2 haremos feature selection y reduciremos a 50-100 con PCA.

**"¿Validaron contra otra fuente?"**
→ Yahoo Finance es el estándar. En spot checks comparamos Corn con datos de CBOT y coinciden.

**"¿Cómo manejan outliers?"**
→ Los marcamos como NaN pero NO los eliminamos. El modelo debe aprender que existen (ej: petróleo negativo en 2020).

**"¿Esto es mejor que comprar un dataset?"**
→ Datasets comerciales cuestan miles de USD/año. Nuestra solución es gratuita, actualizable y customizable.
