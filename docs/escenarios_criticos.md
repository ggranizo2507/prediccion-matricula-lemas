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

## 3. Resultados con los datos reales

Fuente: cuaderno 07 ejecutado con la base seudonimizada (18-oct-2026); agregados en `results/metrics/escenarios_*_real.*` y figuras `results/figures/real_29_escenarios_criticos.png` y `real_30_cambio_distribucion.png`. La comprobación inicial reproduce la Fase 2 en C4 con la semilla fija (D2: Lift@k 1,93; logística híbrida: 1,53). **Sin perturbar**, la media de los 50 sorteos de empates da para D2 un Lift@k de **1,77** (del 1,60 al 1,93) y un Recall@k de 28 %.

Entre corchetes, el rango del percentil 5 al 95 de las repeticiones.

### 3.1 Errores de registro: la debilidad principal

| Probabilidad de error por señal | Lift@k de D2 | Logística híbrida | ¿Útil? |
|---|---|---|---|
| 0 % | 1,77 [1,60; 1,93] | 1,53 | Sí |
| 1 % | 1,67 [1,43; 1,93] | 1,51 | Sí |
| 5 % | 1,63 [1,40; 1,99] | 1,47 | Sí |
| 10 % | 1,48 [1,23; 1,80] | 1,33 | Sí, al límite |
| 20 % | 1,24 [0,89; 1,57] | 1,25 | **No** |

Es el escenario que más daño hace, y el único que la aplicación no puede detectar sola: un dato mal digitado no deja rastro. Basta un 1 % de errores para bajar el Lift de 1,77 a 1,67. La razón es la forma de la regla: un «pagó tarde» puesto por error lleva a esa familia al primer grupo de la lista y ocupa el lugar de un caso real. La lista **tolera hasta un 10 % de errores** y deja de ser útil hacia el 20 %. El ruido gaussiano en el promedio afecta solo a la logística híbrida: con σ = 2 puntos baja de 1,53 a 1,28.

### 3.2 Datos faltantes y señal caída: la regla es redundante

| Señal | 50 % vacía (D2) | Constante (D2) | Constante (híbrida) |
|---|---|---|---|
| Ninguna (sin perturbar) | 1,77 | 1,77 | 1,53 |
| Pago tardío de la matrícula anterior | 1,75 | 1,78 | 1,40 |
| Reserva extraordinaria | 1,67 | 1,75 | **1,13** |
| Pensiones pagadas tarde | 1,73 | 1,66 | 1,46 |
| Las tres señales de D2 | — | **1,05** [0,73; 1,37] | **0,86** |

Con **una sola** señal vacía hasta en la mitad de las filas, o incluso constante, la regla casi no cambia: su Lift queda entre 1,66 y 1,78, y el percentil 5 nunca baja de 1,43. Las tres señales se solapan. Las familias que pagaron tarde la matrícula suelen tener también pensiones atrasadas, así que si una señal falta, las otras la cubren. Esto **no significa** que el pago tardío no importe; significa que en C4 su información ya está en buena parte en los atrasos. Solo cuando caen **las tres** la lista queda en el azar (1,05).

La logística híbrida es más frágil. Sin la reserva extraordinaria baja a 1,13, bajo el umbral, y con las tres señales caídas a 0,86, peor que el azar.

### 3.3 Desbalance extremo: la lista sirve, la medición no

| Tasa familiar del evento | Familias con caso (aprox.) | Lift@k de D2 | PR-AUC |
|---|---|---|---|
| 9,1 % (C4 real) | 95 | 1,77 [1,60; 1,93] | 0,137 |
| 5 % | 50 | 1,85 [1,38; 2,24] | 0,083 |
| 3 % | 29 | 1,77 [1,22; 2,45] | 0,057 |
| 1 % | 10 | 1,87 [0,58; 2,90] | 0,032 |

En promedio, la lista sigue encontrando casi el doble de casos que el azar aunque haya muy pocos. Lo que se rompe es la **medición**. Con 10 familias con caso, la misma lista puede parecer inútil (0,58) o excelente (2,90) según qué familias queden. El criterio de utilidad se cumple hasta una tasa del 3 %. La PR-AUC baja con la tasa porque depende de la prevalencia: no sirve para comparar años con tasas distintas, y por eso la métrica principal es el Lift.

Consecuencia práctica: en un año con muy pocos casos, el control de mayo no debe decidir con un solo año. La regla ya lo prevé, pues solo se suspende el uso si la lista no supera al azar **dos años seguidos**.

### 3.4 Cambio de distribución: la logística híbrida no se transfiere entre sedes

| Origen → destino | PR-AUC transferida | PR-AUC entrenada con todos | Regla D2 | Observados / esperados (transferida) |
|---|---|---|---|---|
| Mucho Lote 1 → Mucho Lote 2 | **0,071** (ROC-AUC 0,40) | 0,183 | 0,134 | **0,74** |
| Mucho Lote 2 → Mucho Lote 1 | 0,165 | 0,112 | 0,143 | **1,27** |
| No becados → becados | 0,256 | 0,266 | 0,387 | 0,94 |
| Becados → no becados | 0,109 | 0,122 | 0,133 | 0,93 |

Cada PR-AUC se compara dentro de su fila, porque depende de la tasa de cada grupo.

- **Entre sedes**, el modelo no se transfiere. Entrenado con Mucho Lote 1 ordena peor que el azar en Mucho Lote 2 (ROC-AUC 0,40) y sobrestima el riesgo: espera un 35 % más de casos de los que hubo. Entrenado con Mucho Lote 2 subestima el riesgo en Mucho Lote 1 (observados / esperados 1,27). El resultado de la dirección inversa, mejor que el modelo de todos, muestra lo inestable que es aprender con pocos casos por sede (en C4 hay 39 estudiantes con caso en Mucho Lote 2 y 83 en Mucho Lote 1).
- **Entre becados y no becados**, sí se transfiere: la discriminación es parecida y la calibración se desvía menos de un 7 %.
- **La regla D2 no se entrena**, así que no tiene este problema. En tres de las cuatro direcciones ordena igual o mejor que el modelo transferido. Para los becados, su PR-AUC alta (0,387) se apoya en solo 13 estudiantes con caso y es muy incierta.

Es otro argumento a favor de usar una sola regla común en lugar de modelos por sede.

### 3.5 Límites operativos

| Escenario | La lista sigue siendo útil (Lift@k ≥ 1,20 en la media y el percentil 5) | Deja de serlo |
|---|---|---|
| Errores de registro | Hasta el 10 % | Hacia el 20 % |
| Una señal vacía | Hasta el 50 %, todo el rango probado | — |
| Una señal constante | Sí, cualquiera de las tres | — |
| Las tres señales caídas | — | Siempre (1,05) |
| Pocos casos en el año | Hasta una tasa del 3 % | Al 1 % la medición no es confiable |
| Cambio entre sedes | Regla D2 común: sí | Un modelo por sede: no |

## 4. Qué hace el sistema cuando deja de ser útil

**Antes de usar la lista (cada 20 de febrero).** Al generar la lista, la aplicación revisa las señales del ciclo cargado (`inferencia.revisar_senales`). Una señal cuenta como **afectada** si:

- más del 80 % de los estudiantes figura como nuevo (falta la hoja del ciclo anterior), falta la fecha de pago anterior en más del 30 % de los que no son nuevos, o ningún estudiante figura con pago tardío;
- la columna de atrasos está vacía en más del 30 % de las filas o llegó toda en cero;
- el tipo de reserva está vacío en más del 30 % de las filas.

El aviso tiene dos niveles, que siguen los resultados de la sección 3.2:

| Señales afectadas | Aviso | Por qué |
|---|---|---|
| Una | **Amarillo** («Revise los datos cuando pueda»). Dice que la lista sigue ordenando casi igual, pero que conviene corregir el Excel | Con una sola señal caída el Lift queda entre 1,66 y 1,78 |
| Dos o más | **Rojo** («Revise los datos antes de usar esta lista»). Dice que la lista se acerca al azar y pide corregir el Excel y volver a generarla | Con las tres caídas el Lift es 1,05 |

La lista se muestra igual, porque quien decide es una persona, pero el aviso no puede pasar inadvertido. Las comprobaciones solo miran proporciones del ciclo cargado y no usan el resultado, que todavía no se conoce. Los umbrales están en `config.yaml` (`calidad_senales`). El 30 % deja margen: la simulación muestra que la regla aguanta hasta el 50 %, pero tantos vacíos casi siempre indican un error de exportación.

**Contra los errores de registro**, que ninguna comprobación automática detecta, la medida es de procedimiento. Antes de llamar, quien tenga la lista confirma en el sistema de Secretaría que el motivo de cada familia es correcto, sobre todo «pagó tarde la matrícula anterior». La lista tiene 165 familias, así que la revisión es breve, y es justo donde un error hace más daño (sección 3.1).

**Después de la campaña (cada mayo).** Con el resultado del ciclo se recalcula el Lift@k de la lista. Si baja de 1,20 se revisa la regla, y si no supera al azar dos años seguidos se suspende su uso ([ficha_modelo.md](ficha_modelo.md) §8). En un año con muy pocos casos (menos del 3 %), un solo año no basta para decidir (sección 3.3). La persona que designe la Dirección decide la suspensión (decisión 5 de la presentación a la Dirección).

## 5. Límites de la simulación

- **C4 ya se usó** para seleccionar y calibrar en la Fase 2: la simulación describe la sensibilidad del sistema, no es una validación nueva.
- **Las perturbaciones son supuestos razonables**, no errores observados: no tenemos registro de cuántos errores de digitación tiene realmente el Excel.
- **Entre años distintos**, el cambio de distribución ya se ve en el Lift por cohorte (sección 1). Aquí solo se simula el cambio entre grupos de una misma cohorte.
- **Con 95 familias con caso en C4**, el desbalance al 1 % deja unas 10 familias con caso, y el rango de las repeticiones es amplio por construcción.
- **La calibración de referencia** («entrenado con todos») se ajustó en todo C4, que incluye al grupo de destino. Favorece a la referencia, así que la pérdida del modelo transferido puede estar algo exagerada.
- **Columna de atrasos.** La calcula LEMAS desde el registro de pagos, y `config.yaml` recomienda contar solo de mayo a enero, porque la pensión de febrero vence después del 20 de febrero. Falta confirmar que las bases históricas se generaron así. Si incluyeran meses posteriores, los atrasos tendrían información futura. La aplicación debe recibir la columna calculada de la misma forma cada año.
