"""
Intervalos y pruebas de equidad, carga operativa y tamaño de la reserva al azar (D60).

Lee solo agregados ya publicados y guarda:

- `results/metrics/equidad_ic_<fuente>.csv`: conteos, % seleccionadas y Recall@k por grupo
  con IC de Wilson,
- `results/metrics/equidad_comparaciones_<fuente>.csv`: prueba exacta de Fisher y razón de
  selección con IC frente al grupo de referencia,
- `results/metrics/reserva_potencia_<fuente>.csv`: familias y campañas necesarias para medir
  el efecto de la llamada,
- `results/metrics/incertidumbre_<fuente>.json`: carga operativa y conclusiones.

    python tools/generar_incertidumbre.py --fuente real
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

import pandas as pd  # noqa: E402

from src import incertidumbre as inc  # noqa: E402

METRICAS = RAIZ / "results" / "metrics"
REFERENCIAS = {"beca": "0", "sede": "Mucho Lote 1", "subnivel": "Educación General Básica"}
REGLA = "D2 · señales administrativas"


def generar(fuente: str) -> dict:
    equidad = pd.read_csv(METRICAS / f"equidad_C5_{fuente}.csv", dtype={"grupo": str})
    finales = json.loads((METRICAS / f"resultados_finales_{fuente}.json").read_text("utf-8"))
    con_ic = inc.equidad_con_ic(equidad[equidad["variable"].isin(REFERENCIAS)])
    comparado = inc.comparaciones(con_ic, REFERENCIAS)
    total = equidad[equidad["variable"] == "beca"]
    familias, eventos = int(total["familias"].sum()), int(pd.to_numeric(total["eventos"]).sum())
    d2 = next(f for f in finales["C5"] if f["sistema"] == REGLA)
    k_total = int(sum(finales["k_por_sede"].values()))
    hallados = int(round(d2["recall_k"] * eventos))
    carga = inc.llamadas_por_caso(k_total, hallados, eventos / familias)
    reserva = inc.tabla_reserva(float(d2["precision_k"]), k_total)
    con_ic.to_csv(METRICAS / f"equidad_ic_{fuente}.csv", index=False)
    comparado.to_csv(METRICAS / f"equidad_comparaciones_{fuente}.csv", index=False)
    reserva.to_csv(METRICAS / f"reserva_potencia_{fuente}.csv", index=False)
    resumen = {
        "fuente": fuente,
        "cohorte": "C5",
        "regla": REGLA,
        "familias": familias,
        "familias_con_caso": eventos,
        "carga_operativa": carga,
        "supuestos_reserva": {
            "tasa_sin_llamar": d2["precision_k"],
            "alfa": 0.05,
            "potencia": 0.80,
            "familias_por_campana": k_total,
        },
        "conclusiones": inc.conclusiones(con_ic, comparado, carga, reserva),
    }
    (METRICAS / f"incertidumbre_{fuente}.json").write_text(
        json.dumps(resumen, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return resumen


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--fuente", choices=["real", "sintetica"], default="real")
    for texto in generar(parser.parse_args().fuente)["conclusiones"]:
        print("-", texto)


if __name__ == "__main__":
    main()
