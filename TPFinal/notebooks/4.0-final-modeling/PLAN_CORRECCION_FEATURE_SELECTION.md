# Plan de Corrección - Feature Selection Pipeline

**Fecha:** 2025-12-07  
**Notebook afectado:** `4.1-feature-selection-optimized.ipynb`  
**Dataset fuente:** `features_final_modeling.csv` (3,247 features incluyendo 10 de GDELT sentiment)

---

## Resumen de Problemas Detectados

### 🔴 Críticos

| # | Problema | Impacto | Evidencia |
|---|----------|---------|-----------|
| 1 | **Sentiment GDELT no seleccionado** | Features validadas por literatura (tone_mean, tone_momentum) eliminadas en feature selection | 0 features de sentiment en `selected_features.json` |
| 2 | **AUC sospechosamente alto en t1** | 0.89 AUC para predicción diaria es anómalo | Literatura indica AUC >0.70 es excepcional para commodities |
| 3 | **~50 features `is_outlier` por combinación** | Posible overfitting o leakage | Features capturan eventos extremos que pueden tener lookahead |

### 🟡 Cuestionables

| # | Problema | Impacto | Acción requerida |
|---|----------|---------|------------------|
| 4 | Precious metals volume en grains | No hay base teórica sólida | Revisar si es spurious correlation |
| 5 | Diferencia drástica entre horizontes | t1 usa fundamentals, t5/t21 usa técnicos | Verificar que no hay leakage temporal |

---

## Plan de Acción Detallado

### FASE 1: Diagnóstico de Sentiment (Prioridad Alta)

**Objetivo:** Entender por qué las 10 features de GDELT no pasaron el feature selection.

#### 1.1 Verificar presencia en dataset de entrada
```python
# Verificar que tone_* están en el input de 4.1
df = pd.read_csv('features_final_modeling.csv')
sentiment_cols = [c for c in df.columns if 'tone_' in c or 'article_' in c]
print(f"Sentiment features en input: {len(sentiment_cols)}")
```

#### 1.2 Analizar en qué etapa se eliminaron
- [ ] ¿Variance Threshold las eliminó? (varianza muy baja)
- [ ] ¿Correlation Filter las eliminó? (alta correlación entre ellas)
- [ ] ¿Mutual Information las descartó? (bajo MI con target)
- [ ] ¿LASSO las penalizó a cero?

#### 1.3 Forzar inclusión de sentiment si MI > 0
**Hipótesis:** Las features de sentiment tienen información pero el pipeline las descarta.

**Acción:** Agregar whitelist de features que SIEMPRE pasan:
```python
MANDATORY_FEATURES = [
    'tone_mean', 'tone_momentum_7d', 'tone_volatility_7d',
    'article_count', 'article_count_change'
]
```

---

### FASE 2: Auditar Data Leakage en t1 (Prioridad Crítica)

**Objetivo:** Investigar por qué t1 tiene AUC=0.89 cuando debería ser ~0.55-0.65.

#### 2.1 Verificar lag de COT data
```python
# COT se publica viernes después del cierre
# Si usamos COT(t) para predecir direction(t+1), es válido
# Si usamos COT(t) para predecir direction(t), es LEAKAGE

# Verificar:
cot_features = ['managed_long', 'managed_short', 'producer_long', ...]
for feat in cot_features:
    print(f"{feat}: lag presente? {'_lag' in feat}")
```

#### 2.2 Verificar construcción de target
```python
# El target direction_t1 debe ser:
# direction_t1[i] = sign(close[i+1] - close[i])
# NO debe ser:
# direction_t1[i] = sign(close[i] - close[i-1])  # LEAKAGE
```

#### 2.3 Verificar split temporal
```python
# El split debe ser estricto: train < test temporalmente
# NO debe haber shuffle que mezcle fechas
assert X_train.index.max() < X_test.index.min()
```

---

### FASE 3: Reducir Features `is_outlier` (Prioridad Media)

**Problema:** ~50 features `is_outlier` por combinación pueden agregar ruido.

#### 3.1 Analizar correlación entre is_outlier features
```python
outlier_cols = [c for c in selected_features if 'is_outlier' in c]
corr_matrix = df[outlier_cols].corr()
# Si muchas tienen corr > 0.7, son redundantes
```

#### 3.2 Limitar a top 10 is_outlier por MI
```python
# En lugar de incluir todas, limitar:
MAX_OUTLIER_FEATURES = 10
outlier_features = [f for f in mi_top_150 if 'is_outlier' in f][:MAX_OUTLIER_FEATURES]
```

#### 3.3 Considerar eliminar completamente
**Alternativa:** Usar solo las features de volatilidad continuas (Bollinger Bands, vol_ratio) que capturan la misma información sin discretizar.

---

### FASE 4: Validar Precious Metals Volume (Prioridad Baja)

**Problema:** `Platinum_volume_is_outlier90` predice Corn - relación no establecida en literatura.

#### 4.1 Calcular correlación directa
```python
corr = df['Platinum_volume'].corr(df['Corn'])
print(f"Correlación Platinum_volume vs Corn: {corr:.3f}")
# Si |corr| < 0.1, es probablemente spurious
```

#### 4.2 Test de causalidad de Granger
```python
from statsmodels.tsa.stattools import grangercausalitytests
# Verificar si Platinum_volume Granger-causa Corn
grangercausalitytests(df[['Corn', 'Platinum_volume']].dropna(), maxlag=5)
```

#### 4.3 Decisión
- Si no hay relación causal → Agregar a blacklist
- Si hay relación → Documentar como finding inesperado

---

### FASE 5: Implementar Cambios en 4.1

#### 5.1 Modificaciones al pipeline

```python
# NUEVO: Whitelists y Blacklists
WHITELIST_FEATURES = [
    # Sentiment (validado por literatura)
    'tone_mean', 'tone_std', 'tone_ma7', 'tone_ma30',
    'tone_volatility_7d', 'tone_volatility_30d', 
    'tone_percentile_30d', 'tone_momentum_7d',
    'article_count', 'article_count_change',
    
    # Fundamentals (Stock-to-Use)
    'psd_world_Stock_to_Use_Ratio_simple_return90',
    'psd_united_states_Stock_to_Use_Ratio_simple_return90',
]

BLACKLIST_PATTERNS = [
    # Precious metals volume en grains (spurious)
    r'(Gold|Silver|Platinum|Palladium)_volume.*corn',
    r'(Gold|Silver|Platinum|Palladium)_volume.*soy',
    r'(Gold|Silver|Platinum|Palladium)_volume.*wheat',
]

# Limitar is_outlier
MAX_OUTLIER_FEATURES = 10
```

#### 5.2 Nueva estructura de feature selection

```
Stage 1: Variance Threshold (0.01) 
    ↓ Excluir WHITELIST del filtro
Stage 2: Correlation Filter (0.95)
    ↓ Proteger WHITELIST de eliminación
Stage 3: Mutual Information (top 150)
    ↓ Garantizar WHITELIST incluida
    ↓ Limitar is_outlier a MAX_OUTLIER
Stage 4: LASSO Selection
    ↓ Aplicar BLACKLIST
Stage 5: Validación cruzada de features finales
```

---

## Cronograma de Ejecución

| Fase | Tarea | Tiempo Est. | Dependencia |
|------|-------|-------------|-------------|
| 1.1 | Verificar sentiment en input | 5 min | - |
| 1.2 | Diagnosticar etapa de eliminación | 15 min | 1.1 |
| 2.1 | Auditar lag de COT | 10 min | - |
| 2.2 | Verificar construcción target | 10 min | - |
| 2.3 | Verificar split temporal | 5 min | - |
| 3.1 | Analizar correlación is_outlier | 10 min | - |
| 4.1 | Test Granger para precious metals | 15 min | - |
| 5.1 | Implementar whitelist/blacklist | 30 min | 1-4 |
| 5.2 | Re-ejecutar 4.1 con cambios | 20 min | 5.1 |
| 6 | Re-ejecutar 4.2 y comparar resultados | 30 min | 5.2 |

**Total estimado:** 2.5 horas

---

## Métricas de Éxito

| Métrica | Valor Actual | Valor Esperado |
|---------|--------------|----------------|
| AUC t1 | 0.89 (sospechoso) | 0.55-0.65 |
| AUC t5 | 0.50-0.53 | 0.52-0.58 |
| AUC t21 | 0.55-0.61 | 0.55-0.65 |
| Features sentiment seleccionadas | 0 | ≥5 |
| Features is_outlier | ~50 | ≤10 |

---

## Referencias de Literatura

1. **COT Positions:** Keenan (2020) - "Advanced positioning, flow, and sentiment analysis"
2. **Stock-to-Use:** USDA WASDE - "The most important number for grain prices"
3. **Sentiment:** ScholarAI encontró 10+ papers validando news sentiment en commodities
4. **Spillovers:** MDPI (2024) - "Volatility Spillovers among Major Commodities"
5. **Bollinger Bands:** Insignia Futures - "Versatile tool for commodity futures"

---

## Notas Adicionales

### Por qué el AUC=0.89 es sospechoso

La literatura académica indica que para predicción direccional de commodities:
- **Random baseline:** AUC = 0.50
- **Modelos simples (MA crossover):** AUC = 0.52-0.55
- **Modelos ML bien calibrados:** AUC = 0.55-0.65
- **Modelos con data leakage:** AUC > 0.75

Un AUC de 0.89 sugiere:
1. Data leakage (información del futuro en features)
2. Target construido incorrectamente
3. Overfitting extremo al test set

### Por qué sentiment debería ser significativo

La literatura (ScholarAI, Tavily) confirma que:
- News sentiment afecta precios de commodities en horizontes de 1-5 días
- GDELT tone score correlaciona con volatilidad de mercado
- Article count es proxy de atención mediática (afecta volumen)

Si nuestro pipeline elimina estas features, hay un problema en:
- Varianza muy baja (ffill crea muchos valores repetidos)
- Alta correlación con otras features
- MI calculado incorrectamente

---

**Próximo paso:** Ejecutar Fase 1.1 - Verificar presencia de sentiment en input
