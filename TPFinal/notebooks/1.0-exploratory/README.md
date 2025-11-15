# 1.0-exploratory - Análisis Exploratorio de Datos (EDA)

## Descripción

Esta carpeta contiene los notebooks de **Exploratory Data Analysis (EDA)** del proyecto de predicción de precios de commodities. El EDA es la fase inicial crítica donde se valida la calidad de los datos, se identifican patrones, y se generan hipótesis para feature engineering y modelado.

## Estructura de Notebooks

### Orden de Ejecución Recomendado

```
1.1-initial-exploration.ipynb       → Análisis descriptivo inicial
1.2-correlation-analysis.ipynb      → Correlaciones y cointegración
1.3-time-series-properties.ipynb    → Estacionariedad, ACF/PACF, STL
1.4-outliers-anomalies.ipynb        → Detección de outliers y eventos extremos
1.5-data-quality-report.ipynb       → Reporte consolidado de calidad
```

---

## 1.1 Initial Exploration

**Objetivo:** Validar carga de datos y caracterizar distribuciones básicas.

**Contenido:**
- Carga del dataset consolidado (`commodities_base_consolidated.csv`)
- Análisis de cobertura temporal por variable
- Identificación de valores faltantes (heatmaps por commodity y predictor)
- Estadísticas descriptivas (media, std, CV, cuartiles)
- Visualización de series temporales con media móvil
- Distribuciones de precios con tests de normalidad (skewness, kurtosis)

**Outputs:**
- `exploracion_missing_patterns_heatmap.png`: Heatmap de missing values (top 30 variables)
- `exploracion_missing_commodities.png`: Missing específico para commodities
- `exploracion_missing_predictores.png`: Missing específico para predictores
- `exploracion_series_temporales_commodities.png`: Gráficos de series por sector
- `exploracion_series_temporales_predictores.png`: Series de índices macroeconómicos
- `exploracion_distribuciones_precios.png`: Histogramas con overlay normal

**Hallazgos clave:**
- Dataset consolidado: ~6,981 obs × 99 variables (sin features derivadas)
- Missing values: 3.5%-35% según variable (supply-demand tiene mayor missing estructural)
- Commodities no siguen distribución normal (kurtosis elevada, asimetría positiva)

**Prerrequisito:** Ejecutar `python src/data/process.py`

---

## 1.2 Correlation Analysis

**Objetivo:** Analizar relaciones lineales y no lineales entre variables.

**Contenido:**
- Matriz de correlación de Pearson para todas las variables base
- Identificación de pares con correlación fuerte (|r| > 0.7)
- Correlaciones rolling (ventanas de 90, 180, 365 días) para detectar cambios temporales
- Clustermap con agrupación jerárquica
- Análisis de cointegración entre commodities (Engle-Granger test)
- Correlaciones condicionales por régimen de volatilidad

**Outputs:**
- `correlacion_completa.png`: Heatmap de matriz completa
- `correlacion_clustermap.png`: Clustering jerárquico
- `correlacion_rolling_selected.png`: Evolución temporal de correlaciones clave
- `correlation_matrix.csv`: Matriz exportada para análisis posterior
- `strong_correlations.csv`: Pares con |r| > 0.7

**Hallazgos clave:**
- Correlaciones fuertes dentro de sectores (metales preciosos, energía)
- Correlación negativa entre VIX y commodities industriales
- Correlaciones rolling aumentan durante crisis (contagio)
- Evidencia de cointegración entre Gold-Silver, Crude Oil-Heating Oil

**Prerrequisito:** Notebook 1.1

---

## 1.3 Time Series Properties

**Objetivo:** Caracterizar propiedades estadísticas de series temporales.

**Contenido:**
- Test de estacionariedad (Augmented Dickey-Fuller)
- Análisis de autocorrelación (ACF) y autocorrelación parcial (PACF)
- Descomposición STL (tendencia + estacionalidad + residuos)
- Análisis de volatilidad clustering (test ARCH-LM)
- Rolling statistics (media y std móviles)
- Identificación de cambios estructurales

**Outputs:**
- `ts_properties_acf_pacf.png`: ACF/PACF para commodities seleccionados
- `ts_properties_stl_decomposition.png`: Descomposición de serie representativa
- `ts_properties_rolling_statistics.png`: Media móvil y volatilidad realizada

**Hallazgos clave:**
- Mayoría de commodities NO son estacionarias (p > 0.05 en ADF test)
- Fuerte autocorrelación en lags 1-7 días → lags relevantes para features
- Estacionalidad significativa en agrícolas (ciclos de cosecha)
- Evidencia de efectos ARCH (volatilidad clustering) → modelos GARCH apropiados
- Tendencia explica >70% de varianza en precios

**Implicaciones:**
- Requerir diferenciación (returns) para estacionariedad antes de ARIMA
- Lags de 1, 7, 30 días confirmados como óptimos
- Necesidad de features de volatilidad condicional

**Prerrequisito:** Notebooks 1.1, 1.2

---

## 1.4 Outliers & Anomalies

**Objetivo:** Detectar valores atípicos y eventos extremos.

**Contenido:**
- Detección con Z-score (threshold = 3)
- Detección con IQR (threshold = 1.5*IQR)
- Isolation Forest (detección multivariada)
- Boxplots para visualización de distribución + outliers
- Análisis de outliers en returns diarios (>±10%)
- Mapeo temporal de anomalías a eventos históricos (crisis 2008, COVID-2020, guerra Ucrania)
- Distribuciones de returns con marcado de extremos

**Outputs:**
- `outliers_boxplots.png`: Boxplots de 6 commodities representativos
- `outliers_isolation_forest_timeseries.png`: Anomalías en contexto temporal
- `outliers_returns_distributions.png`: Histogramas de returns con thresholds
- `outliers_temporal_distribution.png`: Distribución de anomalías por año

**Hallazgos clave:**
- 5-10% de observaciones clasificadas como outliers según método
- Isolation Forest detecta anomalías contextuales (valores normales en contexto anómalo)
- Concentración de anomalías en 2008, 2020, 2022 valida eventos históricos
- Energía (Crude Oil, Natural Gas) tiene mayor frecuencia de returns extremos (>±10%)
- Kurtosis elevada (colas pesadas) confirma outliers frecuentes, NO errores

**Recomendaciones:**
- NO eliminar outliers (información valiosa sobre riesgo)
- Considerar winsorization o transformación log para estabilizar
- Crear features dummy para períodos de crisis
- Usar modelos robustos (Huber loss) en lugar de MSE

**Prerrequisito:** Notebooks 1.1, 1.2, 1.3

---

## 1.5 Data Quality Report

**Objetivo:** Consolidar hallazgos de calidad y generar reporte ejecutivo.

**Contenido:**
- Resumen de missing values por fuente de datos
- Análisis de duplicados y valores inconsistentes
- Validación de rangos físicos (precios negativos, fechas inválidas)
- Continuidad temporal (gaps en series)
- Scorecard de calidad por variable (0-100)
- Recomendaciones de tratamiento (imputación, exclusión, corrección)
- Metadata exportado en JSON

**Outputs:**
- `data_quality_report.html`: Reporte interactivo HTML
- `data_quality_scorecard.csv`: Scores de calidad por variable
- `metadata_quality.json`: Metadata con decisiones de tratamiento

**Hallazgos clave:**
- 85% de variables tienen calidad >80/100
- Variables de supply-demand (USDA PSD) tienen missing estructural esperado (reportes trimestrales)
- No se detectaron duplicados en series temporales
- 3 commodities tienen gaps de >10 días que requieren interpolación

**Prerrequisito:** Notebooks 1.1-1.4

---

## Herramientas y Librerías Utilizadas

**Análisis Estadístico:**
- `pandas`, `numpy`: Manipulación de datos
- `scipy.stats`: Tests estadísticos (normalidad, estacionariedad)
- `statsmodels`: ACF/PACF, ADF test, STL decomposition, ARCH-LM

**Visualización:**
- `matplotlib`, `seaborn`: Gráficos estáticos
- `src.visualization.estilo_graficos`: Módulo custom con colores institucionales UBA

**Detección de Anomalías:**
- `sklearn.ensemble.IsolationForest`: Detección multivariada
- `sklearn.neighbors.LocalOutlierFactor`: LOF (no usado finalmente)

**Reportes:**
- `pandas-profiling` o `sweetviz`: Reportes automatizados (notebook 1.5)

---

## Outputs Consolidados

Todos los gráficos se guardan en `reports/figures/` con nombres descriptivos y alta resolución (300 DPI).

**Lista de archivos generados:**
```
exploracion_missing_patterns_heatmap.png
exploracion_missing_commodities.png
exploracion_missing_predictores.png
exploracion_series_temporales_commodities.png
exploracion_series_temporales_predictores.png
exploracion_distribuciones_precios.png
correlacion_completa.png
correlacion_clustermap.png
correlacion_rolling_selected.png
ts_properties_acf_pacf.png
ts_properties_stl_decomposition.png
ts_properties_rolling_statistics.png
outliers_boxplots.png
outliers_isolation_forest_timeseries.png
outliers_returns_distributions.png
outliers_temporal_distribution.png
data_quality_report.html
```

**Archivos CSV:**
```
correlation_matrix.csv
strong_correlations.csv
data_quality_scorecard.csv
```

---

## Tiempo Estimado de Ejecución

| Notebook | Tiempo | Complejidad |
|----------|--------|-------------|
| 1.1 | 5-8 min | Baja |
| 1.2 | 8-12 min | Media |
| 1.3 | 10-15 min | Alta (STL computacionalmente costoso) |
| 1.4 | 6-10 min | Media |
| 1.5 | 3-5 min | Baja |
| **Total** | **~40 min** | - |

**Nota:** Tiempos asumen dataset de ~7,000 observaciones con 99 variables.

---

## Próximos Pasos

**Después de completar EDA (notebooks 1.1-1.5), proceder con:**

### 2.0-feature-engineering/

1. **2.1-temporal-lag-features.ipynb**: Crear features temporales y lags [1,7,30]
2. **2.2-rolling-statistics-features.ipynb**: MA y STD en ventanas [7,30,90]
3. **2.3-return-features-volatility.ipynb**: Returns y volatilidad realizada
4. **2.4-climate-features.ipynb**: Integración de features climáticas avanzadas

### 3.0-modeling/

1. **3.1-baseline-models.ipynb**: Modelos simples (Naive, MA, Linear Regression)
2. **3.2-arima-sarima.ipynb**: Modelos ARIMA/SARIMAX
3. **3.3-machine-learning.ipynb**: Random Forest, XGBoost, LightGBM
4. **3.4-deep-learning.ipynb**: LSTM, GRU, Transformers (opcional)
5. **3.5-model-evaluation.ipynb**: Comparación con métricas (RMSE, MAE, MAPE, Diebold-Mariano)

---

## Referencias

**Best Practices EDA:**
- [A Data Scientist's Essential Guide to EDA](https://medium.com/data-science/a-data-scientists-essential-guide-to-exploratory-data-analysis-25637eee0cf6)
- [Advanced EDA - Michael Notter](https://miykael.github.io/blog/2022/advanced_eda/)
- [Time Series EDA Guide](https://towardsdatascience.com/time-series-forecasting-a-practical-guide-to-exploratory-data-analysis-a101dc5f85b1)

**Time Series Analysis:**
- Hyndman & Athanasopoulos - "Forecasting: Principles and Practice" (3rd ed)
- Hamilton - "Time Series Analysis"

**Anomaly Detection:**
- Liu, Ting & Zhou - "Isolation Forest" (2008)
- Chandola, Banerjee & Kumar - "Anomaly Detection: A Survey" (2009)

---

## Contacto y Contribuciones

**Proyecto:** BigDataUBA-GrupoJLP  
**Curso:** Taller de Programación - UBA FCE  
**Equipo:** Grupo JLP

Para reportar issues o sugerir mejoras, usar el repositorio de GitHub.
