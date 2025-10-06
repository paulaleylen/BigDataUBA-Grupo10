# Trabajo Práctico N° 1 - Un Primer Encuentro con la EPH

## Grupo JLP

**Universidad de Buenos Aires - 2025**  
**Taller de Programación**

**Repositorio:** https://github.com/paulaleylen/BigDataUBA-GrupoJLP

---

## 🎯 Estado del Proyecto

**Última actualización:** 6 de octubre de 2025

### ✅ Completado (Parte I y II)
- ✅ Configuración inicial y módulo de gráficos (`estilo_graficos.py`)
- ✅ Carga de datos EPH 2005 y 2025 (Gran Buenos Aires)
- ✅ Estandarización de columnas y mapeo de regiones
- ✅ Selección de 16 variables de interés
- ✅ Análisis de valores faltantes con visualización
- ✅ Limpieza de datos (códigos EPH -9, -1)
- ✅ Unión de bases Individuos-Hogares (4 tipos de join)
- ✅ Análisis exploratorio: composición por sexo (2005 vs 2025)
- ✅ Matrices de correlación con variables dummy (30+ variables)
- ✅ Análisis de correlaciones significativas

### 🔄 En Progreso
- 🔄 Análisis descriptivo ampliado (Parte II - Sección restante)
- 🔄 Cálculo de adulto equivalente
- 🔄 Medición de pobreza e indigencia

### ⏳ Pendiente
- ⏳ Pirámide poblacional
- ⏳ Distribución de ingresos (percentiles, Gini)
- ⏳ Clasificación de hogares pobres/indigentes
- ⏳ Brecha de pobreza
- ⏳ Análisis por región
- ⏳ Conclusiones finales
- ⏳ Generación del PDF (máximo 5 páginas)

---

## 📋 Descripción del Proyecto

Este trabajo práctico tiene como objetivo familiarizarnos con la base de datos de la **Encuesta Permanente de Hogares (EPH)** del INDEC. El análisis compara datos de 2005 vs 2025 para Gran Buenos Aires e incluye:

- Limpieza de datos EPH (códigos especiales INDEC)
- Tratamiento de valores faltantes estructurales
- Análisis exploratorio con visualizaciones institucionales UBA FCE
- Medición de pobreza e indigencia según metodología INDEC

---

## 📁 Estructura de Archivos

```
TP1/
├── Program_TP1_GrupoJLP.ipynb          # Jupyter Notebook principal (EN PROGRESO)
├── estilo_graficos.py                  # Módulo de estilos UBA FCE (COMPLETADO)
├── requirements.txt                    # Dependencias Python
├── tabla_adulto_equiv.xlsx             # Tabla de adulto equivalente (pendiente usar)
├── Programación_UBA_TP1 (1).docx      # Consignas del trabajo práctico
├── README.md                           # Este archivo
├── datos/                              # ⚠️ NO SUBIR A GIT (archivos grandes)
│   ├── usu_individual_T105.dta        # 2005 individuos
│   ├── usu_individual_T125.xls        # 2025 individuos
│   ├── usu_hogar_T105.dta             # 2005 hogares
│   ├── usu_hogar_T125.xls             # 2025 hogares
│   └── base_limpia_parte1.csv         # Base procesada (generada automáticamente)
└── graficos/                           # Gráficos generados (PNG)
    ├── figura_missing_values.png       # ✅ Generado
    ├── composicion_sexo_2005_2025.png  # ✅ Generado
    ├── matriz_correlacion_2005.png     # ✅ Generado
    └── matriz_correlacion_2025.png     # ✅ Generado
```

**Importante:** 
- La carpeta `datos/` contiene archivos EPH de ~50MB que NO deben subirse al repositorio
- Los gráficos en `graficos/` SÍ se suben (son PNG livianos)
- El archivo `.gitignore` ya está configurado para excluir `datos/`

---

## 🚀 Guía Git para el Equipo

### Para quien nunca usó Git/GitHub

**GitHub es como Google Drive pero para código.** Permite trabajar en equipo sin pisar cambios de otros.

#### 1️⃣ Primera vez - Clonar

**GitHub Desktop (Recomendado):**
1. Descargar [GitHub Desktop](https://desktop.github.com/)
2. Clone repository → `paulaleylen/BigDataUBA-GrupoJLP`
3. Elegir dónde guardar en tu compu

**Línea de comandos:**
```bash
git clone https://github.com/paulaleylen/BigDataUBA-GrupoJLP.git
cd BigDataUBA-GrupoJLP
```

#### 2️⃣ Antes de trabajar - Actualizar

**SIEMPRE hacer `git pull` antes de modificar:**

```bash
git pull origin main
```

#### 3️⃣ Después de trabajar - Subir cambios

**IMPORTANTE:** Hacer commit solo de lo que modificaste, no de todo.

**Ejemplo - Solo cambios en TP1:**
```bash
# Ver qué archivos cambiaron
git status

# Agregar SOLO la carpeta TP1 (no todo el repo)
git add TP1/

# Commit con mensaje claro
git commit -m "Agregué análisis de pirámide poblacional"

# Subir
git push origin main
```

**Si modificaste solo un archivo:**
```bash
git add TP1/Program_TP1_GrupoJLP.ipynb
git commit -m "Corregí error en limpieza de datos"
git push origin main
```

**Si modificaste el módulo de gráficos:**
```bash
git add TP1/estilo_graficos.py
git commit -m "Agregué función para gráficos de línea"
git push origin main
```

#### ⚠️ Reglas

1. **SIEMPRE `git pull` antes de trabajar**
2. **Hacer commit de lo que tocaste, no de todo** - Usar `git add carpeta/` o `git add archivo.py`
3. **Mensajes claros** - Decir qué hiciste específicamente
4. **NO subir carpeta `datos/`** - Solo código y gráficos PNG
5. **Avisar antes de modificar `estilo_graficos.py`**

---

## 🚀 Configurar el Entorno

### 1. Descargar los Datos

Los datos NO están en el repo (son pesados). Bajarlos del OneDrive del equipo y ponerlos en `TP1/datos/`

**Archivos necesarios:**
- `usu_individual_T105.dta`
- `usu_individual_T125.xls`
- `usu_hogar_T105.dta`
- `usu_hogar_T125.xls`

### 2. Instalar Dependencias

```bash
cd TP1
pip install -r requirements.txt
```

### 3. Abrir el Notebook

En VS Code: abrir carpeta `TP1/` y abrir `Program_TP1_GrupoJLP.ipynb`

**Nota:** Todas las rutas en el notebook son relativas (`datos/archivo.dta`, `graficos/imagen.png`), funcionan en cualquier computadora sin cambios.

---

## 📊 Contenido del Análisis (Estructura del Notebook)

### ✅ Sección 0: Configuración Inicial
- Importación de librerías
- Configuración del módulo de gráficos `estilo_graficos.py`
- Colores institucionales UBA FCE

### ✅ PARTE I: Familiarizándonos con la base EPH y limpieza

#### ✅ 1. ¿Cómo se identifican las personas pobres?
- Metodología INDEC: CBA, CBT, adulto equivalente
- Documentación académica completa

#### ✅ 2.a. Selección de región y unión de bases
- Filtrado: Gran Buenos Aires (código 1)
- Unión temporal: 2005 (9,484 obs) + 2025 (7,181 obs) = 16,665 obs
- Estandarización de columnas y mapeo de regiones

#### ✅ 2.b. Selección de variables y análisis de valores faltantes
- 16 variables seleccionadas (8 obligatorias + 8 adicionales)
- Análisis de NAs: heatmap comparativo 2005 vs 2025
- Identificación de missing estructurales (PP03J: 52.68%)

#### ✅ 2.c. Limpieza de datos
- Códigos EPH: -9 (no sabe), -1 (no responde) → NaN
- Validación: 0 es valor válido (sin ingreso)
- Total limpiado: 961 valores convertidos a NaN

#### ✅ 2.d. Unión de bases Individuos y Hogares
- 4 tipos de join validados (inner, left, right, outer)
- Correspondencia perfecta: 16,665 filas en todos los casos
- Tabla 1 generada con reporte de uniones

### ✅ PARTE II: Primer Análisis Exploratorio

#### ✅ 3. Composición por sexo: 2005 vs 2025
- Gráfico de barras agrupadas con colores UBA
- Distribución estable: ~48% varones, ~52% mujeres
- Análisis markdown de 15+ líneas

#### ✅ 4. Matrices de correlación: 2005 vs 2025
- Creación de 30+ variables dummy con nombres en español
- 2 heatmaps separados 16x14 (sin grid, estilo UBA)
- Análisis exhaustivo de correlaciones (80+ líneas)
- Top 15 correlaciones más significativas identificadas

### 🔄 EN PROGRESO: Análisis descriptivo ampliado
- Pirámide poblacional
- Distribución de ingresos por percentiles
- Características de hogares vs individuos

### ⏳ PENDIENTE: Sección 4 - Medición de Pobreza
- Cálculo de adulto equivalente (usar `tabla_adulto_equiv.xlsx`)
- Definición de líneas CBA y CBT
- Clasificación de hogares (indigentes/pobres/no pobres)
- Análisis por región
- Brecha de pobreza

### ⏳ PENDIENTE: Sección 5 - Conclusiones
- Resumen de hallazgos principales
- Limitaciones del análisis
- Recomendaciones metodológicas

---

## 🎨 Importante: Módulo de Gráficos

Todos los gráficos del proyecto usan el módulo `estilo_graficos.py` que implementa:

✅ **Colores institucionales UBA FCE:**
- `azul_uba` (#0C234B) - Azul institucional
- `bordo` (#8B1538) - Bordo característico FCE
- `verde_eco` (#1B998B) - Verde-azulado
- `comparacion` - Lista para gráficos 2005 vs 2025

✅ **Funciones útiles:**
```python
from estilo_graficos import UBA_FCE_COLORS, configurar_estilo_grafico, formatear_ejes, forzar_y_cero

# Configurar al inicio del notebook
COLORES = configurar_estilo_grafico(dpi=120, base_fontsize=10, variante="claro")

# Usar en gráficos
ax.bar(..., color=COLORES['azul_uba'])
forzar_y_cero(ax)  # Barras SIEMPRE empiezan en 0
formatear_ejes(ax, y_as='numero')  # Formato argentino: 1.000,50

```

**Si necesitas modificar estilos:** Avisar al equipo primero y editar `estilo_graficos.py`

---

## Convenciones del Proyecto

### Variables EPH - Nombres Clave
```python
# Demográficas (obligatorias)
CH04  # Sexo (1=Varón, 2=Mujer)
CH06  # Edad en años
CH07  # Relación de parentesco
CH08  # Estado civil

# Educación y actividad (obligatorias)
NIVEL_ED   # Nivel educativo
ESTADO     # Condición de actividad (Ocupado/Desocupado/Inactivo)
CAT_INAC   # Categoría de inactividad

# Ingresos (obligatorias - CRÍTICAS PARA POBREZA)
IPCF  # Ingreso per cápita familiar
ITF   # Ingreso total familiar

# Mercado laboral (adicionales)
P21       # Ingreso ocupación principal
CAT_OCUP  # Categoría ocupacional
PP03J     # Horas trabajadas
```

### Códigos EPH Especiales
```python
# En variables de ingreso y edad:
-9  # No sabe / No responde → convertir a NaN
-1  # No responde / No corresponde → convertir a NaN
 0  # Sin ingreso → MANTENER (es válido)

# Missing estructurales (no imputar):
# PP03J: NaN para no ocupados
# P21: NaN para no empleados
# CAT_INAC: NaN para ocupados/desocupados
```

### Formato de Números
```python
# SIEMPRE usar formato argentino:
# Separador de miles: punto (.)
# Separador decimal: coma (,)
# Ejemplo: 1.234.567,89

# Usar funciones del módulo:
formatear_ejes(ax, y_as='numero')      # Para cantidades
formatear_ejes(ax, y_as='porcentaje')  # Para porcentajes
```

##  Fecha de Entrega

**8 de septiembre de 2025 a las 17:00 hs**
