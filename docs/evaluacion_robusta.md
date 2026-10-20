# Evaluación robusta: validación, incertidumbre y comparación de sistemas

Este documento explica cómo validamos los modelos y por qué no usamos la validación cruzada aleatoria. También dice qué técnicas de evaluación robusta aplicamos, cuáles no y por qué. Las secciones 1 y 2 describen el método con el que se obtuvieron los resultados que ya están en [modelado.md](modelado.md), [optimizacion.md](optimizacion.md), [alcance_lista.md](alcance_lista.md) y el [reporte de diagnóstico](diagnostic_report.pdf) (D55). La sección 3 añade la métrica de negocio del costo esperado, calculada solo con conteos ya publicados (D56). Ambas decisiones están en [planificacion.md](planificacion.md).

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
| **Media ± desviación estándar** | En parte | Curvas por tamaño del entrenamiento con 5 submuestras por tamaño (banda de ±1 desviación); Lift de la regla D2 en cuatro cohortes (1,38, 1,49, 1,93 y 1,97); media de 100 sorteos de desempate (1,42, 1,57 y 1,75 en C2, C3 y C4); con 500 sorteos en C4, 1,77 (D59) | `results/metrics/curvas_tamano_real.csv`, [alcance_lista.md](alcance_lista.md) |
| **Intervalos por bootstrap** | Aplicada | IC 95 % con 2.000 réplicas que remuestrean familias dentro de cada sede (Lift@k de D2 en C5: 1,97 [1,24; 2,56]). En la semana 3, bootstrap **pareado** de la diferencia de PR-AUC entre cada estrategia y su modelo de partida | `src/modeling.bootstrap_ic`, `src/diagnostico.bootstrap_diferencia`, [modelado.md](modelado.md) §3 |
| **Bootstrap pareado entre sistemas** | Aplicada en C4 | Diferencia de Lift@k D2 − D con las dos reglas sobre las mismas remuestras y un sorteo nuevo en cada una: 0,00 [−0,62; 0,62] (D59) | `src/revision.diferencia_pareada`, `notebooks/08_revision_final.ipynb` |
| **Intervalos de Wilson y prueba exacta de Fisher** | Aplicada | IC 95 % de Wilson del Recall@k y del % seleccionado por grupo; Fisher para cada brecha (beca p = 0,49; sede p = 0,80) y razón de selección con IC de Katz (D60) | `src/incertidumbre.py`, `results/metrics/equidad_ic_real.csv` |
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

## 3. Métrica de negocio: costo esperado

En problemas de negocio y riesgo se recomienda elegir el umbral que minimiza el **costo esperado**, FP × cFP + FN × cFN, y no el que maximiza la exactitud. Aquí la exactitud sería engañosa: en C5, decir «todas se matriculan» acierta el 93 % (1.019 de 1.093 familias) sin encontrar ningún caso, y la lista D2 acierta el 82 % (898). Por eso reportamos Lift@k, Precision@k, Recall@k y PR-AUC, y no exactitud ni F1.

**Carga operativa.** En C5, la lista necesitó **7,5 llamadas por cada familia en riesgo encontrada** (165 llamadas, 22 casos); al azar harían falta unas 15 (1 / 6,8 %). Es la forma más directa de expresar el beneficio para Secretaría (D60).

**Por qué el umbral lo fija la capacidad.** Una llamada de más (cFP) cuesta minutos del personal y una molestia pequeña para la familia. Un estudiante que no continúa (cFN) cuesta un año de pensiones y la continuidad del niño. Como cFN es mucho mayor que cFP, el umbral de costo mínimo pediría llamar a más familias de las que el personal puede atender. Con la capacidad k como restricción, minimizar el costo equivale a encontrar el mayor número de casos con k llamadas, que es lo que mide Lift@k. Es el argumento formal de la métrica principal.

**Cómo lo adaptamos.** Una llamada no rescata todos los casos: solo una fracción, la *eficacia*, que no conocemos y que mediría un piloto controlado en 2027, con una parte de las familias elegida al azar y atendida como siempre ([consideraciones_eticas.md](consideraciones_eticas.md), seguimiento). Medimos todo en llamadas (cFP = 1) y con la razón R = cFN / cFP, sin montos reales:

- beneficio neto de k llamadas = eficacia × R × aciertos − k;
- llamar compensa si precisión × eficacia × R > 1, es decir, si R supera la **razón de equilibrio** R* = 1 / (precisión × eficacia). Cuanto menor es R*, más fácil es que las llamadas compensen.

**Resultados** (`tools/generar_costo.py`, `src/costo.py`). Son aritmética sobre las tablas `alcance_por_k_real.csv` y `alcance_semanal_real.csv` (C2–C4) y la precisión de D2 en C5 ya publicada (D41). **C5 no se vuelve a evaluar.**

| Escenario | Cohorte | Proporción de casos | R* con eficacia 10 % | R* con eficacia 25 % |
|---|---|---|---|---|
| Llamar al azar a k familias | C4 | 9,1 % | 110 | 44 |
| Primera mitad de la lista D2 (k/2) | C4 | 24,1 % | 41 | 17 |
| Lista D2 completa (k) | C4 | 17,6 % | 57 | 23 |
| Alargar la lista de k a 2k (familias nuevas) | C4 | 9,7 % | 103 | 41 |
| Llamar a quienes siguen sin pagar en la semana 5 | C2–C4 | 37,6 % | 27 | 11 |
| Lista D2 completa (k), prueba final | C5 | 13,3 % | 75 | 30 |
| Llamar al azar, prueba final | C5 | 6,8 % | 148 | 59 |

Lectura:

1. **La lista reduce a la mitad lo que debe valer un caso para que llamar compense:** de 110 a 57 en C4 y de 148 a 75 en C5. Si una llamada rescata al 10 % de los casos y un estudiante perdido vale más de 75 llamadas, la lista compensa. Con 15 minutos por llamada, eso son unas 19 horas de personal por estudiante.
2. **El valor de la lista está al principio.** La primera mitad tiene 24 % de casos. Las familias que se añaden al alargarla de k a 2k tienen 9,7 %, casi lo mismo que al azar (9,1 %). Las tres cohortes juntas dan lo mismo: el tramo de k a 2k necesita R mayor que 99 a 112, y el último tramo (de 4k a todas las familias), mayor que 160 (`costo_marginal_real.csv`).
3. **La capacidad extra rinde más en una segunda llamada.** Entre quienes siguen sin pagar en la semana 5 el 38 % son casos (R* = 27), contra 9,7 % si se alarga la lista inicial. Es la campaña en dos etapas de D50, con una salvedad: quedan menos días de margen (41) y la eficacia de una llamada tardía puede ser distinta. Sigue sin validar.
4. **Cuánto vale un caso lo decide la institución.** Con eficacia del 10 %, el tamaño de lista con mayor beneficio en C4 es k/2 si un caso vale 50 llamadas, k si vale 100 y todas las familias si vale 200 (figura `results/figures/real_28_costo_esperado.png`). El análisis no fija k: dice a partir de qué valor conviene cada tamaño.

**Límites.** La eficacia y la razón R son supuestos. La precisión por tramos de C4 se apoya en pocos casos (de 7 a 23 por tramo), y las cifras de C2–C4 describen, no validan: son las cohortes con las que se eligió la regla. El costo de una llamada a una familia que sí iba a pagar no es solo tiempo: si la llamada se percibe como cobranza, daña la relación. Por eso el protocolo de apoyo de [consideraciones_eticas.md](consideraciones_eticas.md) es parte del cálculo.

La sensibilidad del sistema ante datos de entrada perturbados (errores de registro, faltantes, desbalance extremo, cambio de distribución y señal caída) está en [escenarios_criticos.md](escenarios_criticos.md) (D57).

## 4. Limitaciones

- **No hay intervalo de la diferencia entre sistemas en C5.** Tenemos el intervalo de cada sistema por separado (D2: 1,97 [1,24; 2,56]; logística híbrida: 0,98 [0,47; 1,52]), pero no el de la diferencia D2 − híbrida. No lo calculamos ahora porque obligaría a volver a usar C5, que se evaluó una sola vez, y no cambiaría la decisión: la elección de D2 se tomó en C4.
- **Pocas particiones independientes.** Solo hay cuatro cohortes comparables, y C4 y C3 ya intervinieron en decisiones (selección y optimización). La réplica C2 → C3 favorece al modelo que Optuna afinó ahí.
- **El bootstrap mide la variación entre familias de una misma cohorte**, no el cambio entre años. La variación entre años se ve en el Lift de D2 por cohorte (de 1,4 a 2,0).
- **Pocos eventos por grupo.** Los resultados por sede, beca o nivel tienen intervalos amplios: con 11 eventos en becadas, el IC de Wilson del recall va de 5 % a 48 % ([consideraciones_eticas.md](consideraciones_eticas.md) §5).

## 5. Qué haríamos con la cohorte de 2027

La cohorte que cierre en mayo de 2027 no habrá participado en ninguna decisión. Con ella proponemos:

- evaluar la regla D2 y la logística híbrida con el mismo protocolo, incluyendo el **IC bootstrap pareado de la diferencia** registrado antes de mirar los resultados;
- añadir la cohorte a la ventana de validación temporal (C2 … C5 → C6), para tener una partición más y medir mejor la variación entre años;
- aplicar la regla de veredicto de la sección 2 a las estrategias E4a y E4b, que fueron las que más se acercaron;
- medir la **eficacia** de la llamada con ese grupo de comparación para reemplazar el supuesto de la sección 3 y recalcular el tamaño de lista que conviene.
