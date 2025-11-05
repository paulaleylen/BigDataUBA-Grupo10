"""
Visualization utilities

This package contains modules for creating consistent, styled visualizations
following institutional UBA-FCE guidelines.
"""

from . import estilo_graficos

# Import commonly used functions directly
from .estilo_graficos import (
    configurar_estilo_grafico,
    formatear_ejes,
    forzar_y_cero,
    UBA_FCE_COLORS,
)

__all__ = [
    'estilo_graficos',
    'configurar_estilo_grafico',
    'formatear_ejes',
    'forzar_y_cero',
    'UBA_FCE_COLORS',
]
