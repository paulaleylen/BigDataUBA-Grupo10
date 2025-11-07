# AI Agent Instructions - BigDataUBA-GrupoJLP

## Project Context

This is an academic project for Universidad de Buenos Aires (UBA) - Facultad de Ciencias Económicas, analyzing Argentina's Permanent Household Survey (EPH/Encuesta Permanente de Hogares) data from INDEC. The analysis compares 2005 vs 2025 data for Gran Buenos Aires to study poverty and labor market dynamics.

**Repository:** https://github.com/paulaleylen/BigDataUBA-GrupoJLP  
**Assignment:** Trabajo Práctico N° 1 - Un Primer Encuentro con la EPH

## Critical Architecture Decisions

### Graphics Module Pattern (ALWAYS FOLLOW)

**Module:** `TP1/estilo_graficos.py` - Centralized styling for ALL visualizations

```python
# ✅ CORRECT - Import and configure at notebook initialization
from estilo_graficos import UBA_FCE_COLORS, configurar_estilo_grafico, formatear_ejes, forzar_y_cero
COLORES = configurar_estilo_grafico(dpi=120, base_fontsize=10, variante="claro")

# ✅ CORRECT - Use institutional colors
ax.bar(..., color=COLORES['azul_uba'])  # UBA blue
ax.bar(..., color=COLORES['bordo'])     # FCE burgundy

# ✅ CORRECT - Apply utility functions
forzar_y_cero(ax)  # Bar charts MUST start at zero
formatear_ejes(ax, y_as='numero', max_ticks=6)  # Argentine format: 1.000,50

# ❌ NEVER set styles in notebook cells
# NO: plt.style.use('seaborn')
# NO: sns.set_palette(...)
# NO: plt.rcParams.update({...})
```

**Why:** User explicitly demanded "sin grids, bonitos, prolijos asi se repite un mismo estilo siempre" (no grids, beautiful, clean with consistent style). All styling MUST come from the module to avoid inconsistencies.

### Data Loading Pattern - Dual Format Handling

EPH data format changed between years:
- **2005:** Stata format (`.dta`), uses text for regions ("Gran Buenos Aires")
- **2025:** Excel format (`.xls`), uses numeric codes for regions (1, 40, 41, etc.)

```python
# ALWAYS standardize columns first
df_2005.columns = df_2005.columns.str.upper()
df_2025.columns = df_2025.columns.str.upper()

# Map 2005 text regions to numeric codes for consistency
MAPEO_REGIONES_2005 = {
    1: 'Gran Buenos Aires',
    40: 'NOA', 41: 'NEA', 42: 'Cuyo', 43: 'Pampeana', 44: 'Patagónica'
}
```

### Display Pattern - ALWAYS Use `display()`

```python
from IPython.display import display

# ✅ CORRECT - Use display() for ALL DataFrames
display(df.head())
display(missing_analysis)
display(correlation_table)

# ❌ WRONG - Don't rely on implicit printing
df.head()  # This works but is not explicit
```

**Reason:** Explicit is better than implicit. `display()` ensures proper HTML rendering in Jupyter notebooks.

## Data Cleaning Conventions

### Missing Value Codes (EPH-Specific)

INDEC uses special codes for non-response:
- `-9` = No sabe / No responde (don't know / no answer)
- `-1` = No responde / No corresponde (no answer / doesn't apply)
- `0` = **VALID** value (no income)

```python
# Clean income variables by converting negative codes to NaN
variables_ingreso = ['IPCF', 'ITF', 'P21']
for var in variables_ingreso:
    df_limpio.loc[df_limpio[var] < 0, var] = np.nan
```

**Critical:** Zero (0) is a valid value representing "no income" - NEVER convert it to NaN.

### Variables with Structural Missing Values

- `PP03J` (hours worked): Missing for unemployed/inactive persons **by design**
- `P21` (main occupation income): Missing for non-employed persons **by design**
- `CAT_INAC` (inactivity category): Only applies to inactive persons

Don't impute these - they're structurally missing, not data quality issues.

## Temporal Comparison Workflow

```python
# Standard pattern for 2005 vs 2025 analysis
df_2005_region['ANO'] = 2005
df_2025_region['ANO'] = 2025
df_completo = pd.concat([df_2005_region, df_2025_region], ignore_index=True)

# Filter by year when needed
df_2005_viz = df_trabajo[df_trabajo['ANO'] == 2005]
df_2025_viz = df_trabajo[df_trabajo['ANO'] == 2025]
```

## Correlation Analysis Pattern

When creating correlation matrices with categorical variables:

1. **Create dummy variables with Spanish labels** (not generic Parentesco_1.0):
```python
ch07_mapping = {
    'Parentesco_1.0': 'Jefe_Hogar',
    'Parentesco_2.0': 'Conyuge',
    'Parentesco_3.0': 'Hijo'
}
```

2. **Separate matrices by year** - Don't merge 2005+2025 into one correlation:
```python
df_dummy_2005 = crear_dummies_correlacion(df_corr_2005, 2005)
df_dummy_2025 = crear_dummies_correlacion(df_corr_2025, 2025)
corr_2005 = df_dummy_2005.corr()
corr_2025 = df_dummy_2025.corr()
```

3. **Use separate 16x14 heatmaps** for legibility with 30+ variables

## Argentine Number Formatting

Use the module's Spanish formatters:
- Thousands separator: `.` (punto)
- Decimal separator: `,` (coma)
- Example: `1.234.567,89`

```python
# Already implemented in estilo_graficos.py
formatear_ejes(ax, y_as='numero')  # Auto-applies Argentine format
formatear_ejes(ax, y_as='porcentaje')  # For percentages: 25,3%
```

## File Organization

```
TP1/
├── Program_TP1_GrupoJLP.ipynb    # Main analysis notebook
├── estilo_graficos.py             # Graphics module (DO NOT modify lightly)
├── datos/                         # EPH data (NOT in Git - .gitignore)
│   ├── usu_individual_T105.dta   # 2005 individuals
│   ├── usu_individual_T125.xls   # 2025 individuals
│   ├── usu_hogar_T105.dta        # 2005 households
│   └── usu_hogar_T125.xls        # 2025 households
├── graficos/                      # Output visualizations
│   ├── composicion_sexo_2005_2025.png
│   ├── matriz_correlacion_2005.png
│   └── matriz_correlacion_2025.png
└── requirements.txt               # Python dependencies
```

## Academic Documentation Requirements

The user needs **professional, academic-style markdown analysis** for each section:

1. **No emojis** - User explicitly stated "sin emojis, serio y como para entregar"
2. **Comprehensive explanations** (80+ lines for complex analyses like correlations)
3. **Structured format:**
   - Methodology description
   - Results presentation
   - Interpretation with domain knowledge
   - Statistical validation
   - Temporal comparisons when relevant

Example quality level from existing notebook:
```markdown
**Análisis de las matrices de correlación 2005 vs 2025:**

Se construyeron matrices de correlación para ambos períodos...

**1. Correlaciones estructurales más fuertes:**
- **Ocupado vs Desocupado/Inactivo** (r ≈ -0.70 a -0.80): Correlación negativa...
```

## Key Variables Reference

**Mandatory (obligatorias):**
- `CH04`: Sex (1=Male, 2=Female)
- `CH06`: Age in years
- `CH07`: Household relationship
- `CH08`: Marital status
- `NIVEL_ED`: Education level
- `ESTADO`: Employment status (Employed/Unemployed/Inactive)
- `CAT_INAC`: Inactivity category
- `IPCF`: Per capita family income (**critical for poverty measurement**)

**Selected additional:**
- `ITF`: Total family income
- `P21`: Main occupation income
- `CAT_OCUP`: Occupational category
- `PP03J`: Hours worked per week

## Testing & Validation

No formal test suite, but validate:
1. **Region filtering:** Always check observation counts match expected values
2. **Join validation:** Use all 4 join types (inner, left, right, outer) and verify they match
3. **Missing values:** Verify cleaning adds expected number of NaNs
4. **Graphics output:** Always check `graficos/` folder for saved PNG files

## Common Pitfalls

❌ **Don't** set matplotlib styles in notebook cells  
❌ **Don't** convert zero income values to NaN  
❌ **Don't** merge 2005+2025 correlation matrices  
❌ **Don't** use grids in visualizations (user hates them)  
❌ **Don't** commit EPH data files to Git (they're large)  
❌ **Don't** use emojis in academic markdown sections

✅ **Do** use `estilo_graficos.py` functions consistently  
✅ **Do** use `display()` for all DataFrames  
✅ **Do** maintain Spanish variable labels throughout  
✅ **Do** save all plots to `graficos/` folder  
✅ **Do** write comprehensive markdown analysis (50-80 lines minimum for major sections)

## Dependencies & Environment

```bash
pip install -r requirements.txt
```

Key versions:
- pandas >= 2.0.0 (for mixed-type data handling)
- matplotlib >= 3.7.0 (for rcParams compatibility)
- seaborn >= 0.12.0 (for correlation heatmaps)
- openpyxl >= 3.1.0 (for Excel file reading)

## Git Workflow

Standard academic workflow:
- Commit working changes regularly
- Final commit message: "Entrega final del TP"
- **No commits after submission deadline** (explicitly stated in README)

---

## TP3 - Machine Learning Classification Models (CRITICAL UPDATES)

### Project Context: Poverty Prediction with Logit & KNN

TP3 focuses on **binary classification** to predict poverty status using EPH 2025 data. The assignment explicitly requires:
- **Only Logit and KNN models** (no ensembles, no other algorithms)
- Prediction on **two populations**: respondieron (with IPCF) and norespondieron (without IPCF)
- Policy-oriented evaluation emphasizing **Recall over Precision**

### Data Architecture: Dual Population Handling

**CRITICAL:** TP3 works with TWO separate populations:

1. **respondieron_2025** (7,236 obs with IPCF data):
   - Used for training and testing models
   - 40.8% poverty rate
   - Complete income information

2. **no_respondieron_2025** (45,425 obs without IPCF):
   - Cannot calculate poverty directly (missing IPCF)
   - Used for final predictions with trained models
   - Younger population (36.8 vs 38.8 years)
   - Selection bias issues

```python
# Standard pattern for identifying non-respondents
respondieron_2025 = df[df['ANO'] == 2025].copy()
ids_respondieron = set(
    respondieron_2025['CODUSU'].astype(str) + '_' + 
    respondieron_2025['NRO_HOGAR'].astype(str) + '_' + 
    respondieron_2025['COMPONENTE'].astype(str)
)
df_2025_completo['ID'] = (
    df_2025_completo['CODUSU'].astype(str) + '_' + 
    df_2025_completo['NRO_HOGAR'].astype(str) + '_' + 
    df_2025_completo['COMPONENTE'].astype(str)
)
no_respondieron_2025 = df_2025_completo[
    ~df_2025_completo['ID'].isin(ids_respondieron)
].copy()
```

### Variable Mapping Requirements

**CRITICAL:** Original EPH variables must be mapped to match TP2 conventions:

```python
# ALWAYS map these variables for consistency
no_respondieron_2025['EDAD'] = no_respondieron_2025['CH06']
no_respondieron_2025['SEXO'] = no_respondieron_2025['CH04']
no_respondieron_2025['PP03J'] = no_respondieron_2025['PP03J'].fillna(0)
no_respondieron_2025['CAT_OCUP'] = no_respondieron_2025['CAT_OCUP'].fillna(0)
```

**Why:** TP2 cleaned data uses SEXO/EDAD, but original EPH uses CH04/CH06. Both populations need consistent variable names for dummy encoding.

### Model Configuration Standards

#### Logistic Regression (Logit)

```python
# ✅ CORRECT Configuration
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression

scaler_logit = StandardScaler()
X_train_logit = scaler_logit.fit_transform(X_train)
X_test_logit = scaler_logit.transform(X_test)

logit = LogisticRegression(
    random_state=444,
    max_iter=1000,
    class_weight='balanced'  # CRITICAL for imbalanced data
)
logit.fit(X_train_logit, y_train)
```

**Key points:**
- ✅ StandardScaler improves convergence
- ✅ `class_weight='balanced'` handles 40.8% vs 59.2% imbalance
- ✅ `random_state=444` for reproducibility (TP requirement)
- ❌ **DO NOT apply SMOTE to Logit** - use class_weight instead

#### K-Nearest Neighbors (KNN)

```python
# ✅ CORRECT Configuration with SMOTE
from imblearn.over_sampling import SMOTE
from sklearn.neighbors import KNeighborsClassifier

# Apply SMOTE with CONSERVATIVE ratio
smote = SMOTE(
    random_state=444,
    sampling_strategy=0.7,  # Minority = 70% of majority
    k_neighbors=5
)
X_train_smote, y_train_smote = smote.fit_resample(X_train, y_train)
# Result: 5,035 → 5,067 obs (only +32 synthetic examples)

# Scale AFTER SMOTE
scaler = StandardScaler()
X_train_sc = scaler.fit_transform(X_train_smote)
X_test_sc = scaler.transform(X_test)

# Optimize K via Cross-Validation
k_vals = range(1, 11)
cv_scores = []
for k in k_vals:
    knn = KNeighborsClassifier(n_neighbors=k)
    scores = cross_val_score(knn, X_train_sc, y_train_smote, cv=5)
    cv_scores.append(scores.mean())

k_opt = k_vals[np.argmax(cv_scores)]  # Typically K=8

# Final model
knn_final = KNeighborsClassifier(n_neighbors=k_opt)
knn_final.fit(X_train_sc, y_train_smote)
```

**Key points:**
- ✅ SMOTE with `sampling_strategy=0.7` is CONSERVATIVE (not 1.0)
- ✅ Prevents overfitting while improving minority class recall
- ✅ Scale AFTER SMOTE (synthetic points need scaling too)
- ✅ K optimization via 5-fold CV, not train accuracy
- ❌ **DO NOT use K=1** (high variance, overfitting)

### Train/Test Split Requirements

```python
# ✅ CORRECT - Must follow TP specifications
X_train, X_test, y_train, y_test = train_test_split(
    X, y,
    test_size=0.30,      # 70-30 split (TP requirement)
    random_state=444,    # TP-specified seed
    stratify=y           # Maintain 40.8% in both sets
)
```

**Validation checks:**
```python
# ALWAYS verify balance
assert abs(y_train.mean() - y_test.mean()) < 0.01  # Within 1%
assert len(X_train) / len(X) >= 0.69  # Approximately 70%
```

### Dummy Encoding Pattern for Predictions

**CRITICAL:** When predicting on no_respondieron, dummies MUST match training:

```python
# Prepare non-respondent data
X_no_resp = no_respondieron_2025[variables_predictoras].copy()
X_no_resp = pd.get_dummies(
    X_no_resp,
    columns=['SEXO', 'NIVEL_ED', 'ESTADO', 'CAT_OCUP'],
    drop_first=True,
    dtype=int
)

# CRITICAL: Ensure same columns as training
for col in X_train.columns:
    if col not in X_no_resp.columns:
        X_no_resp[col] = 0  # Add missing dummies

X_no_resp = X_no_resp[X_train.columns]  # Enforce column order

# Scale using training scaler
X_no_resp_sc = scaler.transform(X_no_resp)
X_no_resp_logit = scaler_logit.transform(X_no_resp)

# Predict
pred_logit = logit.predict(X_no_resp_logit)
pred_knn = knn_final.predict(X_no_resp_sc)
```

**Why this matters:** If non-respondents have different categorical levels (e.g., a NIVEL_ED category not in train), the dummy matrix will be misaligned and predictions will fail or be wrong.

### Model Evaluation for Policy Applications

**CRITICAL INSIGHT:** For poverty policy, **Error Type II (False Negative) is MORE costly** than Error Type I (False Positive).

```python
# Priority metrics for poverty programs
from sklearn.metrics import (
    accuracy_score, precision_score, 
    recall_score, f1_score, roc_auc_score
)

# ✅ Recall is PRIMARY metric for social policy
recall_logit = recall_score(y_test, y_pred_logit)  # ~55%
recall_knn = recall_score(y_test, y_pred_knn)      # ~23%

# Minimize False Negatives (pobres no detectados)
cm = confusion_matrix(y_test, y_pred)
fn = cm[1, 0]  # Pobres clasificados como no pobres - CRITICAL
```

**Model selection criteria for TP3:**
1. **Maximize Recall** (detect as many poor as possible)
2. Accept moderate Precision (some false positives tolerable)
3. **Logit typically wins** due to higher Recall (~55% vs ~23%)

**Why:** Excluding a poor person from food assistance (FN) has irreversible humanitarian cost. Including a non-poor person (FP) has only financial cost.

### Selection Bias in Non-Respondents

**CRITICAL FINDING:** Non-respondents have systematically different characteristics:

```python
# Compare populations
print(f"EDAD media: Train={X_train['EDAD'].mean():.1f}")  # 38.8 years
print(f"EDAD media: No_resp={X_no_resp['EDAD'].mean():.1f}")  # 36.8 years

# Logit predictions on non-respondents are VERY conservative
prob_logit = logit.predict_proba(X_no_resp_logit)[:, 1]
print(f"Logit mean prob: {prob_logit.mean():.3f}")  # 0.133 (13.3%)
print(f"Logit predicts: {(prob_logit > 0.5).sum()}")  # Only 86 pobres (0.2%)

# KNN is more flexible
prob_knn = knn_final.predict_proba(X_no_resp_sc)[:, 1]
print(f"KNN mean prob: {prob_knn.mean():.3f}")  # 0.399 (39.9%)
print(f"KNN predicts: {(prob_knn > 0.5).sum()}")  # 9,544 pobres (21.0%)
```

**Interpretation:**
- Logit parametric model extrapolates poorly to different population
- Linear coefficients learned on 38.8-year-olds don't fit 36.8-year-olds well
- KNN non-parametric approach adapts better to different profiles
- **Selection bias matters:** Who doesn't respond income is NOT random

### Markdown Documentation Standards for TP3

Each section needs comprehensive markdown following this structure:

**A. Enfoque de validación:**
- Train/test split justification (70-30, stratified)
- Variable selection rationale (why exclude IPCF from X)
- Balance verification with t-tests
- 40-60 lines of explanation

**B. Regresión Logística:**
- Model specification (StandardScaler, class_weight)
- Coefficient interpretation with Odds Ratios (OR)
- Probability visualization vs age
- Statistical significance (p-values from CV)
- 60-80 lines

**C. K-Nearest Neighbors:**
- SMOTE justification (why 0.7 ratio, not 1.0)
- K={1,5,10} comparison showing overfitting in K=1
- Cross-validation for optimal K
- Decision boundary visualization (2D plot)
- Trade-off sesgo-varianza explanation
- 70-90 lines

**D. Evaluación y aplicación:**
- Confusion matrices interpretation (FN vs FP costs)
- ROC curves and AUC comparison
- Metrics table with policy context
- **Model recommendation with justification** (Logit for Recall)
- Non-respondent predictions with selection bias discussion
- 80-100 lines

### Common TP3 Pitfalls

❌ **Don't** use ensembles (Random Forest, XGBoost) - TP requires only Logit & KNN  
❌ **Don't** apply SMOTE to Logit - use `class_weight='balanced'` instead  
❌ **Don't** use SMOTE ratio=1.0 (50-50 balance) - too aggressive, use 0.7  
❌ **Don't** optimize K using train accuracy - use cross-validation  
❌ **Don't** forget to map CH04→SEXO, CH06→EDAD for non-respondents  
❌ **Don't** prioritize Accuracy or Precision for poverty policy - prioritize Recall  
❌ **Don't** ignore selection bias in non-respondent predictions

✅ **Do** verify dummy columns align between train and non-respondents  
✅ **Do** use separate scalers for Logit and KNN (they use different data)  
✅ **Do** compare probability distributions to diagnose conservative predictions  
✅ **Do** emphasize humanitarian cost of False Negatives in policy discussion  
✅ **Do** document why Logit is recommended despite similar AUC (~0.555)  
✅ **Do** explain that 0.2% poverty in non-respondents suggests different population
