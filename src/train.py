"""
Entrenamiento y selección en C4 desde la línea de comandos (nombre que pide la guía).

Repite los pasos de entrenamiento del cuaderno 03 sin abrir C5: construye la tabla de
modelado, optimiza con Optuna cada modelo (C2 → C3, espacio en `config.yaml`), reentrena con
las cohortes de entrenamiento y compara en C4 con las reglas D y D2. No guarda modelos: el
sistema que se congela y se prueba en C5 sale del cuaderno 03.

    python -m src.train                      # base sintética, pruebas de config.yaml
    python -m src.train --trials 5           # prueba rápida
    python -m src.train --fuente real        # solo en el entorno autorizado de LEMAS
"""

from __future__ import annotations

import argparse
import json
import logging

import pandas as pd

from src.data_processing import construir_dataset, limpiar_base
from src.modeling import diagnostico_ajuste, entrenar_candidatos, tabla_seleccion
from src.utils import RAIZ, cargar_config, configurar_logging

log = logging.getLogger("lemas.entrenamiento")


def main(argv: list[str] | None = None) -> int:
    """Entrena los candidatos, imprime la tabla de selección en C4 y el diagnóstico de ajuste."""
    configurar_logging()
    config = cargar_config()
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--fuente", choices=["real", "sintetica"], default="sintetica")
    parser.add_argument("--trials", type=int, default=None,
                        help="pruebas de Optuna por modelo (por defecto, config.yaml)")
    parser.add_argument("--salida", default=None, help="CSV donde guardar la tabla de selección")
    args = parser.parse_args(argv)

    ruta = RAIZ / config["rutas"]["base_real" if args.fuente == "real" else "base_sintetica"]
    if not ruta.exists():
        log.error("No existe la base %s. La base real solo está en el equipo de LEMAS.", ruta)
        return 1
    dataset, _ = construir_dataset(limpiar_base(pd.read_csv(ruta, dtype=str), config), config)
    decision = RAIZ / config["rutas"]["metricas"] / f"decision_c1_{args.fuente}.json"
    try:
        datos_decision = json.loads(decision.read_text(encoding="utf-8"))
    except FileNotFoundError:
        log.error("Falta %s: ejecute antes el cuaderno 02 (decisión sobre C1).", decision)
        return 1
    clave = "con_C1" if datos_decision["incluir_C1"] else "sin_C1"
    cohortes = config["auditoria"]["configuraciones_entrenamiento"][clave]
    k = datos_decision["k_por_sede"]
    log.info("Fuente: %s | entrenamiento: %s | k por sede: %s | C5 no se usa", args.fuente,
             "+".join(cohortes), k)

    candidatos = entrenar_candidatos(dataset, config, cohortes, k, n_trials=args.trials)
    tabla = tabla_seleccion(candidatos, dataset, k, config["proyecto"]["semilla"])
    print(tabla.round(4).to_string(index=False))
    print()
    print(diagnostico_ajuste(candidatos).to_string(index=False))
    if args.salida:
        tabla.to_csv(args.salida, index=False)
        log.info("Tabla de selección: %s", args.salida)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
