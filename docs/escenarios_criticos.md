# Escenarios críticos: evaluación en condiciones parecidas al uso real

Este documento responde a dos pedidos del workshop de la semana 5. El primero es mostrar que el sistema se evaluó en condiciones muy parecidas a las del mundo real. El segundo es simular escenarios críticos y responder la pregunta guía: **¿hasta qué nivel de perturbación la lista sigue siendo útil, y qué hace el sistema cuando deja de serlo?** La decisión está registrada como D57 en [planificacion.md](planificacion.md). El código está en `src/escenarios.py`, `src/graficos_escenarios.py` y el cuaderno `notebooks/07_escenarios_criticos.ipynb`. Ninguna simulación usa C5.

## 1. La prueba final ya imita el uso real

La prueba en C5 se diseñó para que medir el sistema fuera lo mismo que usarlo un 20 de febrero:

| Cómo se usará en LEMAS | Cómo se evaluó | Dónde |
|---|---|---|
| Cada 20 de febrero, solo con lo que se sabe a esa fecha | Foto al 20 de febrero (t0): los predictores solo usan datos anteriores. Las pensiones atrasadas deben contarse de mayo a enero (ver sección 5) | `config.yaml` (`t0_mes_dia`), [hoja_de_datos.md](hoja_de_datos.md) |
| Se aplica a un año que todavía no ocurrió | Se entrena con años pasados y se prueba con un año que no se miró antes (C2 + C3 → C5) | [evaluacion_robusta.md](evaluacion_robusta.md) §1 |
| Nadie puede ajustar el sistema mirando el resultado | Sistema congelado con huella SHA-256 registrada antes de abrir C5; C5 se evaluó una sola vez | D38, D41 |
| Se llama a familias, no a estudiantes | Métricas por familia: los hermanos se consolidan en un solo contacto | `evaluate.consolidar_familias` |
| Hay una capacidad fija de llamadas por sede | k = 118 (Mucho Lote 1) y 47 (Mucho Lote 2), como en la operación | D32 |
| Los empates se resuelven igual en la validación y en la aplicación | Mismo desempate al azar con semilla fija | D48 |
| La aplicación recibe el Excel de Secretaría | La aplicación usa la misma limpieza y la misma regla que la validación, con pruebas automáticas | `src/inferencia.py`, `tests/test_app.py` |
| Cada año es distinto | Lift de D2 en cuatro cohortes: 1,38, 1,49, 1,93 y 1,97 | [alcance_lista.md](alcance_lista.md) |
| Hay grupos distintos de familias | Resultados por sede, beca y nivel | [ficha_modelo.md](ficha_modelo.md) §6 |
| La campaña dura 10 semanas y las familias pagan mientras tanto | Análisis semanal del alcance (C2–C4) | [alcance_lista.md](alcance_lista.md) |

Lo que esta prueba **no** cubre es lo que pasa cuando los datos de entrada llegan mal o cambian. Eso es lo que simulan las secciones siguientes.

## 2. Método de la simulación

- **Qué se perturba:** solo la cohorte de selección (**C4**: 1.374 estudiantes, 1.042 familias y 95 familias con caso). C5 no interviene.
- **Qué se mide:** el sistema ya elegido, sin volver a elegir nada:
  - la **regla D2**, que prioriza y no aprende: solo cambia lo que recibe;
  - la **logística híbrida**, entrenada con C2 + C3 y con los hiperparámetros de la Fase 2. Solo se reentrena en el escenario de cambio de distribución, porque entrenar con un subgrupo es el escenario mismo.
- **Métricas:** Lift@k, Recall@k y Precision@k por familia con el k aprobado, PR-AUC y, para las probabilidades, Brier y la razón observados / esperados. **No se usa F1**, que la tabla del workshop propone: la lista ordena con capacidad fija y no clasifica con un umbral ([evaluacion_robusta.md](evaluacion_robusta.md) §3).
- **Repeticiones:** cada nivel se repite 50 veces, con otra perturbación y otro sorteo de empates. Se publican la media y el rango del percentil 5 al 95. El sorteo pesa: en C4 el Lift de D2 va de 1,53 a 1,99 según cómo se resuelvan los empates (D50). Por eso el valor «sin perturbar» es la media de los sorteos y no el 1,93 de la semilla fija.
- **Criterio de utilidad:** un nivel es útil si el Lift@k de D2 sigue en **1,20 o más** en la media y en el percentil 5. Es la meta del proyecto y el mismo umbral de alerta del seguimiento anual.

| Escenario del workshop | Versión realista para LEMAS | Niveles |
|---|---|---|
| Ruido en la entrada | **Errores de digitación**: con probabilidad *p* se invierte el pago tardío o el tipo de reserva de un estudiante, o su conteo de atrasos se corre en uno. Las señales de D2 son discretas, así que el ruido gaussiano solo se aplica al promedio, la variable continua de la logística híbrida | *p* = 1 %, 2 %, 5 %, 10 % y 20 %; σ = 0,25 a 2 puntos |
| Datos faltantes | Una señal llega vacía en una fracción de las filas, una señal por vez. Un pago vacío deja al estudiante sin esa prioridad; una reserva o un atraso vacíos se leen como cero (regla) o se imputan (modelo) | 10 % a 50 % |
| Desbalance extremo | Se quitan familias con caso (con todos sus estudiantes) hasta una tasa familiar del 5 %, 3 % y 1 %, como en un año con muy pocas familias que no se matriculan. k no cambia | C4 tiene 9,1 % |
| Cambio de distribución | La logística híbrida se entrena con C2 + C3 de un grupo, se calibra en C4 del mismo grupo y se prueba en C4 del otro: Mucho Lote 1 ↔ Mucho Lote 2 y no becados ↔ becados. Se compara con el modelo entrenado con todos | 4 direcciones |
| Feature clave caída | Una señal llega constante: atrasos todos en cero, pago anterior todo «en plazo», ninguna reserva extraordinaria, o las tres a la vez | 5 casos |

## 3. Resultados

> **Pendiente:** la ejecución del cuaderno 07 con los datos reales. Sus agregados irán en `results/metrics/escenarios_*_real.*` y las figuras en `results/figures/real_29_*` y `real_30_*`. Esta sección se completará con esas cifras.
>
> Con los **datos sintéticos** el código funciona de punta a punta (figuras `sintetica_29` y `sintetica_30`), pero sus cifras **no describen a LEMAS**. La base sintética no reproduce la fuerza de las señales: allí D2 tiene un Lift de 1,08 en C4, frente a 1,93 con los datos reales. Por eso no se sacan conclusiones de ellas.

Qué se espera leer en la ejecución real, y por qué importa:

1. **Errores de registro:** cuántos errores de digitación tolera la lista antes de caer bajo 1,20. Como D2 se apoya sobre todo en el pago tardío, que pocas familias tienen, un error que marque «tardío» a quien pagó en plazo puede llenar la lista de falsas alarmas.
2. **Faltantes:** qué señal es la crítica. Se espera que sea el pago tardío de la matrícula anterior, que es la que más separa (22 frente a 6 de cada 100).
3. **Desbalance:** con menos casos el Lift se vuelve muy inestable. Esto dice cuánto hay que desconfiar de la evaluación de un año con pocos casos.
4. **Cambio de distribución:** si la logística híbrida se transfiere entre sedes y entre becados y no becados, y si sus probabilidades se descalibran. La regla D2 no aprende, así que no sufre este problema de la misma forma, aunque su capacidad de ordenar puede ser distinta en cada grupo (la lista ya encuentra menos casos entre los becados, [ficha_modelo.md](ficha_modelo.md)).
5. **Señal caída:** cuánto pierde la lista si una columna no se calculó. Si las tres señales caen, D2 queda en el azar por construcción.

## 4. Qué hace el sistema cuando deja de ser útil

**Antes de usar la lista (cada 20 de febrero).** La aplicación revisa las señales del ciclo cargado al generar la lista (`inferencia.revisar_senales`) y muestra un **aviso en rojo** si:

- más del 80 % de los estudiantes figura como nuevo, porque falta la hoja del ciclo anterior y sin ella no se conoce el pago tardío;
- falta la fecha de pago anterior en más del 20 % de los que no son nuevos;
- ningún estudiante figura con pago tardío, cuando en todos los años revisados hubo casos;
- la columna de atrasos está vacía en más del 20 % de las filas o llegó toda en cero;
- el tipo de reserva está vacío en más del 20 % de las filas.

El aviso explica que con una señal vacía o constante la lista se acerca a una selección al azar, y pide corregir el Excel antes de usarla. La lista se muestra igual, porque quien decide es una persona, pero no puede pasar inadvertido. Estas comprobaciones solo miran proporciones del ciclo cargado y no usan el resultado, que todavía no se conoce.

Los umbrales están en `config.yaml` (`calidad_senales`) y son **provisionales**: se ajustarán con los límites de la sección 3 cuando esté la ejecución real.

**Después de la campaña (cada mayo).** Con el resultado del ciclo se recalcula el Lift@k de la lista. Si baja de 1,20 se revisa la regla, y si no supera al azar dos años seguidos se suspende su uso ([ficha_modelo.md](ficha_modelo.md) §8). La persona que designe la Dirección decide la suspensión (decisión 5 de la presentación a la Dirección).

## 5. Límites de la simulación

- **C4 ya se usó** para seleccionar y calibrar en la Fase 2: la simulación describe la sensibilidad del sistema, no es una validación nueva.
- **Las perturbaciones son supuestos razonables**, no errores observados: no tenemos registro de cuántos errores de digitación tiene realmente el Excel.
- **Entre años distintos**, el cambio de distribución ya se ve en el Lift por cohorte (sección 1). Aquí solo se simula el cambio entre grupos de una misma cohorte.
- **Con 95 familias con caso en C4**, el desbalance al 1 % deja unas 10 familias con caso, y el rango de las repeticiones es amplio por construcción.
- **La calibración de referencia** («entrenado con todos») se ajustó en todo C4, que incluye al grupo de destino. Favorece a la referencia, así que la pérdida del modelo transferido puede estar algo exagerada.
- **Columna de atrasos.** La calcula LEMAS desde el registro de pagos, y `config.yaml` recomienda contar solo de mayo a enero, porque la pensión de febrero vence después del 20 de febrero. Falta confirmar que las bases históricas se generaron así. Si incluyeran meses posteriores, los atrasos tendrían información futura. La aplicación debe recibir la columna calculada de la misma forma cada año.
