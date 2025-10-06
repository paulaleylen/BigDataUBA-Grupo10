"""
Módulo de configuración de estilo para gráficos del TP1
Universidad de Buenos Aires - Facultad de Ciencias Económicas
Taller de Programación - Grupo JLP

Este módulo define el estilo visual consistente para todos los gráficos
del análisis exploratorio de datos de la EPH, siguiendo pautas de 
visualización académica y la identidad visual de UBA Económicas.
"""

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import FuncFormatter, MaxNLocator
from cycler import cycler


# Paleta de colores oficial UBA Económicas
# Basada en la identidad visual institucional
UBA_FCE_COLORS = {
    # Colores principales UBA
    'azul_uba': '#0C234B',          # Azul institucional profundo
    'azul_medio': '#2E6FA7',        # Azul medio académico
    'celeste': '#6EC1E4',           # Celeste de apoyo
    
    # Colores Económicas
    'bordo': '#8B1538',             # Bordo característico FCE
    'verde_eco': '#1B998B',         # Verde-azulado distintivo
    
    # Colores de apoyo
    'gris_oscuro': '#5F6A6A',       # Gris para texto
    'gris_claro': '#E9ECEF',        # Gris de fondo
    'naranja': '#F18F01',           # Naranja para acentos
    'rojo': '#D7263D',              # Rojo para alertas
    
    # Alias para compatibilidad
    'primario': '#0C234B',
    'secundario': '#8B1538',
    'acento1': '#1B998B',
    'acento2': '#F18F01',
    'neutro': '#5F6A6A',
    'comparacion': ['#0C234B', '#8B1538']  # Para comparaciones 2005 vs 2025
}


def _numero_es(x, pos):
    """Formato argentino: punto para miles, coma para decimales"""
    if abs(x) >= 1e6:
        return f"{x/1e6:,.1f}M".replace(",", "_").replace(".", ",").replace("_", ".")
    elif abs(x) >= 1e3:
        return f"{x:,.0f}".replace(",", "_").replace(".", ",").replace("_", ".")
    else:
        return f"{x:,.1f}".replace(",", "_").replace(".", ",").replace("_", ".")


def _porcentaje_es(x, pos):
    """Formato de porcentaje argentino"""
    return f"{100*x:,.1f}%".replace(",", "_").replace(".", ",").replace("_", ".")


def configurar_estilo_grafico(dpi=120, base_fontsize=10, variante="claro"):
    """
    Configura un estilo consistente y profesional para todos los gráficos del análisis.
    Sin grids, colores institucionales UBA FCE, fuentes legibles.
    
    Principios de diseño:
    - Barras siempre parten de cero
    - Sin espinas superiores/derechas
    - Sin grid por defecto
    - Ticks hacia fuera, pocos marcadores
    - Tipografía sans-serif limpia
    
    Parameters:
    -----------
    dpi : int, default=120
        Resolución de la figura
    base_fontsize : int, default=10
        Tamaño base de fuente
    variante : str, default="claro"
        'claro' para fondo blanco, 'oscuro' para fondo oscuro
    
    Returns:
    --------
    dict: Diccionario con paleta de colores UBA FCE
    """
    # Configuración de colores según variante
    fondo_fig = "white" if variante == "claro" else "#0E1117"
    fondo_axes = "white" if variante == "claro" else "#0E1117"
    color_texto = UBA_FCE_COLORS["gris_oscuro"] if variante == "claro" else "#FFFFFF"
    
    # Ciclo de colores institucionales
    ciclo_colores = [
        UBA_FCE_COLORS["azul_uba"],
        UBA_FCE_COLORS["bordo"],
        UBA_FCE_COLORS["verde_eco"],
        UBA_FCE_COLORS["azul_medio"],
        UBA_FCE_COLORS["celeste"],
        UBA_FCE_COLORS["naranja"]
    ]
    
    # Configuración base de matplotlib
    plt.rcParams.update({
        # Figura
        'figure.facecolor': fondo_fig,
        'figure.edgecolor': fondo_fig,
        'figure.figsize': (10, 6),
        'figure.dpi': dpi,
        'figure.autolayout': False,
        
        # Ejes
        'axes.facecolor': fondo_axes,
        'axes.edgecolor': color_texto,
        'axes.linewidth': 1.0,
        'axes.grid': False,  # Sin grids
        'axes.spines.top': False,
        'axes.spines.right': False,
        'axes.titlesize': base_fontsize + 3,
        'axes.titleweight': 'bold',
        'axes.labelsize': base_fontsize + 1,
        'axes.labelcolor': color_texto,
        'axes.labelweight': 'normal',
        'axes.prop_cycle': cycler(color=ciclo_colores),
        
        # Líneas y markers
        'lines.linewidth': 2,
        'lines.markersize': 8,
        
        # Fuentes
        'font.family': 'sans-serif',
        'font.sans-serif': ['Arial', 'DejaVu Sans', 'Liberation Sans'],
        'font.size': base_fontsize,
        
        # Leyenda
        'legend.frameon': False,
        'legend.fontsize': base_fontsize,
        'legend.title_fontsize': base_fontsize,
        
        # Ticks
        'xtick.labelsize': base_fontsize,
        'ytick.labelsize': base_fontsize,
        'xtick.color': color_texto,
        'ytick.color': color_texto,
        'xtick.direction': 'out',
        'ytick.direction': 'out',
        'xtick.major.size': 4,
        'ytick.major.size': 4,
        
        # Guardado
        'savefig.facecolor': fondo_fig,
        'savefig.edgecolor': fondo_fig,
        'savefig.dpi': dpi,
        'savefig.bbox': 'tight',
        'savefig.pad_inches': 0.15,
    })
    
    return UBA_FCE_COLORS


def formatear_ejes(ax, y_as="numero", x_as=None, max_ticks=6):
    """
    Formatea ejes con pocos ticks y formato argentino (punto miles, coma decimal).
    
    Parameters:
    -----------
    ax : matplotlib.axes.Axes
        Eje a formatear
    y_as : str, default='numero'
        Formato del eje Y: 'numero' | 'porcentaje' | None
    x_as : str, default=None
        Formato del eje X: 'numero' | 'porcentaje' | None
    max_ticks : int, default=6
        Número máximo de ticks
    """
    ax.yaxis.set_major_locator(MaxNLocator(nbins=max_ticks, integer=False, min_n_ticks=3))
    ax.xaxis.set_major_locator(MaxNLocator(nbins=max_ticks, integer=False, min_n_ticks=3))
    
    if y_as == "numero":
        ax.yaxis.set_major_formatter(FuncFormatter(_numero_es))
    elif y_as == "porcentaje":
        ax.yaxis.set_major_formatter(FuncFormatter(_porcentaje_es))
    
    if x_as == "numero":
        ax.xaxis.set_major_formatter(FuncFormatter(_numero_es))
    elif x_as == "porcentaje":
        ax.xaxis.set_major_formatter(FuncFormatter(_porcentaje_es))


def forzar_y_cero(ax):
    """
    Asegura que el eje Y comience en 0 para gráficos de barras/columnas.
    Principio fundamental: las barras deben partir de cero para evitar distorsiones visuales.
    """
    ymin, ymax = ax.get_ylim()
    ax.set_ylim(bottom=0, top=max(ymax, 0))


def limpiar_estetica(ax):
    """
    Reduce elementos distractores: elimina grids si quedaron, mantiene solo spines izq/inf.
    """
    ax.grid(False)
    for lado in ["top", "right"]:
        ax.spines[lado].set_visible(False)


def set_labels(ax, titulo, subtitulo=None, fuente=None, nota=None):
    """
    Integra texto y gráfico en una sola unidad informativa.
    Sigue principios de visualización académica: título claro, fuente citada, notas metodológicas.
    
    Parameters:
    -----------
    ax : matplotlib.axes.Axes
        Eje del gráfico
    titulo : str
        Título principal en negrita
    subtitulo : str, optional
        Subtítulo explicativo
    fuente : str, optional
        Fuente de datos
    nota : str, optional
        Nota metodológica o aclaración
    """
    fig = ax.figure
    fig.subplots_adjust(top=0.85, bottom=0.18)
    
    ax.set_title(titulo, loc="left", pad=12)
    
    if subtitulo:
        fig.text(0.125, 0.88, subtitulo, ha="left", va="bottom", 
                fontsize=plt.rcParams["font.size"], 
                color=plt.rcParams["axes.labelcolor"])
    
    pie_y = 0.05
    texto_pie = []
    if fuente:
        texto_pie.append(f"Fuente: {fuente}")
    if nota:
        texto_pie.append(f"Nota: {nota}")
    if texto_pie:
        fig.text(0.125, pie_y, "  |  ".join(texto_pie), 
                ha="left", va="bottom", 
                fontsize=plt.rcParams["font.size"]-1, 
                color=plt.rcParams["axes.labelcolor"])


def anotar_barras(ax, fmt="numero", desplazamiento=3):
    """
    Etiqueta el valor al final de cada barra/columna.
    Evita leyendas innecesarias y facilita la lectura directa de valores.
    
    Parameters:
    -----------
    ax : matplotlib.axes.Axes
        Eje con barras
    fmt : str, default='numero'
        Formato: 'numero' | 'porcentaje'
    desplazamiento : float, default=3
        Desplazamiento de la etiqueta (porcentaje del rango del eje)
    """
    format_fn = _numero_es if fmt == "numero" else _porcentaje_es
    
    for p in ax.patches:
        if p.get_width() > p.get_height():  # barras horizontales
            valor = p.get_width()
            ax.text(p.get_x() + p.get_width() + desplazamiento/100*ax.get_xlim()[1],
                   p.get_y() + p.get_height()/2,
                   format_fn(valor, None),
                   va="center", ha="left", 
                   fontsize=plt.rcParams["font.size"])
        else:  # columnas verticales
            valor = p.get_height()
            ax.text(p.get_x() + p.get_width()/2,
                   p.get_y() + p.get_height() + desplazamiento/100*ax.get_ylim()[1],
                   format_fn(valor, None),
                   va="bottom", ha="center", 
                   fontsize=plt.rcParams["font.size"])


def anotar_linea_ultimo(ax, fmt="numero"):
    """
    Anota el último punto de cada línea.
    Enfatiza el valor final sin necesidad de leyendas extensas.
    
    Parameters:
    -----------
    ax : matplotlib.axes.Axes
        Eje con líneas
    fmt : str, default='numero'
        Formato: 'numero' | 'porcentaje'
    """
    format_fn = _numero_es if fmt == "numero" else _porcentaje_es
    
    for line in ax.get_lines():
        xdata = line.get_xdata()
        ydata = line.get_ydata()
        if len(xdata) == 0:
            continue
        x, y = xdata[-1], ydata[-1]
        ax.text(x, y, "  " + format_fn(y, None), 
               va="center", ha="left", 
               fontsize=plt.rcParams["font.size"])


# Paleta de colores global (compatibilidad con código existente)
COLORES = configurar_estilo_grafico()


# Exportar también bajo el nombre UBA_COLORS para compatibilidad
UBA_COLORS = UBA_FCE_COLORS
