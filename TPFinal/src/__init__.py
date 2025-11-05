"""
commodities_project - Base de Commodities UBA-FCE

Análisis de commodities y predictores macroeconómicos para el Trabajo Final
de la materia Taller de Programación - Universidad de Buenos Aires, FCE.

Estructura del paquete:
- data: Descarga y procesamiento de datos
- visualization: Gráficos con estilo institucional
- features: Feature engineering (futuro)
- models: Modelos predictivos (futuro)
- utils: Utilidades generales
"""

__version__ = '0.1.0'
__author__ = 'Grupo JLP'
__email__ = 'grupo@uba.edu.ar'

from . import data
from . import visualization
from . import config

__all__ = [
    'data',
    'visualization',
    'config',
    '__version__',
]
