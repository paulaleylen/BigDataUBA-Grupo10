# TP1 - Análisis EPH: Pobreza en Gran Buenos Aires (2005-2025)

**Universidad de Buenos Aires - Facultad de Ciencias Económicas**  
**Taller de Programación - 2025**

📦 **Repositorio:** https://github.com/paulaleylen/BigDataUBA-GrupoJLP

---

## 🎯 Objetivo

Análisis comparativo de pobreza en Gran Buenos Aires usando la Encuesta Permanente de Hogares (EPH-INDEC) para 2005 vs 2025. Incluye limpieza de datos, cálculo de adulto equivalente, identificación de pobres y análisis exploratorio con visualizaciones institucionales UBA-FCE.

---

## 📁 Estructura

```
TP1/
├── Program_TP1_GrupoJLP.ipynb     # Notebook principal ✅
├── estilo_graficos.py              # Módulo estilos UBA-FCE
├── requirements.txt                # Dependencias Python
├── tabla_adulto_equiv.xlsx         # Adulto equivalente INDEC
├── datos/                          # ⚠️ NO en Git (grande)
│   ├── usu_individual_T105.dta     # 2005 individuos
│   ├── usu_individual_T125.xls     # 2025 individuos
│   ├── usu_hogar_T105.dta          # 2005 hogares
│   └── usu_hogar_T125.xls          # 2025 hogares
├── graficos/                       # PNG generados
└── doc/                            # Informe LaTeX
    └── Program_TP1_GrupoJLP.tex
```

---

## 🚀 Setup Rápido

### 1. Clonar
```bash
git clone https://github.com/paulaleylen/BigDataUBA-GrupoJLP.git
cd BigDataUBA-GrupoJLP/TP1
```

### 2. Descargar datos EPH
Ir a https://www.indec.gob.ar/ → Bases de datos → EPH  
Descargar los 4 archivos listados arriba y colocar en `datos/`

### 3. Instalar y ejecutar
```bash
pip install -r requirements.txt
jupyter notebook Program_TP1_GrupoJLP.ipynb
```

---

## 📊 Variables Creadas

| Variable | Descripción |
|----------|-------------|
| `ADULTO_EQUIVALENTE` | Adulto equiv. individual según edad/sexo |
| `AD_EQUIV_HOGAR` | Suma de adultos equiv. por hogar |
| `INGRESO_NECESARIO` | CBT × AD_EQUIV_HOGAR (línea pobreza) |
| `pobre` | 1 si ITF < INGRESO_NECESARIO |

**CBT:** $205.07 (2005) / $365,177 (2025) por adulto equivalente

---

## ⚠️ Notas Técnicas

### Códigos EPH
```python
-9, -1  # → convertir a NaN (no respuesta)
     0  # → MANTENER (sin ingreso es válido)
```

### Missing Estructurales (NO imputar)
- `PP03J` (horas): NA para desocupados/inactivos
- `P21` (ingreso): NA para no ocupados

### Diferencias Formato
| | 2005 | 2025 |
|-|------|------|
| **Archivo** | .dta | .xls |
| **Región** | "Gran Buenos Aires" | 1 |
| **Sexo** | "Varón" | 1 |

---

## � Módulo Gráficos

```python
from estilo_graficos import configurar_estilo_grafico, formatear_ejes, forzar_y_cero

COLORES = configurar_estilo_grafico()

# Usar colores institucionales
ax.bar(..., color=COLORES['azul_uba'])  # UBA blue
ax.bar(..., color=COLORES['bordo'])      # FCE burgundy

# Formato argentino automático
formatear_ejes(ax, y_as='numero')  # 1.000,50
forzar_y_cero(ax)  # Barras desde cero
```

---

## � Resultados Principales

- **Pobreza:** 26.88% (2005) → 58.86% (2025) (+31.98 pp)
- **No respuesta ITF:** 1.2% → 40.0% (×33)
- **Cambio demográfico:** Inversión composición por sexo
- **Educación:** Ya no protege contra pobreza en 2025

Ver notebook y documento LaTeX para análisis completo.

---

## 🔧 Workflow Git

```bash
# Antes de trabajar
git pull origin main

# Después de trabajar
git add TP1/
git commit -m "Descripción clara del cambio"
git push origin main
```

**Reglas:**
- SIEMPRE `pull` antes de editar
- NO subir carpeta `datos/`
- Mensajes de commit claros

---

## 📚 Referencias

- **INDEC EPH:** https://www.indec.gob.ar/
- **Metodología:** Método del ingreso (CBT vs ITF)
- **Región:** Gran Buenos Aires (REGION = 1)

---

**Grupo JLP - UBA FCE - 2025**
