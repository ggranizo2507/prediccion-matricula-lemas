"""
Reglas de priorización sin aprendizaje (Fase 1): D y D2.

Es la única definición de las reglas en el proyecto. La usan la auditoría (referencias en
C4), el modelado (selección y prueba final), los escenarios críticos, el alcance de la lista y
la aplicación. Las reglas solo usan datos conocidos en t0, así que Secretaría podría aplicarlas
a mano con el Excel.

- **D · más atrasos primero:** número de pensiones del ciclo de origen pagadas tarde.
- **D2 · señales administrativas:** prioridad lexicográfica. Primero el pago tardío de la
  matrícula anterior, luego la reserva extraordinaria y, dentro de cada grupo, los atrasos.
  Los pesos (100, 20 y 1) solo fijan ese orden: los atrasos van de 0 a 10, así que nunca
  superan a una reserva extraordinaria (20), y 20 + 10 nunca supera a un pago tardío (100).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

__all__ = [
    "REGLA_D",
    "REGLA_D2",
    "PESOS_D2",
    "senales",
    "puntaje_d",
    "puntaje_d2",
    "puntajes_reglas",
]

REGLA_D = "D · más atrasos primero"
REGLA_D2 = "D2 · señales administrativas"
# Orden de las señales de D2 (de la más fuerte a la más débil) y peso de cada una
PESOS_D2 = {"pago_tardio": 100, "reserva_extraordinaria": 20, "atrasos_pension": 1}


def senales(datos: pd.DataFrame) -> dict[str, np.ndarray]:
    """Las tres señales administrativas como números (vacíos = 0)."""
    return {
        "pago_tardio": (datos["pago_origen"] == "tardio").to_numpy().astype(float),
        "reserva_extraordinaria": pd.to_numeric(datos["reserva_extraordinaria"], errors="coerce")
        .fillna(0)
        .to_numpy(),
        "atrasos_pension": pd.to_numeric(datos["atrasos_pension"], errors="coerce")
        .fillna(0)
        .to_numpy(),
    }


def puntaje_d(datos: pd.DataFrame) -> np.ndarray:
    """Regla D: más pensiones pagadas tarde, más prioridad."""
    return senales(datos)["atrasos_pension"]


def puntaje_d2(datos: pd.DataFrame) -> np.ndarray:
    """Regla D2: suma ponderada que reproduce el orden lexicográfico de las señales."""
    valores = senales(datos)
    return sum(peso * valores[nombre] for nombre, peso in PESOS_D2.items())


def puntajes_reglas(datos: pd.DataFrame) -> dict[str, np.ndarray]:
    """Puntajes de D y D2 (más alto = más prioridad)."""
    return {REGLA_D: puntaje_d(datos), REGLA_D2: puntaje_d2(datos)}
