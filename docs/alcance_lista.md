# Alcance de la lista: el 70 % que no encuentra

> **Estado:** ejecutado con datos reales el 03-oct-2026 (D50). Cohortes C2, C3 y C4: 2.986 familias y 260 casos. El recall de D2 en C4 coincide con el de la Fase 2 (0,3053). Queda pendiente una nueva ejecución para publicar el desglose por tipo (sección 6.1).
>
> Cuaderno: [`06_alcance_lista.ipynb`](../notebooks/06_alcance_lista.ipynb) · Código: `src/alcance.py`, `src/graficos_alcance.py` · Pruebas: `tests/test_alcance.py`

## 1. El problema

En la prueba final (C5) hubo 1.093 familias con reserva aprobada y 74 no pagaron la matrícula en plazo. La lista de 165 familias contenía a 22 de ellas: el 30 %. Las otras 52 quedaron fuera.

| | Familias en la lista | Casos encontrados | Recall |
|---|---|---|---|
| Selección al azar | 165 | ≈ 11 | 15 % |
| **Regla D2** | 165 | **22** | **30 %** |
| Orden perfecto | 165 | 74 | 100 % |

La lista tiene más cupos (165) que casos (74). Un orden perfecto los encontraría todos, así que **con este k lo que limita es el orden (la señal), no el número de cupos**. Con los datos administrativos disponibles no sabemos distinguir a la mayoría de las familias que no pagarán a tiempo. Más contactos también alcanzarían más casos, pero a costa de dejar de priorizar (sección 4).

## 2. Qué revisamos y por qué

| Crítica al diseño actual | Análisis | Función |
|---|---|---|
| La etiqueta mezcla a quien paga unos días tarde con quien no registra ningún pago. La señal más fuerte de la regla es haber pagado tarde antes, así que puede estar encontrando sobre todo a los primeros | Desglose del evento y aciertos de la lista por tipo | `desglose_evento` |
| k (118 y 47) es el doble del promedio histórico de casos. Fue una decisión (D32), no una medida de lo que el personal puede hacer: son menos de dos contactos por persona y semana | Recall, precisión y carga de trabajo con otros tamaños de lista | `alcance_por_k` |
| La lista es una foto del 20 de febrero. Durante la campaña aparece información que ese día no existe: quién sigue sin pagar | Grupo pendiente semana a semana, y comparación de tres formas de usar los mismos contactos | `foto_semanal`, `campana` |

## 3. Reglas del análisis

- **C5 no interviene.** Se usan las cohortes de entrenamiento y C4. Una prueba comprueba que cambiar C5 no altera ninguna de las cuatro tablas.
- **Es descriptivo.** Son las mismas cohortes con las que se exploraron los datos y se eligió la regla: sus cifras ayudan a decidir cómo usar el sistema, no lo validan.
- **No se optimiza nada.** Ningún resultado de aquí cambia la regla ni el modelo.
- **La lista es la misma de la validación.** Una prueba comprueba que son las mismas familias en cada cohorte, y el cuaderno comprueba que el Recall@k de D2 en C4 coincide con el de la Fase 2.
- **Privacidad.** Los conteos entre 1 y 4 se ocultan, y si en una fila de cohortes queda una sola celda oculta se oculta otra más, para que no se deduzca del total. El desglose por tipo solo se publica por cohorte si ninguna celda es pequeña. La foto semanal solo se publica para el conjunto de las cohortes, y una semana se oculta si desde la última semana publicada pagaron menos de 5 familias.

## 4. Cómo se mide cada cosa

**Unidad.** La familia (representante). Es un caso si alguno de sus estudiantes no tiene la matrícula pagada al 30 de abril, y sigue *pendiente* hasta que paga el último.

**Tipos de caso.**
- *Todos pagan, el último después del 30 de abril.* La familia continúa, pero tarde.
- *Paga por unos estudiantes y no por otros.*
- *No registra ningún pago* en el ciclo siguiente.

**Quién sigue pendiente.** Cada semana se toman las familias que aún no terminan de pagar. Quien paga sale del grupo; quien no pagará en plazo se queda hasta el final. Por eso el grupo se achica y la proporción de casos sube, con regla o sin ella. No es una variable predictiva: es el resultado, que se va revelando. Cerca del 30 de abril, seguir pendiente es casi lo mismo que ser un caso.

**Tres formas de usar los mismos k contactos.**

| Estrategia | Qué hace |
|---|---|
| Lista fija, toda en la semana 1 | El mejor caso del diseño actual: todas las llamadas con el margen completo |
| Lista fija, repartida | Se llama en orden durante las 10 semanas y se salta a quien ya pagó; su cupo queda sin usar |
| Lista semanal | Igual, pero el cupo de quien ya pagó pasa a la siguiente familia pendiente del mismo orden |

El orden es el mismo en las tres (regla D2 y un solo sorteo entre empatadas), así que la lista semanal no puede alcanzar menos casos que la fija: solo usa cupos que la fija deja libres. Dos versiones al azar (fija y semanal) separan cuánto se gana solo por saber quién sigue pendiente y cuánto añade la regla.

**Medidas por estrategia.** Casos alcanzados en toda la campaña; casos alcanzados en la primera mitad de las semanas, cuando queda más tiempo para ayudar; margen medio de un acierto (días que faltaban hasta el 30 de abril al empezar la semana de la llamada); cupos sin usar; y el rango del recall al cambiar el sorteo entre familias empatadas.

## 5. Límites que hay que tener presentes

1. **Las fechas de pago son las históricas.** La simulación supone que las llamadas no cambian cuándo paga una familia. En una campaña real sí lo harían.
2. **Alcanzar tarde vale menos.** Esperar concentra los casos, pero deja menos tiempo para actuar. Un alcance del 90 % en la semana 9 no es mejor que uno del 40 % en la semana 3. El total de la lista semanal no se puede comparar sin más con el de la lista fija: quien paga no puede ser un caso, así que quitarlo mejora cualquier lista, incluso una al azar.
3. **Detectar no es ayudar.** Nada de esto mide si la llamada cambia la decisión de la familia. Para eso hace falta un grupo de comparación en una campaña real.
4. **«No registra ningún pago» no es lo mismo que «se fue».** Puede haber pagos no registrados o estudiantes que continúan por otra vía. Es la mejor aproximación con los datos disponibles.
5. **Las fechas de pago sintéticas son inventadas.** En los datos de ejemplo casi todas las familias pagan en las primeras semanas, lo que exagera la ventaja de la lista semanal. Las cifras sintéticas sirven para probar el código y nada más.

## 6. Resultados con datos reales

Cohortes C2, C3 y C4 juntas: 2.986 familias, 260 casos (8,7 %), k = 165 familias por año. Todas las cifras salen de los agregados de `results/metrics/alcance_*_real.csv`; las figuras son `results/figures/real_24` a `real_27`. Las cifras «por año» son el total de las tres cohortes dividido para tres, y el resumen automático del cuaderno escribe 1,6 y 9,9 contactos por persona y semana donde aquí se lee 1,7 y 10,0 (los valores son 1,65 y 9,95).

### 6.1 Qué hay dentro del evento: todavía sin respuesta

Con la primera versión de la regla de privacidad, el desglose por tipo no se pudo publicar: alguna celda tenía menos de 5 familias y se ocultó la tabla entera. La regla se afinó para ocultar solo la celda pequeña y una más; **hace falta volver a ejecutar el cuaderno** para saber cuántos casos son familias que no registran ningún pago y a cuántas de ellas encuentra la lista.

### 6.2 Más contactos

| × k aprobado | Contactos por año | Familias contactadas | Casos alcanzados | Al azar | Precisión | Lift | Contactos por persona y semana |
|---|---|---|---|---|---|---|---|
| 0,5 | 83 | 8 % | 17 % | 8 % | 0,177 | 2,03 | 0,8 |
| **1 (aprobado)** | **165** | **17 %** | **27 %** | 17 % | 0,139 | 1,60 | 1,7 |
| 1,5 | 248 | 25 % | 36 % | 25 % | 0,126 | 1,45 | 2,5 |
| 2 | 330 | 33 % | 45 % | 33 % | 0,117 | 1,35 | 3,3 |
| 3 | 495 | 50 % | 62 % | 50 % | 0,108 | 1,24 | 5,0 |
| 4 | 660 | 66 % | 76 % | 66 % | 0,100 | 1,14 | 6,6 |
| Todas | ≈ 995 | 100 % | 100 % | 100 % | 0,087 | 1,00 | 10,0 |

- **La regla añade entre 9 y 12 puntos sobre el azar con cualquier tamaño de lista.** No más. Con el doble de contactos se llega al 45 % de los casos, pero 33 de esos 45 puntos los daría cualquier lista de ese tamaño.
- **La capacidad no es el límite.** Contactar a todas las familias una vez son 10 contactos por persona y semana, dos por día laborable. El k aprobado son menos de dos por semana.
- **El Lift cambia con la cohorte:** 1,38 en C2, 1,49 en C3 y 1,93 en C4. C4 es la cohorte donde se eligió la regla, así que su cifra es la más favorable. Con el 1,97 de la prueba final (C5, IC 95 % [1,24; 2,56]), el Lift de la regla ha ido de 1,4 a 2,0 en cuatro cohortes: no hay base para esperar siempre el valor más alto.

### 6.3 Quién sigue sin pagar

| Semana | Día | Familias pendientes | Por año | Casos entre las pendientes | Lista D2 de k: casos que contiene | Lista al azar entre pendientes |
|---|---|---|---|---|---|---|
| 1 | 0 | 100 % | 995 | 8,7 % | 27 % | 17 % |
| 2 | 7 | 90 % | 893 | 9,7 % | 28 % | 18 % |
| 3 | 14 | 65 % | 649 | 13,3 % | 30 % | 25 % |
| 4 | 21 | 39 % | 390 | 22,2 % | 41 % | 42 % |
| 5 | 28 | 23 % | 231 | 37,6 % | 64 % | 72 % |
| 6 | 35 | 20 % | 198 | 43,8 % | 80 % | 83 % |
| 7 | 42 | 16 % | 161 | 53,9 % | 94 % | 96 % |
| 8 | 49 | 12 % | 124 | 69,7 % | 100 % | 100 % |
| 10 | 63 | 9 % | 94 | 91,9 % | 100 % | 100 % |

- **Tres de cada cuatro familias pagan en las primeras cuatro semanas.** El día 28 solo queda pendiente el 23 %.
- **A mitad de campaña quedan unas 200 familias pendientes por año**, poco más que el k aprobado (165), y el 44 % son casos. Contactarlas a todas el día 35 alcanzaría a todos los casos con 34 días de margen.
- **La ventaja de la regla está solo al principio.** Desde la semana 4 no ordena mejor que el azar entre las familias pendientes, y en la semana 5 queda por debajo: su lista contiene 166 casos y una al azar contendría unos 186. Una explicación posible, que no pudimos comprobar, es que las señales de la regla (haber pagado tarde antes) marcan a familias que suelen pagar tarde pero dentro del plazo. Encaja con la crítica a la etiqueta de la sección 2.

### 6.4 Tres formas de usar los mismos contactos

| Estrategia | Casos alcanzados | En la primera mitad | Margen medio | Cupos sin usar |
|---|---|---|---|---|
| Lista fija, toda en la semana 1 · regla D2 | 27 % | 27 % | 69 días | 0 % |
| Lista fija, repartida en la campaña · regla D2 | 27 % | 17 % | 42 días | 52 % |
| Lista semanal · regla D2 | 82 % | 25 % | 27 días | ≈ 0 % |
| Lista fija, toda en la semana 1 · al azar | 16 % | 16 % | 69 días | 0 % |
| Lista semanal · al azar | 80 % | 18 % | 26 días | ≈ 0 % |

- **Repartir la lista fija es desperdiciarla.** Si se llama en orden durante las diez semanas, la mitad de las familias (52 %) ya habrá pagado cuando le llegue el turno.
- **La lista semanal alcanza al 82 %, pero no antes.** En la primera mitad de la campaña llega al 25 %, dos puntos menos que la lista fija llamada al inicio. Todo lo que gana lo gana en la segunda mitad, con un margen medio de 27 días.
- **Lo que gana no se debe a la regla.** Una lista semanal al azar alcanza al 80 %. La regla aporta 7 puntos en la primera mitad (25 % frente a 18 %) y 2 en el total.
- **El sorteo entre familias empatadas importa.** Muchas familias tienen el mismo puntaje y el corte de la lista cae entre ellas. Según cómo caiga el sorteo, el alcance de la lista fija va de 25 % a 28 % en el conjunto, y en C4 de 24 % a 32 %. El 30,5 % de C4 que se usó para elegir la regla (Lift 1,93) está en la parte alta de ese rango; con el sorteo más desfavorable habría sido 1,53, igual que la logística híbrida.

## 7. Qué concluimos

1. **El 30 % no mejora con más modelo ni con más cupos, sino con tiempo.** El 20 de febrero los datos no distinguen a la mayoría de los casos. Cinco semanas después, basta mirar quién sigue sin pagar.
2. **La regla D2 sirve para empezar, no para toda la campaña.** Ordena mejor que el azar las primeras tres semanas (Lift de 1,4 a 1,9 según la cohorte). Después no añade nada.
3. **El resultado de C4 era algo optimista.** Parte de la ventaja de D2 sobre el mejor modelo dependía del sorteo entre empatadas. La prueba final en C5 no se toca y sigue siendo el resultado del proyecto, pero en adelante conviene informar el promedio de varios sorteos y no uno solo.
4. **Sigue sin saberse si llamar ayuda.** Todo lo anterior mide a quién se alcanza y cuándo.

### Propuesta para la campaña de 2027 (hipótesis, no resultado)

| Etapa | Cuándo | A quién | Contactos por año |
|---|---|---|---|
| 1 | 20 de febrero, en las dos primeras semanas | Las k familias de la regla D2 | 165 |
| 2 | Hacia el día 28 a 35 | Todas las familias que siguen sin pagar y aún no fueron contactadas | 200 a 230, menos las ya contactadas |

En total serían menos de 400 contactos por año, unos cuatro por persona y semana. Con las fechas de pago históricas, este esquema alcanzaría a todos los casos con unas cinco semanas de margen (41 días si la segunda etapa empieza el día 28 y 34 si empieza el día 35), frente al 27 % de la lista actual.

Tres advertencias antes de adoptarlo:
- Usa fechas históricas: si la primera etapa cambia cuándo pagan las familias, la segunda será distinta.
- No se puede validar con los datos actuales. Debe probarse en la campaña de 2027 con un grupo de comparación elegido al azar.
- La aplicación ya lista a las familias pendientes a una fecha de corte (pestaña *Seguimiento*, D51). Eso hace posible la segunda etapa, pero no la valida.

## 8. Lo que este análisis no cubre

Quedan como trabajo futuro, porque necesitan datos o campañas que hoy no existen:

- **Contacto escalonado:** mensaje a todas las familias y llamada a las priorizadas y a las que no responden.
- **Señal de intención:** confirmación de continuidad en enero, solicitud de documentos para otro colegio, alerta del tutor.
- **Variables que la regla ignora:** estudiante nuevo, años de cambio de nivel, hermanos, empeoramiento reciente de los pagos.
- **Grupo de comparación al azar** para medir el efecto de la llamada.
