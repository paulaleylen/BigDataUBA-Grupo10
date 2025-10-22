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
| Luis Mella| [Completar] | [@usuario3](https://github.com/usuario3) |

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

## 📁 Estructura del Repositorio

```
BigDataUBA-GrupoJLP/
├── README.md                        # Este archivo
├── .gitignore                       # Excluye datos/ de cada TP
└── TP1/                            # ✅ Trabajo Práctico 1
```

---

## 🚀 Inicio Rápido

### Clonar el repositorio
```bash
git clone https://github.com/paulaleylen/BigDataUBA-GrupoJLP.git
cd BigDataUBA-GrupoJLP
```

### Ejecutar TP1
```bash
cd TP1
pip install -r requirements.txt
jupyter notebook Program_TP1_GrupoJLP.ipynb
```

**Nota:** Descargar datos EPH desde [INDEC](https://www.indec.gob.ar/) y colocar en `TP1/datos/` (ver [TP1/README.md](./TP1/README.md))

---

## 📋 Convenciones del Equipo

### Workflow Git
- **Antes de trabajar:** Siempre `git pull origin main`
- **Commits selectivos:** `git add TP1/archivo.py` (no `git add .`)
- **Mensajes claros:** En español, descriptivos del cambio
- **NO subir:** Carpetas `datos/` (ver `.gitignore`)

### Estándares del Proyecto
- **Gráficos:** Usar módulo `estilo_graficos.py` (colores UBA-FCE)
- **Formato números:** Argentino (1.000,50)
- **Región análisis:** Gran Buenos Aires (región 1)
- **Branches:** Trabajar en `main`

---

## 📖 Recursos

- **Repositorio:** https://github.com/paulaleylen/BigDataUBA-GrupoJLP
- **EPH-INDEC:** https://www.indec.gob.ar/indec/web/Institucional-Indec-BasesDeDatos
- **Documentación TP1:** [TP1/README.md](./TP1/README.md)

---

**Universidad de Buenos Aires - Facultad de Ciencias Económicas**  
**Taller de Programación - 2025**




