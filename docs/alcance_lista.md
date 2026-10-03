# Alcance de la lista: el 70 % que no encuentra

> **Estado:** método construido y probado con datos sintéticos (D50, 03-oct-2026). **Falta ejecutarlo con datos reales**; hasta entonces este documento no contiene conclusiones sobre LEMAS.
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

## 6. Resultados

**Con datos reales: pendiente.** Se completará cuando el cuaderno se ejecute con `FUENTE = "real"` y se compartan los agregados (`alcance_real.zip`).

Archivos que genera el cuaderno:

| Archivo | Contenido |
|---|---|
| `results/metrics/alcance_desglose_{fuente}.csv` | Casos por tipo y aciertos de la lista por tipo |
| `results/metrics/alcance_por_k_{fuente}.csv` | Recall, precisión, Lift y carga de trabajo según el número de contactos |
| `results/metrics/alcance_semanal_{fuente}.csv` | Grupo pendiente y alcance de la lista por semana |
| `results/metrics/alcance_campana_{fuente}.csv` | Comparación de las cuatro estrategias |
| `results/metrics/alcance_{fuente}.json` | Resumen y frases de lectura |
| `results/figures/{fuente}_24` a `_27` | Cuatro figuras a 300 DPI |

## 7. Qué decisiones puede informar

| Si los datos reales muestran… | Entonces conviene… |
|---|---|
| Que la lista encuentra sobre todo a quienes pagan tarde | Evaluar la regla con el evento «no registra ningún pago» en la siguiente cohorte, y decirlo en la documentación |
| Que duplicar los contactos sube mucho el alcance y el personal puede asumirlo | Revisar k con Secretaría a partir de la capacidad real |
| Que, repartida, buena parte de la lista ya habrá pagado cuando le llegue el turno, y que la lista semanal alcanza más casos también en la primera mitad | Probar la lista semanal en la siguiente campaña, con un grupo de comparación |
| Que casi todo el mundo paga en los últimos días | La lista semanal aporta poco: la mejora tiene que venir de datos nuevos (intención de continuar, alertas del tutor) |
| Que la regla añade poco sobre el azar entre las familias pendientes | Lo que ayuda es saber quién sigue sin pagar, no la regla: bastaría un listado de pendientes actualizado |

Cualquiera de estos cambios es una hipótesis para la campaña de 2027. No se puede validar ahora: C5 ya se usó una vez y C4 ya se usó para elegir.

## 8. Lo que este análisis no cubre

Quedan como trabajo futuro, porque necesitan datos o campañas que hoy no existen:

- **Contacto escalonado:** mensaje a todas las familias y llamada a las priorizadas y a las que no responden.
- **Señal de intención:** confirmación de continuidad en enero, solicitud de documentos para otro colegio, alerta del tutor.
- **Variables que la regla ignora:** estudiante nuevo, años de cambio de nivel, hermanos, empeoramiento reciente de los pagos.
- **Grupo de comparación al azar** para medir el efecto de la llamada.
