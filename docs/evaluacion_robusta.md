# Evaluación robusta: validación, incertidumbre y comparación de sistemas

Este documento explica cómo validamos los modelos y por qué no usamos la validación cruzada aleatoria. También dice qué técnicas de evaluación robusta aplicamos, cuáles no y por qué. No contiene resultados nuevos: describe el método con el que se obtuvieron los que ya están en [modelado.md](modelado.md), [optimizacion.md](optimizacion.md), [alcance_lista.md](alcance_lista.md) y el [reporte de diagnóstico](diagnostic_report.pdf). La decisión de documentarlo está registrada como D55 en [planificacion.md](planificacion.md).

## 1. Por qué validación temporal y no validación cruzada aleatoria

El sistema se usa cada 20 de febrero para ordenar las llamadas del ciclo siguiente. Un pliegue al azar mezcla estudiantes de distintos años: el modelo aprendería, por ejemplo, de 2025 para predecir 2023. Esa mezcla filtra información del futuro y da un resultado optimista, sobre todo cuando la tasa de no matrícula cambia de un año a otro (del 6,2 % al 11,1 % según la cohorte, [analisis_datos.md](analisis_datos.md)).

Por eso todas las particiones respetan el orden del tiempo: se entrena con cohortes anteriores y se valida con una posterior.

| Partición | Entrena con | Valida con | Estudiantes (eventos) en la validación | Uso |
|---|---|---|---|---|
| Interna | C2 | C3 | 1.305 (81) | Optuna elige los hiperparámetros (60 combinaciones por modelo); se fija la parada temprana |
| Selección | C2 + C3 | C4 | 1.374 (122) | Comparar modelos con las reglas, elegir el sistema y calibrar |
| Prueba final | C2 + C3 | C5 | 1.411 (98); 1.093 familias (74) | Medir una sola vez el sistema congelado |

C1 quedó fuera por la auditoría de comparabilidad de la Fase 1. Las cohortes son años lectivos: el corte natural del problema. En términos de la literatura es una **validación temporal de origen móvil con un conjunto de prueba reservado**. C5 se evaluó una sola vez, con el sistema congelado y su huella SHA-256 registrada (D38, D41).

**La unidad es la familia.** Un mismo estudiante aparece en varias cohortes (por ejemplo, en C3 para entrenar y en C4 para validar). Es intencional: así se usará el sistema, para predecir el año siguiente de estudiantes que ya están en el colegio. Lo que sí se agrupa es la familia: los hermanos de una cohorte se consolidan en un solo contacto (`evaluate.consolidar_familias`) y entran o salen juntos en cada réplica bootstrap.

## 2. Qué técnicas aplicamos

| Técnica | Estado | Qué hicimos | Dónde |
|---|---|---|---|
| **Stratified k-fold repetido** | No aplica | Los pliegues al azar mezclan años (sección 1) | — |
| **GroupKFold** | Aplicada la idea | El grupo es la familia: evaluación por familia y bootstrap que remuestrea familias completas | `src/evaluate.py`, `src/modeling.bootstrap_ic`, `src/diagnostico.bootstrap_diferencia` |
| **TimeSeriesSplit** | Aplicada la idea, por cohortes | Ventana creciente: C2 → C3, C2+C3 → C4 y C2+C3 → C5 | `src/diagnostico.py` (`particion_interna`, `particion_diagnostico`), `notebooks/03_modelado.ipynb` |
| **Media ± desviación estándar** | En parte | Curvas por tamaño del entrenamiento con 5 submuestras por tamaño (banda de ±1 desviación); Lift de la regla D2 en cuatro cohortes (1,38, 1,49, 1,93 y 1,97); media de 100 sorteos de desempate (1,42, 1,57 y 1,75 en C2, C3 y C4) | `results/metrics/curvas_tamano_real.csv`, [alcance_lista.md](alcance_lista.md) |
| **Intervalos por bootstrap** | Aplicada | IC 95 % con 2.000 réplicas que remuestrean familias dentro de cada sede (Lift@k de D2 en C5: 1,97 [1,24; 2,56]). En la semana 3, bootstrap **pareado** de la diferencia de PR-AUC entre cada estrategia y su modelo de partida | `src/modeling.bootstrap_ic`, `src/diagnostico.bootstrap_diferencia`, [modelado.md](modelado.md) §3 |
| **Semillas aleatorias múltiples** | Aplicada | Cinco semillas (42, 7, 123, 2024, 9) en las estrategias de la semana 3; 100 sorteos para el desempate de la regla D2 | `config.yaml` (`diagnostico.semillas`), [alcance_lista.md](alcance_lista.md) |
| **McNemar** | No aplica | Compara aciertos y errores caso por caso de dos clasificadores con un umbral. Nuestra métrica es una lista de k familias por sede (Lift@k); para comparar dos listas usamos el bootstrap pareado de la diferencia | — |
| **Wilcoxon sobre pliegues pareados** | No aplica | Necesita muchos pliegues. Con 4 particiones temporales, el menor valor p bilateral posible es 2/2⁴ = 0,125: nunca podría salir significativo | — |
| **t pareado corregido (Nadeau–Bengio)** | No aplica | Corrige la prueba t cuando los pliegues de una validación cruzada repetida comparten datos. Sin pliegues repetidos no corresponde | — |

**Regla de veredicto de la semana 3 (D54).** En lugar de una prueba de significancia sobre pliegues, una estrategia solo «mejora» si se cumplen cuatro condiciones fijadas antes de repetir el análisis con datos reales:

1. el cambio de PR-AUC en C4 llega a 0,005;
2. el IC 95 % bootstrap pareado de la diferencia no incluye el cero;
3. la réplica en C2 → C3 va en el mismo sentido;
4. las cinco semillas van en el mismo sentido.

Con 122 eventos en C4, ninguna de las siete estrategias cumplió las cuatro.

## 3. Limitaciones

- **No hay intervalo de la diferencia entre sistemas en C5.** Tenemos el intervalo de cada sistema por separado (D2: 1,97 [1,24; 2,56]; logística híbrida: 0,98 [0,47; 1,52]), pero no el de la diferencia D2 − híbrida. No lo calculamos ahora porque obligaría a volver a usar C5, que se evaluó una sola vez, y no cambiaría la decisión: la elección de D2 se tomó en C4.
- **Pocas particiones independientes.** Solo hay cuatro cohortes comparables, y C4 y C3 ya intervinieron en decisiones (selección y optimización). La réplica C2 → C3 favorece al modelo que Optuna afinó ahí.
- **El bootstrap mide la variación entre familias de una misma cohorte**, no el cambio entre años. La variación entre años se ve en el Lift de D2 por cohorte (de 1,4 a 2,0).
- **Pocos eventos por grupo.** Los resultados por sede, beca o nivel tienen intervalos amplios ([ficha_modelo.md](ficha_modelo.md) §6).

## 4. Qué haríamos con la cohorte de 2027

La cohorte que cierre en mayo de 2027 no habrá participado en ninguna decisión. Con ella proponemos:

- evaluar la regla D2 y la logística híbrida con el mismo protocolo, incluyendo el **IC bootstrap pareado de la diferencia** registrado antes de mirar los resultados;
- añadir la cohorte a la ventana de validación temporal (C2 … C5 → C6), para tener una partición más y medir mejor la variación entre años;
- aplicar la regla de veredicto de la sección 2 a las estrategias E4a y E4b, que fueron las que más se acercaron.
