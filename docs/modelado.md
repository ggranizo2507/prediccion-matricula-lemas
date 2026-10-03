# Modelado y evaluación final · Fase 2

> **Estado: cerrada (01-oct-2026).** Datos reales de LEMAS, cuaderno `03_modelado`. Todas las cifras son agregados.
>
> Fuentes: `seleccion_C4_real.csv`, `diagnostico_ajuste_real.csv`, `shap_importancia_real.csv`, `permutacion_real.csv`, `resultados_finales_real.json`, `equidad_C5_real.csv`, `proyeccion_C5_real.csv` y figuras 9 a 12.

## 1. Protocolo

| Paso | Cohortes | Detalle |
|---|---|---|
| Entrenamiento | C2 + C3 | C1 excluida por la auditoría (Fase 1) |
| Optimización (Optuna, TPE, semilla 42) | C2 → C3 | 60 combinaciones por modelo; se maximiza la PR-AUC |
| Selección y calibración | C4 | Lift@k por representante frente a las reglas D y D2; calibración de Platt |
| Prueba final, una sola vez | C5 | Sistema congelado (SHA-256 registrado); IC 95 % con 2.000 réplicas bootstrap por representante |

**k por sede** (D32, el doble del promedio histórico): 118 representantes en Mucho Lote 1 y 47 en Mucho Lote 2. En total son 165 contactos, alrededor del 15 % de los 1.093 representantes de C5.

**Candidatos:**
- Regresión logística elastic-net.
- Gradient boosting con monotonía creciente en atrasos.
- Logística híbrida: señales de D2 más variables académicas. Se registró como **intento único** (D39) antes de verla en C4.

## 2. Selección en C4

| Candidato | Precision@k | Lift@k | Recall@k | PR-AUC | ROC-AUC |
|---|---|---|---|---|---|
| **D2 · señales administrativas** | **0,176** | **1,93** | **0,31** | **0,137** | **0,601** |
| D · más atrasos primero | 0,170 | 1,86 | 0,29 | 0,112 | 0,571 |
| Logística híbrida | 0,139 | 1,53 | 0,24 | 0,125 | 0,589 |
| Regresión logística regularizada | 0,127 | 1,40 | 0,22 | 0,113 | 0,534 |
| Gradient boosting | 0,097 | 1,06 | 0,17 | 0,103 | 0,540 |

**Diagnóstico de ajuste (actividad de la semana 3):**

| Modelo | PR-AUC entrenamiento | PR-AUC C4 | Brecha | Diagnóstico |
|---|---|---|---|---|
| Regresión logística | 0,140 | 0,113 | 0,026 | Subajuste: las señales son débiles |
| Gradient boosting | 0,245 | 0,103 | 0,141 | **Sobreajuste**: aprende particularidades de C2–C3 |
| Logística híbrida | 0,126 | 0,125 | 0,000 | Estable, pero con poca capacidad |

**Decisión (D40):** ningún modelo supera a D2, así que **la priorización final es la regla D2**. La logística híbrida calibrada se conserva para las probabilidades y la proyección.

## 3. Prueba final en C5 (una sola vez)

| Sistema | Precision@k [IC 95 %] | Lift@k [IC 95 %] | Recall@k [IC 95 %] | PR-AUC |
|---|---|---|---|---|
| **D2 · señales administrativas** | **0,133** [0,079; 0,182] | **1,97** [1,24; 2,56] | **0,30** [0,19; 0,39] | 0,097 |
| D · más atrasos primero | 0,115 [0,067; 0,164] | 1,70 [1,03; 2,30] | 0,26 [0,16; 0,35] | 0,094 |
| Logística híbrida (calibrada) | 0,067 [0,030; 0,103] | 0,98 [0,47; 1,52] | 0,15 [0,07; 0,23] | 0,088 |
| A · selección al azar de k familias | 0,073 | 1,08 | 0,16 | 0,074 |

- **D2 se confirma fuera de muestra.** Contactando al 15 % de los representantes se llega al **30 % de las familias que no se matricularán**, casi el doble que al azar. El IC de Lift@k no incluye el 1.
- **La logística híbrida no supera al azar en C5.** Esto confirma que la decisión tomada en C4 fue correcta.

**Calibración (Brier por estudiante en C5; menor es mejor):**

| Línea base | Brier |
|---|---|
| R · "si reservó, continúa" | 0,0695 |
| B0 · clase mayoritaria | 0,0695 |
| B1 · tasa histórica (0,076) | **0,0647** |
| Logística híbrida calibrada | 0,0648 |

El modelo calibrado da probabilidades correctas en promedio, pero **no mejora a B1**: el riesgo individual no se distingue de la tasa histórica.

## 4. Cumplimiento de los criterios del Canvas (C5)

| Criterio | Meta | Resultado | ¿Cumple? |
|---|---|---|---|
| Precision@k familiar mayor que la tasa base familiar | > 0,068 | 0,133 (D2) | ✅ |
| Lift@k | ≥ 1,20 | 1,97 [1,24; 2,56] (D2) | ✅ |
| AP mayor que la tasa base estudiantil | > 0,070 | 0,097 (D2) | ✅ |
| Brier menor que el predictor histórico (B1) | < 0,0647 | 0,0648 | ❌ (empate) |
| MAPE por sede y subnivel ≤ 15 % y mejor que B1 | ≤ 15 % y < B1 | 2,8 % frente a 2,8 % | ⚠️ cumple el umbral, no mejora a B1 |

## 5. Explicabilidad

- **Permutación (caída de PR-AUC en C4):** lo que más aporta al ordenamiento es la reserva extraordinaria (0,014), los atrasos en pensiones (0,011) y la puntualidad del pago anterior (0,008). Promedio y subnivel aportan muy poco; sede, beca, hermanos, años de permanencia y conducta no aportan nada.
- **SHAP (logística híbrida):** promedio, es_nuevo y subnivel mueven mucho la probabilidad, pero la permutación muestra que **no mejoran el orden**. Un efecto grande en la probabilidad no equivale a capacidad predictiva.
- **Conclusión:** la información útil está en el **comportamiento de pago y el tipo de reserva**, que es justo lo que resume D2.

## 6. Equidad de la priorización D2 en C5 (por representante)

| Grupo | Familias | Eventos | % seleccionadas | Precision@k | Recall@k |
|---|---|---|---|---|---|
| Mucho Lote 1 | 640 | 44 | 18,4 % | 0,12 | 0,32 |
| Mucho Lote 2 | 453 | 30 | 10,4 % | 0,17 | 0,27 |
| Sin beca | 930 | 63 | 15,9 % | 0,14 | 0,32 |
| Con beca | 163 | 11 | 10,4 % | 0,12 | **0,18** |
| Educación General Básica | 743 | 55 | 16,4 % | 0,12 | 0,27 |
| Inicial | 115 | 6 | 8,7 % | 0,20 | 0,33 |
| Preparatoria | 113 | 12 | 11,5 % | 0,38 | 0,42 |
| Bachillerato | 122 | <5 | 16,4 % | — | — |

- **Recall menor en familias becadas** (18 % frente a 32 %). Solo hay 11 eventos, así que la diferencia es incierta. Aun así, se recomienda que Secretaría revise también a las familias becadas con atrasos.
- **Diferencia entre sedes:** se explica porque k es menor en Mucho Lote 2 (47), proporcional a su historial.
- **Representante con cédula genérica:** no aparece en C5, así que la equidad de ese grupo no se pudo evaluar.

## 7. Conclusión de la Fase 2

1. **Resultado principal:** una regla de priorización derivada del análisis de datos (D2) duplica la efectividad del contacto frente al azar. Se validó fuera de muestra con IC 95 % y cumple las metas técnicas del Canvas.
2. **Resultado de los modelos:** con alrededor de 200 eventos de entrenamiento y señales débiles, los modelos de aprendizaje automático no superan a la regla. Es un resultado válido y previsto en el v5: la IA sirvió para descubrir, validar y cuantificar la regla, y para medir la incertidumbre de forma honesta.
3. **Para la app (Fase 3):** se usa D2 para la lista de contactos. Las probabilidades individuales se presentan como "tasa histórica ajustada", sin afirmar más precisión de la que tienen, y la proyección por sede y subnivel se acompaña de B1.
