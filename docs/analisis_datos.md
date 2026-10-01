# Análisis de datos · Fase 1

> **Estado: preliminar (30-sep-2026).** Las cifras salen de la primera ejecución con datos reales de LEMAS (`perfil_lemas.json`, figuras `real_*`, `reporte_6_3_real.csv` y `decision_c1_real.json`). Esa ejecución reveló tres problemas de datos (sección 7), ya corregidos en el código (D27–D29). Las secciones 3, 6 y 8 se actualizarán al volver a ejecutar los cuadernos 01 y 02.
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

## 3. Población modelable y eventos (tabla 6.3 del v5, preliminar)

| Cohorte | N elegibles | Matrículas | No matrículas | q | Familias | Familias con no matrícula | q familiar | Exclusiones | Comparable |
|---|---|---|---|---|---|---|---|---|---|
| C1 | 1.035 | 920 | 115 | 11,1 % | 797 | 102 | 12,8 % | 263 | No |
| C2 | 1.236 | 1.124 | 112 | 9,1 % | 936 | 85 | 9,1 % | 247 | Sí |
| C3 | 1.305 | 1.224 | 81 | 6,2 % | 996 | 69 | 6,9 % | 208 | Sí |
| C4 | 1.374 | 1.252 | 122 | 8,9 % | 1.042 | 95 | 9,1 % | 205 | Sí |
| C5 | 1.411 | 1.313 | 98 | 6,9 % | 1.093 | 74 | 6,8 % | 161 | Sí |

- **Suficiencia:** todas las cohortes superan el mínimo de 30 eventos (D18). El evento es minoritario: la tasa global es de 8,3 %, así que hay desbalance de clases.
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
| Sede, beca, promedio, años de permanencia | Sin diferencia relevante | — | Aportan poco solas; pueden ayudar combinadas con otras |

Las correlaciones de Spearman con el resultado son débiles (|ρ| ≤ 0,07). Ninguna variable separa los casos por sí sola, así que se espera una discriminación modesta.

## 6. Comparabilidad de C1 (preliminar)

- **Diferencias estandarizadas (Figura 8):** las mayores diferencias aparecen en categorías de `curso` como "Tercer Grado" frente a "Tercer Grado EGB". Son en buena parte un **efecto del cambio de nombre** de los cursos, no de la población. Las diferencias reales son el promedio (SMD ≈ +0,24), la composición por sede (≈ ±0,22) y la proporción de nuevos (≈ −0,23).
- **Prueba en C4 con la regresión logística base:** con C1 (C1+C2+C3), Precision@k = 0,176; sin C1 (C2+C3), 0,211. La diferencia es de −0,034, mayor que la tolerancia de 0,02, así que **C1 se excluye de forma preliminar**.
- **Cautela:** con k = 76 representantes, esa diferencia equivale a unos 3 aciertos. Se volverá a calcular con los cursos normalizados y con un intervalo de confianza por bootstrap (nuevo en el cuaderno 02). La regla de decisión no cambia.

## 7. Problemas detectados y corregidos

| # | Problema | Efecto | Corrección |
|---|---|---|---|
| D27 | Dos formatos de curso | Infla las diferencias de C1 y fragmenta las categorías del modelo | `normalizar_curso`: se quita "EGB" y "Primer/Segundo/Tercer Curso" pasa a "… de bachillerato" |
| D28 | "Tercer Curso – Bachillerato" no se reconocía como último curso | Los graduados de ese formato podían contar como no matrícula | La regla de curso terminal se aplica al nivel y al curso normalizado |
| D29 | Un representante con 39 estudiantes: es una **cédula genérica** que se usa para familias extranjeras sin cédula ecuatoriana (D33) | En la Figura 4, el grupo "38 hermanos" tiene un 92 % de no matrícula; distorsiona hermanos y k | Con más de 6 estudiantes por año, cada estudiante cuenta como su propio contacto y se reporta como `representante_atipico`. Esa marca no es predictor, porque equivaldría a usar la nacionalidad; en la Fase 2 se revisará la equidad para este grupo |

## 8. Referencias y capacidad (preliminar)

- **Regresión logística base en C4:** ROC-AUC entre 0,57 y 0,59 y PR-AUC entre 0,13 y 0,14, frente a una tasa base de alrededor de 0,09. **Lift@k entre 1,9 y 2,3**: en la lista priorizada hay unas 2 veces más casos que al azar. El Brier (≈ 0,25) es alto porque el modelo balanceado no está calibrado; la calibración se hace en la Fase 2.
- **Referencias R, D, D2 y B1:** se agregaron al cuaderno 02 (`referencias_C4_real.csv`). En la Fase 2, el modelo debe superar a las reglas D y D2.
- **k por sede (regla D06):** Mucho Lote 1 = 54 y Mucho Lote 2 = 22 representantes. Con el personal disponible equivale a 0,9 y 0,55 contactos por persona y por semana en 10 semanas. **La capacidad real es mucho mayor que k.** El equipo decidió **duplicar k** (D32): con los datos preliminares quedaría en ≈ 108 y ≈ 44. Esto aumenta el recall a costa de la precisión.

## 9. Implicaciones para la Fase 2

1. Usar modelos regularizados y simples, y comparar con métodos de árboles (gradient boosting) usando restricciones de monotonía en atrasos.
2. Tratar `atrasos_pension` con una forma no lineal (por tramos), como sugiere la Figura 4.
3. Calibrar las probabilidades (Platt o isotónica) en C4 antes de evaluar en C5.
4. Medir la equidad por sede y por beca (Fairlearn), dada la poca diferencia de tasas entre esos grupos.
5. Conducta: el ciclo 2022 tiene un 18 % de notas B, frente a 2–3 % en los demás años. El equipo confirmó que la conversión es correcta (D34). Como la variable varía poco, se evaluará también como indicador "A / no A".
6. Equidad: revisar el desempeño del modelo para los estudiantes con representante de cédula genérica (familias extranjeras), sin usar esa marca como predictor.
