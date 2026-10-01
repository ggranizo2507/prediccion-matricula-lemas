# Análisis de datos · Fase 1

> **Estado: cierre de la Fase 1 (01-oct-2026).** Cifras de la segunda ejecución con datos reales de LEMAS, ya con las correcciones D27–D29 y k duplicado (D32). Fuentes: `perfil_lemas.json`, figuras `real_*`, `reporte_6_3_real.csv`, `decision_c1_real.json`, `referencias_C4_real.csv` y `sensibilidad_real.csv`.
>
> Todo lo que aparece aquí son **agregados**. Los grupos con menos de 5 casos se muestran como `<5`.

## 1. Fuente y volumen

| Concepto | Valor |
|---|---|
| Hojas (ciclos lectivos) | 6: de 2021–2022 a 2026–2027 |
| Filas (estudiante × ciclo) | 9.031 |
| Estudiantes distintos (seudónimo de cédula) | 2.733 |
| Representantes distintos | 2.017 |
| Filas por ciclo | 1.299 · 1.484 · 1.513 · 1.581 · 1.572 · 1.582 |

- **Sedes:** Mucho Lote 1 tiene el 62 % de las filas y Mucho Lote 2 el 38 %. La composición cambia con los años: Mucho Lote 2 pasa de 334 a 726 estudiantes (2021 → 2026) y Mucho Lote 1 baja de 965 a 856.
- **Hoja 2026–2027:** solo aporta `fecha_pago`, porque el ciclo está en curso. Sirve únicamente como destino de C5, así que es normal que tenga vacías las notas, la reserva y los atrasos (17,5 % de nulos en esas columnas).

## 2. Calidad de los datos

| Hallazgo | Tratamiento |
|---|---|
| `anoa` se llama `anoaa` en las hojas 2022–2026, y `Fecha Reserva` se llama `Fecha` en las hojas 2022–2025 | Se unifican al leer (`alias_columnas`, D26). El Excel ya se corrigió |
| `fecha_pago` vacía en el 0,13 % de las filas | Se trata como "sin pago" en el destino |
| `P.Conducta` con el valor "-" en menos de 5 casos | Queda vacía y se imputa en el preprocesamiento |
| 88 textos de `Nivel` con dos formatos ("Segundo Grado EGB" frente a "Segundo Grado"; "Tercer Curso" frente a "Tercero de bachillerato") | Se normaliza el curso (D27) |
| Un representante figura con 39 estudiantes en un mismo año | Se trata como representante atípico (D29) |
| `anio_ingreso` vacío en el 0,01 % | Años de permanencia vacíos, que se imputan |

## 3. Población modelable y eventos (tabla 6.3 del v5)

| Cohorte | N elegibles | Matrículas | No matrículas | q | Familias | Familias con no matrícula | q familiar | Exclusiones | Comparable |
|---|---|---|---|---|---|---|---|---|---|
| C1 | 1.035 | 920 | 115 | 11,1 % | 797 | 102 | 12,8 % | 263 | No |
| C2 | 1.236 | 1.124 | 112 | 9,1 % | 948 | 96 | 10,1 % | 247 | Sí |
| C3 | 1.305 | 1.224 | 81 | 6,2 % | 996 | 69 | 6,9 % | 208 | Sí |
| C4 | 1.374 | 1.252 | 122 | 8,9 % | 1.042 | 95 | 9,1 % | 205 | Sí |
| C5 | 1.411 | 1.313 | 98 | 6,9 % | 1.093 | 74 | 6,8 % | 161 | Sí |

- **Suficiencia:** todas las cohortes superan el mínimo de 30 eventos (D18). El evento es minoritario: la tasa global es de 8,3 %, así que hay desbalance de clases.
- **Efecto de D29:** solo cambia C2 (ciclo 2022), que gana 12 contactos al separar a los estudiantes de la cédula genérica. Las demás cohortes no cambian. D28 tampoco modificó los elegibles: los estudiantes de "Tercer Curso" no tenían reserva aprobada.
- **Variación:** la tasa cambia entre años sin una tendencia clara (de 6,2 % a 11,1 %). Esto hace que la tasa base de C5 sea distinta de la del entrenamiento.

## 4. Validación del calendario (t0 = 20-feb, H = 30-abr)

Entre 2023 y 2026, el 99 % de los estudiantes **antiguos** pagó la matrícula dentro de la ventana [t0, H]. En 2022 la proporción fue del 95 %, con 50 pagos tardíos. Los pagos de antiguos antes de t0 son menos de 5 por año. Esto respalda el corte t0 = 20-feb (D01).

Los **nuevos** pagan sobre todo antes de t0 (entre 107 y 125 por año). No forman parte de la población del modelo como destino, pero sí como origen, con `pago_origen = nuevo`.

## 5. Señales univariadas (Figuras 3 a 6)

| Variable | Grupo con más riesgo | Grupo de referencia | Lectura |
|---|---|---|---|
| Pago de la matrícula anterior | Tardío: ≈ 24 % (n = 88) | En plazo: ≈ 7,6 % | **La señal más fuerte**, aunque afecta a pocos casos |
| Pensiones pagadas tarde (`# meses caído`) | 4–5 atrasos: ≈ 14–16 % | 0 atrasos: ≈ 7 % | Crece de forma casi lineal de 0 a 5 y no es lineal desde 6 |
| Reserva extraordinaria | ≈ 12,7 % | Ordinaria: ≈ 7,6 % | Señal moderada |
| Subnivel | Preparatoria: ≈ 11,4 % | Bachillerato: ≈ 6,3 % | Las transiciones tempranas tienen más riesgo |
| Conducta | B: ≈ 11,3 % | A: ≈ 8,1 % | Varía poco: el 94 % de las notas son A |
| Hermanos en LEMAS | 3 o más: ≈ 10 % (n = 48) | 1 hermano: ≈ 7,6 % | Diferencia pequeña; antes de D29 aparecía un falso "38 hermanos" con 92 % |
| Sede, beca, promedio, años de permanencia | Sin diferencia relevante | — | Aportan poco solas; pueden ayudar combinadas con otras |

Las correlaciones de Spearman con el resultado son débiles (|ρ| ≤ 0,07). Ninguna variable separa los casos por sí sola, así que se espera una discriminación modesta.

## 6. Comparabilidad de C1 y decisión

- **Diferencias estandarizadas (Figura 8):** al normalizar los cursos, las diferencias por nombre de curso desaparecen. Quedan cinco diferencias reales que superan el umbral de 0,20: promedio (SMD ≈ +0,24; C1 tiene notas más altas), proporción de nuevos (≈ −0,23), sede (≈ ±0,22) y conducta (≈ +0,21).
- **Prueba en C4 con la regresión logística base y k duplicado:** con C1 (C1+C2+C3), Precision@k = 0,112; sin C1 (C2+C3), 0,139. La diferencia es de −0,027, mayor que la tolerancia de 0,02.
- **Decisión (regla D14): C1 se excluye del entrenamiento.** Se entrena con C2+C3, se selecciona con C4 y se prueba con C5.
- **Robustez:** el IC 95 % por bootstrap de la diferencia es [−0,061; +0,012] (2.000 réplicas). Incluye el 0, así que la evidencia contra C1 es débil, aunque la dirección es estable en las dos ejecuciones. Se aplica la regla registrada de antemano. En la Fase 2 se reportará, como análisis de sensibilidad, el modelo final entrenado también con C1.

## 7. Problemas detectados y corregidos

| # | Problema | Efecto | Corrección |
|---|---|---|---|
| D27 | Dos formatos de curso | Infla las diferencias de C1 y fragmenta las categorías del modelo | `normalizar_curso`: se quita "EGB" y "Primer/Segundo/Tercer Curso" pasa a "… de bachillerato" |
| D28 | "Tercer Curso – Bachillerato" no se reconocía como último curso | Riesgo de contar a los graduados como no matrícula. En estos datos no hubo efecto, porque esos estudiantes no tenían reserva aprobada | La regla de curso terminal se aplica al nivel y al curso normalizado |
| D29 | Un representante con 39 estudiantes: es una **cédula genérica** que se usa para familias extranjeras sin cédula ecuatoriana (D33) | En la Figura 4, el grupo "38 hermanos" tiene un 92 % de no matrícula; distorsiona hermanos y k | Con más de 6 estudiantes por año, cada estudiante cuenta como su propio contacto y se reporta como `representante_atipico`. Esa marca no es predictor, porque equivaldría a usar la nacionalidad; en la Fase 2 se revisará la equidad para este grupo |

## 8. Referencias en C4 y capacidad

Todas se evalúan en C4, con el mismo k por sede y la misma consolidación por representante. C5 no se usó.

| Referencia | Precision@k | Lift@k | Recall@k | PR-AUC |
|---|---|---|---|---|
| R · selección al azar | 0,103 | 1,13 | 0,18 | 0,089 |
| D · más atrasos primero | 0,170 | 1,86 | 0,29 | 0,112 |
| **D2 · señales administrativas** (pago anterior tardío → reserva extraordinaria → atrasos) | **0,176** | **1,93** | **0,31** | **0,137** |
| B1 · regresión logística balanceada (C2+C3) | 0,139 | 1,53 | 0,24 | 0,119 |

- **Hallazgo clave:** las reglas simples D y D2 **superan** a la regresión logística con todas las variables, que discrimina poco (ROC-AUC ≈ 0,54). Con 193 eventos en el entrenamiento y muchas categorías de curso, el modelo completo tiende a sobreajustar. En la ejecución anterior su ROC-AUC llegaba a 0,59, pero se apoyaba en el falso grupo de 38 hermanos, que D29 eliminó.
- **Meta para la Fase 2:** el modelo optimizado debe superar a **D2** (Lift@k ≈ 1,93, Recall@k ≈ 0,31) en C4. Si no lo logra, se recomendará la regla D2 como solución operativa, y eso también es un resultado válido del proyecto.
- **k por sede (D32, el doble del promedio histórico):** Mucho Lote 1 = 118 y Mucho Lote 2 = 47 representantes. Equivale a unos 2,0 y 1,2 contactos por persona y por semana en 10 semanas, lo que es viable con 6 y 4 personas.

## 9. Sensibilidad: solo reservas en estado "Aprobar"

| Cohorte | Elegibles (principal) | Elegibles (solo Aprobar) | Tasa principal | Tasa solo Aprobar |
|---|---|---|---|---|
| C1 | 1.035 | 830 | 11,1 % | 10,5 % |
| C2 | 1.236 | 1.046 | 9,1 % | 8,8 % |
| C3 | 1.305 | 1.289 | 6,2 % | 5,9 % |
| C4 | 1.374 | 1.196 | 8,9 % | 7,8 % |
| C5 | 1.411 | 1.375 | 7,0 % | 6,8 % |

Excluir las aprobaciones extraordinarias reduce la tasa entre 0,2 y 1,1 puntos. La conclusión no cambia: las aprobaciones que pudieron ser tardías no distorsionan la etiqueta. Se mantiene la población principal (D08).

## 10. Implicaciones para la Fase 2

1. Reducir la dimensión: agrupar `curso` en subnivel o eliminarlo, regularizar con L1/L2 y comparar con gradient boosting con restricciones de monotonía en atrasos. **La meta es superar a D2.**
2. Tratar `atrasos_pension` con una forma no lineal (por tramos), como sugiere la Figura 4.
3. Calibrar las probabilidades (Platt o isotónica) en C4 antes de evaluar en C5.
4. Medir la equidad por sede y por beca (Fairlearn), dada la poca diferencia de tasas entre esos grupos.
5. Conducta: el ciclo 2022 tiene un 18 % de notas B, frente a 2–3 % en los demás años. El equipo confirmó que la conversión es correcta (D34). Como la variable varía poco, se evaluará también como indicador "A / no A".
6. Equidad: revisar el desempeño del modelo para los estudiantes con representante de cédula genérica (familias extranjeras), sin usar esa marca como predictor.
