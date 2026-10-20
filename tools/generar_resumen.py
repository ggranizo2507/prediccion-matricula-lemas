"""
Reporte de resultados en Markdown, generado desde los agregados de `results/metrics`.

Escribe `results/reports/resumen_resultados_<fuente>.md` con la selección en C4, la prueba
final en C5, la calibración, la proyección y los hiperparámetros del sistema congelado. Si
existe `revision_<fuente>.json` (cuaderno 08), agrega las comprobaciones de la revisión final.
No lee datos individuales.

    python tools/generar_resumen.py --fuente real
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
METRICAS = RAIZ / "results" / "metrics"
REPORTES = RAIZ / "results" / "reports"


def _n(valor, decimales: int = 2) -> str:
    """Número con coma decimal; vacío si falta."""
    if valor is None or valor != valor:  # None o NaN
        return "—"
    return f"{float(valor):.{decimales}f}".replace(".", ",")


def _ic(par) -> str:
    return f" [{_n(par[0])}; {_n(par[1])}]" if par else ""


def generar(fuente: str) -> Path:
    """Arma el Markdown y lo guarda; devuelve la ruta."""
    datos = json.loads((METRICAS / f"resultados_finales_{fuente}.json").read_text(encoding="utf-8"))
    lineas = [
        f"# Resumen de resultados ({fuente})",
        "",
        "Generado por `tools/generar_resumen.py` a partir de `results/metrics/"
        f"resultados_finales_{fuente}.json`. Solo agregados.",
        "",
        f"- Sistema elegido: **{datos['priorizacion']}**",
        f"- Entrenamiento: {' + '.join(datos['cohortes_entrenamiento'])} · selección: C4 · "
        "prueba única: C5",
        f"- k por sede: {', '.join(f'{s}: {k}' for s, k in datos['k_por_sede'].items())}",
        f"- Huella SHA-256 del sistema congelado: `{datos['sha256_sistema']}`",
        "",
        "## Selección en C4",
        "",
        "| Candidato | Lift@k | Precision@k | Recall@k | PR-AUC |",
        "|---|---|---|---|---|",
    ]
    for fila in datos["C4"]:
        lineas.append(
            f"| {fila['candidato']} | {_n(fila['lift_k'])} | {_n(fila['precision_k'], 3)}"
            f" | {_n(fila['recall_k'])} | {_n(fila['pr_auc'], 3)} |"
        )
    lineas += [
        "",
        "## Prueba final en C5 (una sola vez)",
        "",
        "| Sistema | Lift@k [IC 95 %] | Precision@k | Recall@k |",
        "|---|---|---|---|",
    ]
    for fila in datos["C5"]:
        lineas.append(
            f"| {fila['sistema']} | {_n(fila['lift_k'])}{_ic(fila.get('ic95_lift_k'))}"
            f" | {_n(fila['precision_k'], 3)} | {_n(fila['recall_k'])} |"
        )
    lineas += ["", "## Calibración y proyección (C5)", "", "| Referencia | Brier |", "|---|---|"]
    lineas += [f"| {f['linea_base']} | {_n(f['brier'], 4)} |" for f in datos["brier_C5"]]
    mape = datos.get("mape_C5", {})
    if mape:
        lineas += [
            "",
            "MAPE de la proyección por sede y subnivel: modelo "
            f"{_n(100 * mape['modelo'], 1)} %, B1 {_n(100 * mape['B1'], 1)} %.",
        ]
    lineas += ["", "## Hiperparámetros del sistema congelado", ""]
    for tipo, params in datos["hiperparametros"].items():
        texto = ", ".join(
            f"{k} = {_n(v, 4) if isinstance(v, float) else v}" for k, v in params.items()
        )
        lineas.append(f"- **{tipo}:** {texto}")
    revision = METRICAS / f"revision_{fuente}.json"
    if revision.exists():
        rev = json.loads(revision.read_text(encoding="utf-8"))
        lineas += ["", "## Comprobaciones de la revisión final (D59, cuaderno 08)", ""]
        lineas += [f"- {t}" for t in rev["conclusiones"]]
    salida = REPORTES / f"resumen_resultados_{fuente}.md"
    salida.parent.mkdir(parents=True, exist_ok=True)
    salida.write_text("\n".join(lineas).rstrip() + "\n", encoding="utf-8")
    return salida


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--fuente", choices=["real", "sintetica"], default="real")
    args = parser.parse_args(argv)
    try:
        print("Reporte:", generar(args.fuente))
    except FileNotFoundError as error:
        print(f"Falta un archivo de resultados: {error.filename}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
