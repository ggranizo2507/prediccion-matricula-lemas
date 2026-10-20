# Resumen de resultados (sintetica)

Generado por `tools/generar_resumen.py` a partir de `results/metrics/resultados_finales_sintetica.json`. Solo agregados.

- Sistema elegido: **Logística híbrida (señales de D2 + variables académicas)**
- Entrenamiento: C1 + C2 + C3 · selección: C4 · prueba única: C5
- k por sede: Mucho Lote 1: 113, Mucho Lote 2: 75
- Huella SHA-256 del sistema congelado: `a2fd6d089c5ff84d373b3889398f9ba4ae5437a3ded793632873234c413dce88`

## Selección en C4

| Candidato | Lift@k | Precision@k | Recall@k | PR-AUC |
|---|---|---|---|---|
| Logística híbrida (señales de D2 + variables académicas) | 1,51 | 0,144 | 0,28 | 0,143 |
| D · más atrasos primero | 1,46 | 0,138 | 0,27 | 0,135 |
| Gradient boosting (árboles, monotonía en atrasos) | 1,40 | 0,133 | 0,26 | 0,180 |
| Regresión logística regularizada | 1,34 | 0,128 | 0,24 | 0,163 |
| D2 · señales administrativas | 1,06 | 0,101 | 0,19 | 0,095 |

## Prueba final en C5 (una sola vez)

| Sistema | Lift@k [IC 95 %] | Precision@k | Recall@k |
|---|---|---|---|
| Logística híbrida (señales de D2 + variables académicas) | 1,73 [1,16; 2,23] | 0,138 | 0,30 |
| D · más atrasos primero | 1,26 [0,85; 1,84] | 0,101 | 0,22 |
| D2 · señales administrativas | 1,26 [0,80; 1,80] | 0,101 | 0,22 |
| A · selección al azar de k familias | 1,03 | 0,083 | 0,18 |

## Calibración y proyección (C5)

| Referencia | Brier |
|---|---|
| R · si reservó, continúa | 0,0746 |
| B0 · clase mayoritaria | 0,0746 |
| B1 · tasa histórica (0.086) | 0,0691 |
| Modelo calibrado · Logística híbrida (señales de D2 + variables académicas) | 0,0688 |

MAPE de la proyección por sede y subnivel: modelo 1,2 %, B1 1,2 %.

## Hiperparámetros del sistema congelado

- **logistica:** balanceado = False, conjunto = completo, C = 0,0231, l1_ratio = 0,6813
- **arboles:** balanceado = False, conjunto = completo, learning_rate = 0,0173, max_depth = 2, max_leaf_nodes = 15, min_samples_leaf = 21, l2_regularization = 0,1071, max_iter = 186
- **hibrido:** balanceado = False, C = 0,0014

## Comprobaciones de la revisión final (D59, cuaderno 08)

- Con C1–C3, las señales se ordenan así por riesgo relativo: al menos una pensión pagada tarde > pago tardío de la matrícula anterior > reserva extraordinaria; es un orden distinto al de D2.
- Con C2–C3 (entrenamiento), las señales se ordenan así por riesgo relativo: al menos una pensión pagada tarde > reserva extraordinaria > pago tardío de la matrícula anterior; es un orden distinto al de D2.
- Con C1 no se pueden comparar las tres señales: alguna tiene menos casos que el mínimo publicable.
- Con C2 no se pueden comparar las tres señales: alguna tiene menos casos que el mínimo publicable.
- Con C3 no se pueden comparar las tres señales: alguna tiene menos casos que el mínimo publicable.
- En C4, con 500 sorteos de desempate, el Lift@k de D2 tiene media 1,08 (percentiles 5 y 95: 0,95 y 1,18); la semilla oficial da 1,06, más que el 24 % de los sorteos.
- En C4, la diferencia de Lift@k D2 − D es -0,33 [IC 95 %: -0,90; 0,22]; D2 supera a D en el 10 % de las remuestras: no se puede afirmar que D2 sea mejor que D.
- El azar por estudiante da un Lift@k medio de 1,02 y el azar por familia, 0,99. Las familias con caso tienen 1,12 estudiantes en promedio, frente a 1,10 las demás.
