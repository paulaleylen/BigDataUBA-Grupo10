# BigDataUBA-Grupo10

**Taller de Programación - Big Data**  
**Universidad de Buenos Aires - Facultad de Ciencias Económicas**  
**Año 2025**

---

## 👥 Integrantes del Equipo

| Nombre | Formación | GitHub |
|--------|-----------|--------|
| Paula Leylén Ramirez| Licenciada en Economía - UNL | [@paulaleylen](https://github.com/paulaleylen) |
| Juan Ignacio Pintos | Licenciado en Ciencia Política - UDELAR | [@juanpintoselso33](https://github.com/juanpintoselso33) |
| Luis Mella| M.A Estadística aplicada - Universidad de Nebrija |

---

## 📚 Trabajos Prácticos

### ✅ TP1: Análisis EPH - Pobreza en Gran Buenos Aires (2005-2025)

**Estado:** Completado ✅  
**Fecha entrega:** 8 de octubre de 2025

**Descripción:**  
Análisis comparativo de pobreza usando la Encuesta Permanente de Hogares (EPH-INDEC). Implementa metodología oficial INDEC (método del ingreso) para identificación de pobres mediante cálculo de adulto equivalente y línea de pobreza.

**Datos:**
- **Períodos:** 1er Trimestre 2005 vs 1er Trimestre 2025
- **Región:** Gran Buenos Aires (GBA)
- **Observaciones:** 16,665 individuos (9,484 en 2005 + 7,181 en 2025)
- **Variables analizadas:** 16 (demográficas, educativas, laborales, ingresos)

**Resultados principales:**
- Pobreza: 26.88% (2005) → 58.86% (2025) | +31.98 puntos porcentuales
- Crisis de calidad de datos: 40% no respuesta en ITF (2025)
- Colapso de educación como protección contra pobreza
- Inversión composición demográfica por sexo

**Tecnologías:** Python, Pandas, Matplotlib, Seaborn, LaTeX  
**Entregables:** Notebook, Informe PDF (10 páginas), Módulo de gráficos UBA-FCE

📂 **Ver detalles:** [TP1/README.md](./TP1/README.md)

---

### ✅ TP2: Histogramas, Kernels & Métodos No Supervisados

**Estado:** Completado ✅  
**Fecha entrega:** 24 de octubre de 2025

**Descripción:**  
Análisis exploratorio con técnicas de visualización (histogramas y kernels) y aplicación de métodos no supervisados (PCA y clustering) sobre datos de la EPH.

**Métodos aplicados:**
- **Parte I:** Creación de variables, histogramas y distribuciones kernel
- **Parte II:** Matriz de correlaciones, PCA, K-means, clustering jerárquico

**Tecnologías:** Python, Pandas, Scikit-learn, Matplotlib, Seaborn, SciPy  
**Entregables:** Notebook, Informe PDF, Módulo de gráficos UBA-FCE

📂 **Ver detalles:** [TP2/README.md](./TP2/README.md)

---

### ✅ TP3: Modelos de Clasificación para Predicción de Pobreza

**Estado:** Completado ✅  
**Fecha entrega:** Noviembre de 2025

**Descripción:**  
Clasificación binaria para predecir pobreza usando datos EPH 2025. Implementación de Regresión Logística y K-Nearest Neighbors (KNN) con enfoque en políticas sociales donde el costo de los errores es asimétrico.

**Modelos implementados:**
- **Regresión Logística:** StandardScaler, class_weight='balanced', análisis de Odds Ratios
- **KNN:** SMOTE con ratio conservador (0.7), optimización de K mediante 5-Fold CV

**Poblaciones analizadas:**
- **Respondieron (7,236 obs):** Datos completos con IPCF para train/test
- **No respondieron (45,425 obs):** Sin IPCF, usados para predicciones finales

**Resultados principales:**
- Recall Logit: 69.3% vs KNN: 23% → **Logit recomendado** para políticas sociales
- Análisis de sesgo de selección en no respondientes
- Énfasis en minimizar Falsos Negativos (pobres no detectados)

**Tecnologías:** Python, Scikit-learn, imbalanced-learn (SMOTE), Matplotlib, LaTeX  
**Entregables:** Notebook, Informe PDF, Gráficos de fronteras de decisión y curvas ROC

📂 **Ver notebook:** [TP3/Program_TP3_Grupo10.ipynb](./TP3/Program_TP3_Grupo10.ipynb)

---

### ✅ TP4: Métodos de Regularización y CART

**Estado:** Completado ✅  
**Fecha entrega:** Noviembre de 2025

**Descripción:**  
Extensión del TP3 con técnicas de regularización (LASSO y Ridge) y árboles de decisión (CART). Comparación sistemática de todos los modelos de clasificación para predicción de pobreza.

**Modelos implementados:**
- **LASSO (L1):** Selección automática de variables, λ óptimo = 0.1
- **Ridge (L2):** Shrinkage de coeficientes, λ óptimo = 10
- **CART:** Árboles de decisión con poda por costo-complejidad (ccp_alpha)

**Resultados principales:**
- CART lidera en Accuracy (71.8%), pero Logit mantiene mejor Recall (69.3%)
- LASSO elimina variables no significativas, Ridge encoge pero no elimina
- Árbol podado con ccp_alpha=0.0026 evita sobreajuste (gap train-test < 5%)
- Comparación de importancia de variables: EDAD, ESTADO, NIVEL_ED como principales predictores

**Visualizaciones:**
- Trayectorias de coeficientes LASSO/Ridge vs λ
- Visualización del árbol de decisión podado
- Importancia de variables por Gini
- Curvas ROC comparativas (todos los modelos)
- Matrices de confusión horizontales

**Tecnologías:** Python, Scikit-learn, Graphviz, Matplotlib, LaTeX  
**Entregables:** Notebook, Informe PDF, Comparación de coeficientes (CSV)

📂 **Ver notebook:** [TP4/Program_TP4_Grupo10.ipynb](./TP4/Program_TP4_Grupo10.ipynb)

---

### 🔄 TP Final: Predicción de Precios de Commodities

**Estado:** En desarrollo 🔄  
**Fecha entrega:** Diciembre de 2025

**Descripción:**  
Sistema de predicción de precios de commodities agrícolas (maíz, soja, trigo) utilizando modelos tradicionales, series temporales y deep learning. Pipeline automatizado de descarga y procesamiento de datos con múltiples fuentes externas.

**Datos:**
- **Commodities:** 22 activos (granos, energía, metales) desde Yahoo Finance
- **Predictores macro:** 7 índices (VIX, DXY, S&P500, tasas, etc.)
- **Features académicas:** CFTC (11), GDELT Sentiment (10), BDI (8), Crop Conditions (15), Gov Stocks (9), FRED (33)
- **Dataset final:** 6,731 observaciones × 3,239 features

**Arquitectura de modelos:**
- **Baseline:** Linear Regression, Ridge, Lasso, ElasticNet
- **Tree-based:** Random Forest, XGBoost, LightGBM
- **Time Series:** ARIMA, Prophet
- **Deep Learning:** LSTM univariado, LSTM multivariado con atención, VMD-LSTM (descomposición)
- **Ensemble:** Combinación ARIMA + LSTM
- **Clasificación direccional:** Predicción de subida/bajada de precios
- **Walk-Forward Validation:** Evaluación temporal correcta para series financieras

**Métricas evaluadas:**
- Regresión: RMSE, MAE, MAPE, R²
- Clasificación direccional: Accuracy, F1-Score
- Backtesting: Simulación de trading con señales del modelo

**Estructura del proyecto:**
```
TPFinal/
├── data/                    # Datos (raw, interim, processed, external)
├── notebooks/               # Exploración y modelado
│   ├── 1.0-exploratory/     # EDA inicial
│   ├── 2.0-feature-engineering/  # Features académicas
│   └── 3.0-modeling/        # 12 notebooks de modelos
├── src/                     # Código reutilizable
│   ├── data/                # Descarga y procesamiento
│   ├── features/            # Feature engineering
│   ├── models/              # Entrenamiento
│   └── visualization/       # Gráficos
├── models/                  # Modelos entrenados (.h5, .pkl)
└── reports/                 # Visualizaciones y reportes
```

**Tecnologías:** Python, TensorFlow/Keras, Scikit-learn, XGBoost, LightGBM, Prophet, yfinance, FRED API, USDA NASS API  
**Entregables:** Pipeline automatizado, Notebooks de análisis, Modelos entrenados, Informe final

📂 **Ver detalles:** [TPFinal/README.md](./TPFinal/README.md)

---

## 📁 Estructura del Repositorio

```
BigDataUBA-Grupo10/
├── README.md                        # Este archivo
├── .gitignore                       # Excluye datos/ de cada TP
├── TP1/                             # ✅ Análisis EPH - Pobreza (2005-2025)
├── TP2/                             # ✅ Histogramas, Kernels & No Supervisados
├── TP3/                             # ✅ Clasificación: Logit & KNN
├── TP4/                             # ✅ Regularización (LASSO/Ridge) & CART
└── TPFinal/                         # 🔄 Predicción de Commodities
```

---

## 🚀 Inicio Rápido

### Clonar el repositorio
```bash
git clone https://github.com/paulaleylen/BigDataUBA-Grupo10.git
cd BigDataUBA-Grupo10
```

### Ejecutar TP1
```bash
cd TP1
pip install -r requirements.txt
jupyter notebook Program_TP1_GrupoJLP.ipynb
```

### Ejecutar TP2
```bash
cd TP2
pip install -r requirements.txt
jupyter notebook Program_TP2_Grupo10.ipynb
```

### Ejecutar TP3
```bash
cd TP3
pip install -r ../TP1/requirements.txt
jupyter notebook Program_TP3_Grupo10.ipynb
```

### Ejecutar TP4
```bash
cd TP4
pip install -r ../TP1/requirements.txt
jupyter notebook Program_TP4_Grupo10.ipynb
```

### Ejecutar TP Final
```bash
cd TPFinal
pip install -e .                          # Instala paquete en modo editable
make data                                  # Descarga y procesa todos los datos (~20 min)
jupyter notebook notebooks/3.0-modeling/  # Explora notebooks de modelado
```

**Nota:** Descargar datos EPH desde [INDEC](https://www.indec.gob.ar/) y colocar en `TP*/datos/` (ver README de cada TP)

---

## 📋 Convenciones del Equipo

### Workflow Git
- **Antes de trabajar:** Siempre `git pull origin main`
- **Commits selectivos:** `git add TP*/archivo.py` (no `git add .`)
- **Mensajes claros:** En español, descriptivos del cambio
- **NO subir:** Carpetas `datos/` y `data/` (ver `.gitignore`)

### Estándares del Proyecto
- **Gráficos:** Usar módulo `estilo_graficos.py` (colores UBA-FCE)
- **Formato números:** Argentino (1.000,50)
- **Región análisis EPH:** Gran Buenos Aires (región 1)
- **Branches:** Trabajar en `main`
- **Documentación:** LaTeX con template KOMA-Script

---

## 📖 Recursos

- **Repositorio:** https://github.com/paulaleylen/BigDataUBA-Grupo10
- **EPH-INDEC:** https://www.indec.gob.ar/indec/web/Institucional-Indec-BasesDeDatos
- **Yahoo Finance:** https://finance.yahoo.com
- **FRED API:** https://fred.stlouisfed.org/docs/api/
- **Cookiecutter Data Science:** https://drivendata.github.io/cookiecutter-data-science/

---

**Universidad de Buenos Aires - Facultad de Ciencias Económicas**  
**Taller de Programación - Big Data | 2025**





