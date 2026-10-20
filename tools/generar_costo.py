"""
Análisis de costo esperado de la lista de contactos (D56).

Lee solo tablas agregadas ya publicadas en `results/metrics`:

- `alcance_por_k_<fuente>.csv` (cohortes C2–C4, cuaderno 06),
- `alcance_semanal_<fuente>.csv` (familias pendientes por semana, C2–C4),
- `resultados_finales_<fuente>.json` (precisión de D2 en la prueba C5, ya publicada).

y guarda:

- `results/metrics/costo_equilibrio_<fuente>.csv`: razón de equilibrio por escenario,
- `results/metrics/costo_marginal_<fuente>.csv`: precisión y equilibrio de cada tramo,
- `results/metrics/costo_beneficio_<fuente>.csv`: beneficio neto por tamaño de lista,
- `results/metrics/costo_<fuente>.json`: supuestos, mejor tamaño y conclusiones,
- `results/figures/<fuente>_28_costo_esperado.png`.

No usa datos individuales ni vuelve a evaluar en C5: es aritmética sobre conteos publicados.

    python tools/generar_costo.py --fuente real
    python tools/generar_costo.py --fuente sintetica
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

import pandas as pd  # noqa: E402

from src import costo  # noqa: E402
from src.graficos_costo import figura_costo, guardar  # noqa: E402

METRICAS = RAIZ / "results" / "metrics"
FIGURAS = RAIZ / "results" / "figures"


def _c5(fuente: str) -> dict | None:
    ruta = METRICAS / f"resultados_finales_{fuente}.json"
    if not ruta.exists():
        return None
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    for fila in datos.get("C5", []):
        if str(fila.get("sistema", "")).startswith("D2"):
            return fila
    return None


def generar(fuente: str, cohorte: str = "C4", semana: int = 5) -> dict:
    por_k = pd.read_csv(METRICAS / f"alcance_por_k_{fuente}.csv")
    ruta_semanal = METRICAS / f"alcance_semanal_{fuente}.csv"
    semanal = pd.read_csv(ruta_semanal) if ruta_semanal.exists() else None
    c5 = _c5(fuente)

    equilibrio = costo.tabla_equilibrio(costo.escenarios(por_k, semanal, c5, cohorte, semana))
    marg = costo.marginales(por_k, cohorte)
    marg_todas = costo.marginales(por_k, costo.TODAS)
    curva = costo.curva_beneficio(por_k, cohorte)
    mejor = costo.mejor_tamano(curva)
    textos = costo.conclusiones(equilibrio, marg, mejor)

    equilibrio.to_csv(METRICAS / f"costo_equilibrio_{fuente}.csv", index=False)
    pd.concat([marg, marg_todas]).to_csv(METRICAS / f"costo_marginal_{fuente}.csv", index=False)
    curva.to_csv(METRICAS / f"costo_beneficio_{fuente}.csv", index=False)
    resumen = {
        "fuente": fuente,
        "cohorte": cohorte,
        "semana_segunda_llamada": semana,
        "supuestos": {
            "eficacias": list(costo.EFICACIAS),
            "razones_cFN_cFP": list(costo.RAZONES),
            "unidad": "llamadas (cFP = 1)",
        },
        "mejor_tamano": mejor.to_dict(orient="records"),
        "conclusiones": textos,
    }
    (METRICAS / f"costo_{fuente}.json").write_text(
        json.dumps(resumen, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    guardar(figura_costo(equilibrio, curva, cohorte), FIGURAS / f"{fuente}_28_costo_esperado.png")
    return resumen


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--fuente", choices=["real", "sintetica"], default="sintetica")
    parser.add_argument("--cohorte", default="C4")
    parser.add_argument("--semana", type=int, default=5)
    args = parser.parse_args()
    resumen = generar(args.fuente, args.cohorte, args.semana)
    for texto in resumen["conclusiones"]:
        print("-", texto)


if __name__ == "__main__":
    main()
