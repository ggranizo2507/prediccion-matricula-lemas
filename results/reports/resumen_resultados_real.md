# Resumen de resultados (real)

Generado por `tools/generar_resumen.py` a partir de `results/metrics/resultados_finales_real.json`. Solo agregados.

- Sistema elegido: **D2 · señales administrativas**
- Entrenamiento: C2 + C3 · selección: C4 · prueba única: C5
- k por sede: Mucho Lote 1: 118, Mucho Lote 2: 47
- Huella SHA-256 del sistema congelado: `ab86463689d57108188d1dedead2057e614777caed66a7aab84bc9b1b31d69d7`

## Selección en C4

| Candidato | Lift@k | Precision@k | Recall@k | PR-AUC |
|---|---|---|---|---|
| D2 · señales administrativas | 1,93 | 0,176 | 0,31 | 0,137 |
| D · más atrasos primero | 1,86 | 0,170 | 0,29 | 0,112 |
| Logística híbrida (señales de D2 + variables académicas) | 1,53 | 0,139 | 0,24 | 0,125 |
| Regresión logística regularizada | 1,40 | 0,127 | 0,22 | 0,113 |
| Gradient boosting (árboles, monotonía en atrasos) | 1,06 | 0,097 | 0,17 | 0,103 |

## Prueba final en C5 (una sola vez)

| Sistema | Lift@k [IC 95 %] | Precision@k | Recall@k |
|---|---|---|---|
| Logística híbrida (señales de D2 + variables académicas) | 0,98 [0,47; 1,52] | 0,067 | 0,15 |
| D · más atrasos primero | 1,70 [1,03; 2,30] | 0,115 | 0,26 |
| D2 · señales administrativas | 1,97 [1,24; 2,56] | 0,133 | 0,30 |
| A · selección al azar de k familias | 1,08 | 0,073 | 0,16 |

## Calibración y proyección (C5)

| Referencia | Brier |
|---|---|
| R · si reservó, continúa | 0,0695 |
| B0 · clase mayoritaria | 0,0695 |
| B1 · tasa histórica (0.076) | 0,0647 |
| Modelo calibrado · Logística híbrida (señales de D2 + variables académicas) | 0,0648 |

MAPE de la proyección por sede y subnivel: modelo 2,8 %, B1 2,8 %.

## Hiperparámetros del sistema congelado

- **logistica:** conjunto = completo, balanceado = False, C = 2,7450, l1_ratio = 0,8670
- **arboles:** conjunto = completo, balanceado = True, learning_rate = 0,0351, max_depth = 3, max_leaf_nodes = 6, min_samples_leaf = 101, l2_regularization = 4,2494, max_iter = 359
- **hibrido:** balanceado = True, C = 9,0132

## Comprobaciones de la revisión final (D59, cuaderno 08)

- Con C1–C3, las señales se ordenan así por riesgo relativo: pago tardío de la matrícula anterior > reserva extraordinaria > al menos una pensión pagada tarde; es el mismo orden de D2.
- Con C2–C3 (entrenamiento), las señales se ordenan así por riesgo relativo: pago tardío de la matrícula anterior > reserva extraordinaria > al menos una pensión pagada tarde; es el mismo orden de D2.
- Con C1, las señales se ordenan así por riesgo relativo: pago tardío de la matrícula anterior > al menos una pensión pagada tarde > reserva extraordinaria; es un orden distinto al de D2.
- Con C2, las señales se ordenan así por riesgo relativo: pago tardío de la matrícula anterior > al menos una pensión pagada tarde > reserva extraordinaria; es un orden distinto al de D2.
- Con C3 no se pueden comparar las tres señales: alguna tiene menos casos que el mínimo publicable.
- En C4, con 500 sorteos de desempate, el Lift@k de D2 tiene media 1,77 (percentiles 5 y 95: 1,60 y 1,93); la semilla oficial da 1,93, más que el 87 % de los sorteos.
- En C4, la diferencia de Lift@k D2 − D es 0,00 [IC 95 %: -0,62; 0,62]; D2 supera a D en el 47 % de las remuestras: no se puede afirmar que D2 sea mejor que D.
- El azar por estudiante da un Lift@k medio de 1,12 y el azar por familia, 1,00. Las familias con caso tienen 1,45 estudiantes en promedio, frente a 1,30 las demás.
