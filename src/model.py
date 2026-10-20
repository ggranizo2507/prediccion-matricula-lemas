"""
Definición de los modelos (nombre que pide la guía del curso).

Es un punto de entrada delgado: la implementación vive en `src/modeling.py` (modelos de
aprendizaje automático y su espacio de búsqueda) y en `src/reglas.py` (reglas D y D2, la
solución elegida). Se reexporta aquí para que quien busque `model.py` encuentre lo esencial
sin duplicar código.

    from src.model import construir_modelo, espacio_de, puntaje_d2
"""

from src.modeling import CONJUNTOS, NOMBRES, TIPOS, construir_modelo, distribuciones, espacio_de
from src.reglas import PESOS_D2, REGLA_D, REGLA_D2, puntaje_d, puntaje_d2, puntajes_reglas

__all__ = [
    "CONJUNTOS",
    "NOMBRES",
    "TIPOS",
    "construir_modelo",
    "distribuciones",
    "espacio_de",
    "PESOS_D2",
    "REGLA_D",
    "REGLA_D2",
    "puntaje_d",
    "puntaje_d2",
    "puntajes_reglas",
]
