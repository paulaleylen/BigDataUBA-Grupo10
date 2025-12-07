# Supply & Demand Features

Archivos de features relacionadas con oferta/demanda de commodities.

## Crop Conditions (USDA NASS)

Features basadas en reportes semanales de condiciones de cultivos (% Good/Excellent).

**Archivos:**
- `crop_conditions_all_features.csv` - 337 obs × 15 features (merged, 2024-2025)
- `crop_condition_corn_features.csv` - 188 obs × 5 features
- `crop_condition_soybeans_features.csv` - 162 obs × 5 features  
- `crop_condition_wheat_features.csv` - 337 obs × 5 features

**Período:** 2024-04-07 → 2025-11-24 (337 días)

**Fuente:** USDA NASS Quick Stats API  
**Script:** `src/data/download_crop_conditions.py`

**Features por commodity (5):**
1. `{commodity}_good_excellent_pct` - % Good + Excellent semanal
2. `{commodity}_crop_condition_change` - Cambio week-over-week
3. `{commodity}_crop_condition_ma4` - Moving average 4 semanas
4. `{commodity}_crop_condition_deviation` - Desviación de promedio histórico
5. `{commodity}_crop_condition_binary` - 1 si > 60%, 0 si < 60%

**Limitación:** Solo 2024-2025 data debido a restricciones NASS API.

---

## Government Stocks (USDA ERS)

Inventarios gubernamentales anuales (ending stocks) de Corn, Soybeans, Wheat.

**Archivos:**
- `government_stocks_ers_all_features.csv` - 23,834 obs × 9 features (merged, 1960-2025)
- `gov_stocks_ers_corn_features.csv` - 23,742 obs × 3 features
- `gov_stocks_ers_soybeans_features.csv` - 16,072 obs × 3 features
- `gov_stocks_ers_wheat_features.csv` - 23,742 obs × 3 features

**Período:** 1960-05-31 → 2025-08-31 (65 años, 23,834 días)

**Fuente:** USDA ERS Yearbooks (CSV/XLSX direct downloads, NO API)  
**Script:** `src/data/download_government_stocks_ers.py`

**Features por commodity (3):**
1. `{commodity}_gov_stocks` - Ending stocks absolutos (bushels)
2. `{commodity}_gov_stocks_change` - Cambio year-over-year (bushels)
3. `{commodity}_gov_stocks_pct_change` - Cambio porcentual YoY

**Fuentes específicas:**
- **Corn:** Feed Grains Yearbook CSV (1960-2025, 66 años)
- **Soybeans:** Oil Crops Yearbook CSV (1980-2024, 45 años)
- **Wheat:** Wheat Data XLSX multi-sheet (1960-2025, 66 años) - Custom parser

**Marketing Year Ends:**
- Corn/Soybeans: August 31
- Wheat: May 31 (diferente!)

**Conversiones:**
- Corn: Million metric tons → bushels (factor: 39.368)
- Soybeans: Million bushels (no conversion)
- Wheat: Million bushels (no conversion)

---

## Archivos Eliminados (Deprecados)

❌ **NASS Government Stocks (deprecated 6 DIC 2025):**
- `government_stocks_all_features.csv` - Solo 244 obs (2025 only)
- `gov_stocks_corn_features.csv`
- `gov_stocks_soybeans_features.csv`
- `gov_stocks_wheat_features.csv`

**Razón eliminación:** NASS API severamente limitado (solo 2025 data), reemplazado por USDA ERS Yearbooks con 60+ años históricos.

---

## Uso en Notebooks

```python
import pandas as pd

# Crop Conditions (solo 2024-2025)
crop = pd.read_csv('data/interim/supply_demand/crop_conditions_all_features.csv')
# 337 obs × 15 features

# Government Stocks (1960-2025, 65 años)
stocks = pd.read_csv('data/interim/supply_demand/government_stocks_ers_all_features.csv')
# 23,834 obs × 9 features

# Merge con dataset principal (on 'date')
final = base.merge(crop, on='date', how='left')  # Left join (crop solo 2024-2025)
final = final.merge(stocks, on='date', how='left')  # Left join (stocks desde 1960)
```

**Nota:** Crop Conditions solo tiene data 2024-2025, usar `how='left'` para evitar perder observaciones del dataset principal (2000-2025).

---

**Última actualización:** 6 de diciembre de 2025
