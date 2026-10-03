# Consideraciones éticas

El sistema trata datos de **menores de edad y sus familias** y orienta acciones de una institución educativa sobre ellas. Por eso la ética no es un anexo: condicionó el diseño de los datos, del modelo, de la aplicación y de la forma de comunicar los resultados.

Este documento sigue los siete puntos que pide la guía del proyecto (sesgos, equidad, privacidad, transparencia, impacto social, responsabilidad y mal uso) y añade los temas de la semana 4 del curso: principios, dilemas, mapa de actores, cadena de responsabilidad, marcos de referencia y cumplimiento normativo. El workshop de impacto social y responsabilidad lo resume en ocho partes, con severidad y probabilidad de cada riesgo, una estrategia de mitigación por riesgo y el compromiso ético del equipo: [impacto_social_responsabilidad.md](impacto_social_responsabilidad.md).

> **Alcance de lo que aquí se afirma.** Distinguimos lo que **ya está implementado** en el proyecto de lo que **LEMAS debe completar** antes de un uso permanente. La lectura de las normas es la de un equipo técnico, no una asesoría legal: LEMAS debe confirmarla con su asesor jurídico o su delegado de protección de datos.

| # | Sección | Punto de la guía |
|---|---|---|
| 1 | Propósito y uso permitido | 7 |
| 2 | Principios éticos y cómo se cumplen | — |
| 3 | Dilemas éticos del proyecto | — |
| 4 | Sesgos identificados | 1 |
| 5 | Equidad | 2 |
| 6 | Privacidad y protección de datos | 3 |
| 7 | Transparencia y explicabilidad | 4 |
| 8 | Impacto social | 5 |
| 9 | Responsabilidad y rendición de cuentas | 6 |
| 10 | Uso dual y mal uso | 7 |
| 11 | Regulación y cumplimiento | 3 |
| 12 | Consideraciones prácticas de implementación | 6 |
| 13 | Honestidad sobre las capacidades | — |
| 14 | Limitaciones éticas reconocidas | — |
| 15 | Lista de verificación | — |

## 1. Propósito y uso permitido

| Uso permitido | Uso prohibido |
|---|---|
| Priorizar **contactos de apoyo** (información, planes de pago, atención de inquietudes) entre el 20 de febrero y el 30 de abril | Negar, condicionar o retirar cupos, reservas, becas o servicios |
| Planificar cupos, paralelos y personal con la proyección agregada | Presionar o cobrar a familias por aparecer en la lista |
| Evaluar el proceso de reservas de forma agregada | Perfilar a estudiantes o familias con fines distintos al aprobado |

La lista es un **apoyo a la decisión humana**. La aplicación no contacta a nadie ni toma decisiones: Secretaría revisa cada caso.

## 2. Principios éticos y cómo se cumplen

Tomamos como referencia los principios de la Recomendación de la UNESCO sobre la ética de la IA (2021) y los Principios de IA de la OCDE (2019, actualizados en 2024). La tabla recoge ocho de los diez principios de la UNESCO; los de sostenibilidad y gobernanza con múltiples actores no los trabajamos. Como los titulares son menores, revisamos también la guía de UNICEF sobre IA y niñez (2025), que pide priorizar la equidad, la privacidad y la explicación a niños y familias.

| Principio | Qué significa en este proyecto | Evidencia | Estado |
|---|---|---|---|
| Beneficio y no hacer daño (proporcionalidad) | El contacto es para ofrecer ayuda. Se usa la herramienta más simple que resuelve el problema | Uso permitido y prohibido; la regla D2 se eligió sobre modelos más complejos | Implementado |
| Equidad y no discriminación | Ningún grupo debe quedar sistemáticamente fuera del apoyo | Métricas por sede, beca y subnivel (sección 5); la nacionalidad nunca es predictor | Parcial: pocos eventos por grupo |
| Privacidad y protección de datos | Seudónimos, y ningún dato real en el repositorio ni en la app pública | Sección 6 | Medidas implementadas; pendientes de LEMAS en la sección 11 |
| Transparencia y explicabilidad | Cualquier persona puede entender por qué una familia está en la lista | Regla D2 pública; columna *motivo* en la app; SHAP y permutación | Implementado hacia el personal; pendiente hacia las familias |
| Supervisión y decisión humana | La lista no ejecuta ninguna acción | Secretaría decide; k es editable | Implementado |
| Responsabilidad y rendición de cuentas | Queda registro de quién decidió qué y por qué | Registro de decisiones D01–D53, sistema congelado con SHA-256, actas | Implementado en el desarrollo; gobernanza propuesta para la operación |
| Seguridad y robustez | El sistema se probó fuera de muestra y falla de forma controlada | Prueba única en C5 con IC 95 %; 179 pruebas automáticas; la app pública rechaza archivos sin la marca de datos sintéticos | Implementado |
| Sensibilización | El personal sabe leer la lista y conoce sus límites | Manual de usuario, Excel de práctica ficticio, pestaña *Acerca de* | Parcial: falta la validación con usuarios |

## 3. Dilemas éticos del proyecto

No todas las decisiones tenían una respuesta correcta. Varios de estos dilemas son los que la literatura sobre analítica del aprendizaje describe desde hace años: consentimiento, etiquetado y uso de los datos para un fin distinto del original (Slade y Prinsloo, 2013). Estos fueron los nuestros y lo que decidimos.

| Dilema | Tensión | Qué decidimos | Costo que aceptamos |
|---|---|---|---|
| **Usar o no las señales de pago** | Son las únicas señales que mostraron capacidad de ordenar a las familias (sección 7), pero reflejan la situación económica | Usarlas, con el uso limitado a contacto de apoyo y la decisión en manos de una persona | Las familias con atrasos de pago aparecen más en la lista |
| **Privacidad frente a utilidad** | Secretaría necesita nombres y teléfonos para llamar; el modelo no | El modelo solo ve seudónimos. Los nombres aparecen únicamente en el modo institucional, en un equipo de LEMAS, y la app no los guarda (D45) | Más personas pueden ver datos personales que si solo reidentificara el custodio, y la lista con nombres se puede descargar |
| **A cuántas familias llamar** | Con k contactos, priorizar a unas familias es dejar de priorizar a otras. Pero k fue una decisión (el doble del promedio histórico de casos), no una medida de lo que el personal puede hacer | k proporcional al historial de cada sede y editable; Secretaría mantiene su atención habitual a todas | La lista alcanza cerca del 30 % de los casos. Como tiene más cupos que casos, el 70 % restante es un límite de señal y no de capacidad ([alcance_lista.md](alcance_lista.md)) |
| **Informar a las familias** | Las familias tienen derecho a saber cómo se usan sus datos; el análisis académico se hizo sin consultarlas | Reconocerlo como limitación y dejar listo un texto de aviso (anexo A) | El estudio académico se hizo solo con autorización institucional |
| **Cédula genérica de familias extranjeras** | Marcar esos casos mejoraría la calidad de los datos, pero usarlo como predictor equivale a usar la nacionalidad | Se trata como problema de calidad de datos; nunca es predictor (D33) | No se pudo evaluar la equidad de ese grupo en C5 |
| **Etiquetar a una familia** | Una etiqueta de "riesgo" puede estigmatizar y condicionar el trato | La app habla de *prioridad de contacto*, la lista es confidencial y cada familia lleva su motivo | La etiqueta sigue existiendo para quien usa la lista. Para no añadirle un número, las listas no muestran la probabilidad estimada (D49) |
| **Exactitud frente a explicabilidad** | Un modelo complejo podría acertar más y explicarse peor | Aquí no hubo conflicto: la regla más simple fue también la más eficaz | Ninguno. Si en el futuro un modelo supera a la regla, habrá que volver a decidir |
| **Mostrar un resultado modesto** | Decir que la IA no ganó resta brillo al proyecto | Informarlo en el README, la app y el pitch | — |

## 4. Sesgos identificados y cómo se abordaron

| Sesgo o riesgo | Evidencia | A quién puede perjudicar | Mitigación |
|---|---|---|---|
| **Proxy socioeconómico:** los atrasos en pensiones reflejan la capacidad de pago | La regla D2 se apoya en señales de pago | Familias con menos recursos, si la lista se usara para presionar | Uso exclusivo para contacto de **apoyo**: ofrecer planes de pago y no presionar. La decisión final es humana |
| **Menor detección en familias becadas** | Recall de D2 en C5: 0,18 en becadas frente a 0,32 en no becadas (11 eventos; diferencia incierta) | Familias becadas, que recibirían menos contactos de apoyo | Advertencia en la app y en el manual; se recomienda revisar también a becadas con atrasos; se vigilará con nuevas cohortes |
| **Diferencias entre sedes** | Mucho Lote 1 tiene más familias seleccionadas (18 %) que Mucho Lote 2 (10 %) | Familias de la sede con menos contactos | k proporcional al historial de cada sede y editable; la precisión es 0,12 y 0,17 |
| **Familias extranjeras con cédula genérica** | Un representante figuraba con 39 estudiantes | Familias extranjeras | Cada estudiante cuenta como un contacto individual (D29). La marca `representante_atipico` **no es predictor** (D33). En C5 no hubo casos para evaluar |
| **Cambios entre cohortes** | C1 mostró diferencias en promedio, sede y conducta | Todos: un modelo entrenado con un año atípico se equivoca más | Auditoría de comparabilidad; C1 excluida con regla registrada de antemano (D14) |
| **Sesgo histórico** | La regla aprende de lo que pasó: si antes se atendió menos a un grupo, sus señales pesan distinto | Grupos poco representados | Revalidación anual con la cohorte nueva y revisión por grupos |
| **Sesgo de confirmación del equipo** | Riesgo de probar modelos hasta que uno gane | La validez del resultado | Un único intento adicional registrado antes de verlo (D39); C5 evaluada una sola vez con el sistema congelado (D38) |

Son tipos de sesgo descritos en educación (Baker y Hawn, 2022): el proxy socioeconómico es un sesgo de medición (una variable que mide otra cosa), la menor detección en becadas puede ser de representación (pocos casos de un grupo) y aprender de decisiones pasadas es un sesgo histórico.

**Sesgos del conjunto de datos.** Todos los registros son de una sola institución privada con dos sedes en Guayaquil, y solo incluyen a estudiantes con reserva aprobada (sesgo de selección). Los resultados no se pueden trasladar a otros colegios ni a estudiantes nuevos.

**Sesgo de la etiqueta.** El evento es *no tener la matrícula pagada al 30 de abril*. Incluye a familias que se matriculan después de esa fecha (D03), y la señal más fuerte de la regla es haber pagado tarde el año anterior. Al desglosar el evento en C2 a C4 ([alcance_lista.md](alcance_lista.md), sección 6.1), el 86 % de los casos son familias que no registran ningún pago, el 9 % paga por unos estudiantes y no por otros y el 5 % paga todo después del 30 de abril. La regla encuentra al 43 % de los dos últimos grupos y solo al 24 % del primero: detecta mejor el retraso que la salida, aunque la mayoría de sus aciertos (53 de 69) son familias sin ningún pago. «No registra ningún pago» tampoco equivale a «se fue», y por eso hablamos de *no pagar la matrícula en plazo* y no de abandono. No se usan variables demográficas sensibles (etnia, religión, discapacidad, salud) ni la nacionalidad.

## 5. Equidad

**Qué medimos.** Para cada grupo comparamos tres valores de la lista D2 en la prueba final (C5, por representante): el porcentaje de familias seleccionadas, la Precision@k (de las familias listadas, cuántas no se matricularon) y el Recall@k (de las que no se matricularon, cuántas estaban en la lista). El Recall@k por grupo es la medida más importante aquí, porque equivale a la **igualdad de oportunidades**: que una familia que necesita apoyo tenga la misma probabilidad de recibir la llamada sin importar su grupo.

| Grupo | Familias | Eventos | % seleccionadas | Precision@k | Recall@k |
|---|---|---|---|---|---|
| Mucho Lote 1 | 640 | 44 | 18,4 % | 0,12 | 0,32 |
| Mucho Lote 2 | 453 | 30 | 10,4 % | 0,17 | 0,27 |
| Sin beca | 930 | 63 | 15,9 % | 0,14 | 0,32 |
| Con beca | 163 | 11 | 10,4 % | 0,12 | **0,18** |
| Educación General Básica | 743 | 55 | 16,4 % | 0,12 | 0,27 |
| Inicial | 115 | oculto | 8,7 % | — | — |
| Preparatoria | 113 | 12 | 11,5 % | 0,38 | 0,42 |
| Bachillerato | 122 | <5 | 16,4 % | — | — |

Fuente: `results/metrics/equidad_C5_real.csv`. Las celdas con menos de 5 casos no se muestran. La de Inicial se oculta además para que la de Bachillerato no pueda deducirse restando del total (supresión complementaria, D48). La evaluación sigue el enfoque de comparar métricas por grupo que propone Fairlearn; no usamos la librería, sino `src/modeling.py`.

**Dos medidas resumen, becadas frente a no becadas.**
- **Razón de selección** (paridad demográfica): 10,4 % frente a 15,9 %, es decir 0,66. Como orientación, suele considerarse una alerta un valor menor que 0,80.
- **Diferencia de Recall@k** (igualdad de oportunidades): 0,18 frente a 0,32, una diferencia de 0,14. En casos: 2 de 11 frente a 20 de 63.

**Lectura.** El sistema no trata igual a todos los grupos: las familias becadas reciben menos contactos de los que les corresponderían. Con 11 eventos no podemos decir si la diferencia es real o producto del azar (no calculamos intervalos por grupo), y por eso la informamos como una alerta y no como una conclusión.

Hay una tensión que no resolvimos. La regla selecciona más a las familias con atrasos de pago, pero selecciona menos a las becadas. Una explicación posible es que quien tiene beca paga menos y acumula menos atrasos, de modo que la regla no ve su dificultad. No lo comprobamos.

**Estrategias aplicadas.**
- La regla D2 no usa la beca ni la sede, y la nacionalidad no se usa en ninguna parte del sistema.
- k separado por sede, para que una sede no absorba los contactos de la otra.
- Recomendación de revisar a las familias becadas con atrasos aunque no estén en la lista. Hoy depende de Secretaría, que conoce qué familias tienen beca: la app no las marca ni muestra a las familias no listadas.
- Revisión de estas mismas métricas cada mayo, acumulando cohortes para ganar eventos por grupo.

No aplicamos una corrección estadística de equidad (por ejemplo, cupos por grupo), porque con tan pocos eventos por grupo estaríamos ajustando ruido.

## 6. Privacidad y protección de datos

**¿Se usan datos personales o sensibles?** Sí: datos personales de niñas, niños y adolescentes, que la ley ecuatoriana trata como **categoría especial**, y de sus representantes. No se usan datos sensibles en el sentido legal (salud, etnia, religión, condición migratoria), ni motivos del DECE, ni texto libre.

| Riesgo | Medida implementada | Dónde |
|---|---|---|
| Exposición de identidades | Seudonimización **HMAC-SHA256** de las cédulas del estudiante y del representante, con clave custodiada por LEMAS. Se eliminan nombres, código interno, saldo, deuda y estado de pago | `tools/seudonimizar.py`, `00a` |
| Reidentificación por terceros | Solo quien tiene la clave y el Excel original puede revertir los seudónimos. La base seudonimizada conserva campos que, combinados, podrían identificar a alguien para quien conozca los registros originales (paralelo, promedio, fecha de pago): por eso nunca se publica | `seudonimizar.py reidentificar`, pestaña *Lista con nombres* |
| Publicación accidental | `.gitignore` bloquea Excel, `base_seud.csv`, claves, actas, perfiles y modelos reales; el repositorio contiene solo código, datos **sintéticos** y agregados | `.gitignore` |
| Inferencia a partir de agregados | Supresión de celdas con **menos de 5 casos** en tablas y figuras; con datos reales, el gráfico SHAP por estudiante no se muestra | `privacidad.min_celda`, cuadernos |
| Datos reales en un servidor público | **Aplicación en dos modos (D42):** la versión pública rechaza los archivos con columnas identificadoras y los que no llevan la marca de datos sintéticos, y no tiene carga de Excel ni pantalla con nombres. Es una barrera contra errores, no contra un uso deliberado | `src/inferencia.py` |
| Datos personales en la app institucional (D45) | El Excel y la clave se procesan **en memoria y en el mismo equipo**; el arranque limita la app a `localhost`; se verifica que la base de trabajo no tenga nombres ni cédulas; los nombres se muestran solo tras confirmar que se es personal autorizado; botón para borrar los datos de la sesión | `src/institucional.py`, `iniciar_lemas.bat` |
| Uso de una clave equivocada o nueva | La clave se sube en cada uso; la app muestra su huella para compararla con la de años anteriores y solo ofrece crear una clave si LEMAS confirma que no tiene | `app/app.py` |
| Copias de la lista con nombres | El archivo descargado contiene datos personales: el manual indica guardarlo solo en carpetas autorizadas y eliminarlo al terminar la campaña; `.gitignore` bloquea esos archivos | Manual de usuario |
| Retención | Las copias de trabajo en Colab se borran al terminar cada sesión; el modelo entrenado con datos reales no se publica; se propone eliminarlo 30 días después de la aceptación académica | Práctica del equipo; v5 5.7 |
| Minimización | Solo se usan variables conocidas en t0. La regla necesita tres; el modelo de apoyo usa además promedio, conducta, subnivel y si el estudiante es nuevo (ver la sección 14, punto 9) | `config.yaml`, v5 5.6 |

Estas medidas aplican el principio de **protección de datos desde el diseño y por defecto**. En la tabla de equidad se aplica además supresión complementaria: cuando solo queda una celda oculta, se oculta una segunda para que no pueda deducirse por diferencia. La proyección se publica por subnivel y por sede, sin su cruce, por la misma razón (sección 14, punto 10). El marco legal y lo que falta para cumplirlo por completo están en la sección 11.

## 7. Transparencia y explicabilidad

**¿El sistema es interpretable?** Sí. La priorización final es una regla que cabe en una frase: 100 puntos por haber pagado tarde la matrícula anterior, 20 por reserva extraordinaria y un punto por cada pensión atrasada. Se ordena de mayor a menor. No hay una caja negra en la decisión.

Los empates dentro de un mismo puntaje se resuelven al azar con semilla fija, con la misma función en la validación y en la aplicación (D48). La probabilidad del modelo no interviene en el orden ni aparece en las listas (D49); solo se muestra en el formulario individual, junto a la tasa histórica.

| Para quién | Qué se le explica | Cómo |
|---|---|---|
| Secretaría y Admisiones | Por qué cada familia está en la lista | Columna *motivo* en la app y en la descarga |
| Dirección | Qué tan bien funciona y qué no puede hacer | Pestaña *Acerca de*, resultados con IC 95 %, este documento |
| Evaluadores y otros desarrolladores | Cómo se construyó y validó | Código abierto, cuadernos ejecutables, registro de decisiones, [ficha del modelo](ficha_modelo.md) |
| Familias | Para qué se usan sus datos y qué pueden pedir | **Pendiente:** texto de aviso propuesto en el anexo A |

**Técnicas de explicabilidad aplicadas a los modelos candidatos.**
- **Importancia por permutación** en la logística híbrida (caída de PR-AUC en C4): reserva extraordinaria 0,014 y atrasos en pensiones 0,011. La puntualidad del pago anterior (0,008) y el subnivel (0,004) tienen una variación tan grande como su efecto, así que no son concluyentes. Este modelo no recibe la sede, la beca ni los hermanos, por lo que la permutación no dice nada de ellos.
- **SHAP** en la logística híbrida: el promedio, ser estudiante nuevo y el subnivel son lo que más mueve la probabilidad, pero la permutación muestra que no mejoran el orden.
- **Restricción de monotonía** en el gradient boosting: más atrasos nunca reducen el riesgo estimado.

La regla D2 se eligió por su Lift@k en C4, no por estos análisis. Lo que aportó la explicabilidad fue una comprobación: la permutación es coherente con la regla, y SHAP mostró que las variables académicas mueven la probabilidad sin mejorar el orden.

**Lo que la explicación no dice.** La regla describe una asociación, no una causa. Que una familia haya pagado tarde no explica por qué podría no matricularse, y la lista no debe leerse como un diagnóstico de la familia.

## 8. Impacto social

### 8.1 Mapa de actores

| Actor | Cómo le afecta | Beneficio posible | Riesgo posible | Participación en el proyecto |
|---|---|---|---|---|
| Estudiantes | Indirectamente: su continuidad depende de la decisión de la familia | Menos interrupciones de su escolaridad | Ser tratados distinto si la etiqueta se filtra a docentes | Ninguna (menores; sus datos van seudonimizados) |
| Familias y representantes | Reciben o no una llamada de apoyo | Información y facilidades a tiempo | Sentirse vigiladas o presionadas; estigma económico | Ninguna todavía: limitación reconocida |
| Secretaría y Admisiones | Usan la lista para organizar su trabajo | Enfocar 69 días y 10 personas donde más sirve | Confiar de más en la lista y descuidar al resto | Definieron k y el proceso; falta la validación de uso (anexo E del documento técnico) |
| Dirección | Decide si el sistema se usa y responde por él | Planificación de cupos y personal | Tomar decisiones sobre una proyección que no mejora a la tasa histórica | Autorizó el estudio |
| Custodio de datos | Guarda la clave y aprueba cada extracción | Proceso ordenado y trazable | Concentrar un riesgo: si la clave se pierde o se filtra | Ejecuta la seudonimización |
| Docentes | No usan el sistema | Paralelos más estables | Ninguno directo, si la lista no circula | Ninguna |
| Equipo desarrollador | Construye y mantiene | Aprendizaje y resultado académico | Sesgo de confirmación | Autores |
| Autoridad de protección de datos (SPDP) | Supervisa el tratamiento | — | — | Ninguna |
| Otros colegios | Podrían reutilizar el código abierto | Punto de partida documentado | Usarlo sin revalidar con sus datos | Ninguna |

**Quién se beneficia y quién podría salir perjudicado.** Se benefician sobre todo la institución (planificación) y las familias que reciben un contacto oportuno. Los grupos que podrían salir perjudicados son las familias con dificultades económicas, si la lista se usara para cobrar, y las familias becadas, si la menor detección se confirma.

### 8.2 Dimensiones del impacto

| Dimensión | Impacto positivo | Impacto negativo posible | Salvaguarda |
|---|---|---|---|
| Individual y familiar | Contacto **oportuno** antes de perder el cupo | Estigma; contacto percibido como presión de cobro | Lista confidencial; protocolo de contacto con enfoque de apoyo (manual de usuario) |
| Educativa | Continuidad del estudiante en su colegio | Ninguno directo: el sistema no interviene en lo académico | La prioridad sale de señales administrativas; las notas solo intervienen para desempatar |
| Institucional | Mejor planificación de cupos y docentes | Confianza excesiva en "la IA" | La app explica que los modelos no superaron a la regla y muestra la incertidumbre |
| Laboral | El personal enfoca su esfuerzo; no reemplaza puestos | Que el número de contactos se use para evaluar al personal | La lista es un apoyo; no mide el desempeño de nadie |
| Económica | Ingresos más previsibles para sostener el servicio | Que el incentivo económico desplace al de apoyo | Uso prohibido para cobranza (sección 1) |
| Social | Un ejemplo de IA modesta, explicable y con datos protegidos | Normalizar el perfilado de familias | Finalidad limitada y revisión anual por Dirección |

**Lo que aprendimos de otros casos.** El sistema de alerta temprana de deserción de Wisconsin (DEWS) es el antecedente más estudiado. Un análisis de casi una década de datos concluyó que el sistema ordenaba bien a los estudiantes, pero no pudo demostrar que mejorara la graduación, y que la información del entorno escolar predecía casi igual que la individual (Perdomo et al., 2025). Una investigación periodística mostró además que daba más falsas alarmas con estudiantes negros e hispanos y que usaba la raza como variable (Feathers, 2023). De ahí tomamos cuatro lecciones: no usar variables demográficas, tratar la etiqueta como confidencial, capacitar a quien usa la lista y **no confundir predecir con ayudar**. Por eso reconocemos como limitación que todavía no medimos si la llamada cambia la decisión de la familia.

## 9. Responsabilidad y rendición de cuentas

### 9.1 ¿Quién responde si el sistema falla?

El sistema no decide: propone un orden. La responsabilidad de lo que se hace con ese orden es de las personas y de la institución.

| Tipo de falla | Consecuencia | Quién responde | Qué se hace |
|---|---|---|---|
| Una familia que no se matricula no estaba en la lista | Ninguna adicional: recibe la atención habitual | Secretaría | La lista no reemplaza la atención a todas las familias |
| Una familia listada sí pensaba matricularse | Una llamada innecesaria | Secretaría | Contacto breve y de apoyo; se registra el resultado |
| La regla deja de ordenar mejor que el azar | Esfuerzo mal dirigido | Equipo técnico y Dirección | Revalidación anual; se suspende si no supera al azar (9.4) |
| Error técnico (archivo mal leído, clave equivocada) | Lista incorrecta o seudónimos que no coinciden | Equipo técnico | Verificaciones al cargar, huella de la clave, 179 pruebas automáticas |
| Uso indebido (cobro, exclusión) | Daño a la familia y a la confianza | Dirección | Uso prohibido documentado; revisión anual por Dirección |
| Fuga de datos personales | Daño a los titulares | LEMAS como responsable del tratamiento; custodio | Protocolo de incidentes (9.5) |

### 9.2 Cadena de responsabilidad

| Etapa | Responsable | Qué decide | Registro que queda |
|---|---|---|---|
| 1. Datos de origen | Secretaría de LEMAS | Calidad de lo que se registra | Excel institucional |
| 2. Extracción y seudonimización | Custodio de datos | Qué sale y con qué clave | Acta con huella SHA-256 del archivo; la app muestra además la huella de la clave |
| 3. Desarrollo y validación | Equipo técnico (Guillermo Granizo y José Ulloa) | Variables, protocolo, modelo o regla | Registro de decisiones D01–D53; código y pruebas; sistema congelado con SHA-256 |
| 4. Aprobación de uso | Dirección | Si el sistema se usa y con qué límites | Autorización del estudio (30-sep-2026). La del uso operativo está pendiente |
| 5. Generación de la lista | Secretaría, con el custodio | Ciclo, k por sede | Bitácora con fecha, k y quién la generó (propuesto: hoy el archivo no lo registra) |
| 6. Contacto | Secretaría y Admisiones | A quién llamar y qué ofrecer | Resultado del contacto (propuesto) |
| 7. Revisión | Dirección y equipo técnico | Si se mantiene, se ajusta o se retira | Informe anual de resultados y equidad (propuesto) |

En los términos de la norma ecuatoriana sobre IA y datos personales (sección 11), LEMAS es el **responsable del tratamiento** e **implementador** del sistema, y el equipo es su **desarrollador**. Las plataformas públicas (GitHub y Streamlit Community Cloud) solo reciben código y datos sintéticos.

**Separación de funciones.** Un integrante del equipo trabaja en LEMAS y tuvo a su cargo los datos reales. Eso facilitó el acceso y el conocimiento del proceso, pero concentra funciones. Quien desarrolla o mantiene el sistema no debería ser la única persona que custodia la clave ni la única que revisa los resultados: la revisión anual corresponde a Dirección, y LEMAS debe designar por escrito al custodio.

### 9.3 Mecanismos de rendición de cuentas

**Ya existen:**
- Registro de decisiones con fecha y motivo (`docs/planificacion.md`).
- Sistema congelado con huella SHA-256 antes de abrir la prueba final, que se hizo una sola vez.
- Acta de extracción en cada seudonimización; la app institucional muestra la huella de la clave.
- Código abierto, resultados agregados publicados y cuadernos que cualquiera puede ejecutar.
- Pruebas automáticas e integración continua en cada cambio.
- Motivo visible por cada familia de la lista.
- [Ficha del modelo](ficha_modelo.md) con uso previsto, métricas, grupos y límites, y [hoja de datos](hoja_de_datos.md) con el origen, la composición y los límites del conjunto de datos.
- Compromiso ético del equipo, que los dos integrantes firman en el documento entregado ([impacto_social_responsabilidad.md](impacto_social_responsabilidad.md), parte 8).

**Propuestos para la operación en LEMAS:**
- Bitácora por campaña: quién generó la lista, cuándo, con qué k y cuál fue el resultado de cada contacto.
- Canal para que una familia pregunte por qué fue contactada, pida corregir sus datos o presente un reclamo. La ley reconoce esos derechos (explicación, observaciones, criterios, datos usados e impugnación) frente a decisiones automatizadas con efectos jurídicos. Esta lista no los produce, pero ofrecerlos igual es una buena práctica.
- Informe anual a Dirección con resultados y equidad.

### 9.4 Plan de monitoreo y actualización (propuesto)

| Qué se vigila | Cuándo | Señal de alerta | Acción |
|---|---|---|---|
| Lift@k por familia en la cohorte que cierra, con su IC 95 % | Cada mayo | Menor que 1,20 (meta del proyecto) | Revalidar la regla antes de la siguiente campaña |
| | | El intervalo incluye el 1 dos años seguidos | Suspender la priorización y volver al contacto habitual |
| Recall@k por beca, sede y subnivel | Cada mayo, acumulando cohortes | La diferencia entre grupos se mantiene al acumular eventos | Ajustar la regla o reservar contactos para el grupo afectado |
| Cambios de política (cobros, reservas, becas) | Cuando ocurran | Cualquier cambio en lo que mide la regla | Revalidar antes de usarla |
| Calidad de los datos | En cada carga | Hojas o columnas faltantes, formatos nuevos | La app avisa; se corrige el Excel de origen |
| Quejas de familias por el contacto | Durante la campaña | Cualquiera | Revisar el protocolo de contacto |
| Incidentes de privacidad | Siempre | Cualquiera | Protocolo de incidentes |
| Efecto del contacto | Tras dos campañas | — | Piloto controlado para medir si la llamada cambia la decisión |

**Una advertencia sobre este plan.** Cuando la lista se use de verdad, las llamadas pueden cambiar el resultado: si funcionan, las familias contactadas se matriculan y el Lift medido baja aunque el sistema sea útil. Para poder medirlo, proponemos reservar desde la primera campaña una parte pequeña de los contactos para familias elegidas al azar. Sirve de grupo de comparación y, además, da una oportunidad a familias que la regla no ve. Con unos 74 eventos por año, el Lift de un solo ciclo es incierto; por eso el criterio de suspensión mira dos años.

El modelo calibrado se reentrena solo con cohortes de resultado cerrado. Cada versión se etiqueta en el repositorio.

### 9.5 Respuesta a incidentes

Cualquier fallo, técnico o de uso, se atiende en cinco pasos.

| Paso | Qué se hace | Incidente del 3-oct-2026 (error en la aplicación pública) |
|---|---|---|
| 1. Detección | Pruebas automáticas en cada cambio, avisos de la aplicación al cargar datos, quejas de familias y revisión de mayo | El Product Owner vio un error al generar la lista después de una actualización |
| 2. Respuesta inmediata | Avisar al custodio y a Dirección; contener; volver al contacto habitual mientras se resuelve | Se reinició la aplicación. No había datos personales: la versión pública solo usa datos sintéticos |
| 3. Investigación | Qué falló, qué datos y cuántas personas están afectados; reproducir el fallo con una prueba | La plataforma ejecutó el programa nuevo con un módulo antiguo que seguía en memoria |
| 4. Corrección | Reparar y, si alguien resultó afectado, explicárselo | La aplicación ahora detecta el código que cambió y lo vuelve a cargar |
| 5. Prevención | Dejar una prueba que reproduzca el fallo y registrar lo ocurrido | Dos pruebas nuevas; registrado como D51 |

**Si el incidente afecta a datos personales:**

1. Avisar de inmediato al custodio y a Dirección.
2. Contener: retirar el archivo o el acceso y, si la clave se expuso, dejar de usarla y generar otra (los seudónimos anteriores dejan de servir).
3. Evaluar qué datos y cuántas personas están afectados.
4. Notificar: la ley fija un término de cinco días para avisar a la autoridad (LOPDP, art. 43) y de tres días para avisar a los titulares cuando hay riesgo para sus derechos (art. 46). LEMAS debe confirmar con su asesor el procedimiento y las excepciones.
5. Registrar lo ocurrido y lo que se cambió para que no se repita.

### 9.6 Marcos de responsabilidad que usamos como guía

| Marco | Qué propone | Cómo lo aplicamos |
|---|---|---|
| NIST AI RMF 1.0 (2023) | Cuatro funciones: gobernar, mapear, medir y gestionar los riesgos | **Gobernar:** roles y cadena de responsabilidad (9.2). **Mapear:** uso permitido, actores e impactos (secciones 1 y 8). **Medir:** prueba única con IC, equidad por grupo, pruebas automáticas. **Gestionar:** monitoreo, umbral de suspensión y protocolo de incidentes (9.4 y 9.5) |
| Fichas de modelo (Mitchell et al., 2019) | Documentar uso previsto, métricas, grupos y límites | [`docs/ficha_modelo.md`](ficha_modelo.md) |
| Hojas de datos (Gebru et al., 2021) | Documentar origen, composición, recolección y usos del conjunto de datos | [`docs/hoja_de_datos.md`](hoja_de_datos.md) |
| Evaluación de equidad por grupos (enfoque de Fairlearn) | Comparar las métricas entre grupos antes de usar un sistema | Sección 5, con código propio |
| ISO/IEC 42001:2023 | Sistema de gestión de IA para organizaciones | No se implementó. Es la referencia si LEMAS decide formalizar la gestión de sus sistemas de IA |

## 10. Uso dual y mal uso

El sistema no tiene un uso malicioso evidente fuera de la institución, pero dentro de ella la misma lista que sirve para ayudar podría servir para lo contrario.

| Mal uso posible | Daño | Salvaguarda técnica | Salvaguarda organizativa |
|---|---|---|---|
| **Cobranza:** usar la lista para presionar pagos | Estigma y presión sobre familias con dificultades | La lista muestra el motivo (por ejemplo, pago tardío) pero ningún monto; saldo y deuda se eliminan al seudonimizar | Uso prohibido; protocolo de contacto de apoyo |
| **Seguimiento como lista de morosos:** tratar a las familias que siguen sin pagar a mitad de campaña como deudoras (D51) | Presión sobre familias que están dentro del plazo | El listado no muestra montos ni saldos y advierte que no es una predicción; los nombres piden la misma confirmación | El plazo vence el 30 de abril: no hay mora. Mismo uso prohibido y mismo protocolo de apoyo |
| **Exclusión:** negar o condicionar cupos, reservas o becas | Afecta el acceso a la educación | La app no tiene ninguna función de decisión sobre cupos | Uso prohibido; decisión humana; revisión por Dirección |
| **Perfilado:** cruzar la lista con otros datos o compartirla con terceros | Pérdida de privacidad | Seudónimos; nombres solo en el equipo de LEMAS | Finalidad limitada; la lista con nombres se elimina al cerrar la campaña |
| **Reidentificación** de la base seudonimizada por un tercero | Exposición de datos de menores | HMAC con clave secreta; la base real nunca se publica | La clave la guarda el custodio y no se envía por correo |
| **Datos reales en la app pública** | Datos de menores en un servidor externo | La app pública rechaza archivos con columnas identificadoras o sin la marca de datos sintéticos | Advertencias en la app y el manual |
| **Reutilización sin revalidar** en otro colegio u otro proceso | Decisiones basadas en una regla que no aplica | El repositorio solo trae datos sintéticos | Límites de uso en el README y en la ficha del modelo |
| **Evaluar al personal** por el número de contactos o conversiones | Incentivos para presionar a las familias | — | La lista no es un indicador de desempeño |

**Límites de uso.** El sistema solo es válido para estudiantes de LEMAS con reserva aprobada al 20 de febrero. No sirve para estudiantes nuevos, reservas pendientes, abandono durante el año, otros colegios ni decisiones de admisión, becas o cobro.

Como referencia, la Ley de IA de la Unión Europea clasifica como de **alto riesgo** los sistemas que determinan el acceso o la admisión a instituciones educativas. A nuestro juicio, este sistema quedaría fuera de esa categoría porque no decide admisiones; si se usara para negar cupos entraría en ella. Es una razón más para mantener ese uso prohibido.

## 11. Regulación y cumplimiento

**Normas que aplican.** El responsable del tratamiento y los titulares están en Ecuador, así que rige la normativa ecuatoriana. El RGPD europeo y la CCPA de California no son directamente aplicables; los usamos como referencia, igual que la Ley de IA de la Unión Europea.

| Norma | Qué exige en lo que nos toca |
|---|---|
| Constitución del Ecuador, arts. 44 y 66.19 | Interés superior de niñas, niños y adolescentes; derecho a la protección de datos personales |
| Código de la Niñez y Adolescencia, art. 11 | Interés superior del niño en toda decisión que le afecte |
| LOPDP (2021), art. 10 | Principios: finalidad, minimización, proporcionalidad, transparencia, seguridad, conservación y responsabilidad proactiva, entre otros |
| LOPDP, arts. 7 y 21 | Base legítima del tratamiento. Según nuestra lectura, el art. 21 pide para los datos de niñas, niños y adolescentes la **autorización expresa del titular o de su representante legal** (los adolescentes pueden darla desde los 15 años), salvo que el tratamiento responda a un interés público esencial |
| LOPDP, art. 12 | Derecho de las familias a ser informadas de los fines y del tratamiento |
| LOPDP, art. 20 | Derecho a no ser objeto de decisiones basadas **única o parcialmente** en valoraciones automatizadas que produzcan efectos jurídicos o afecten derechos fundamentales, y a pedir explicación e impugnar. No aplica si la decisión no conlleva impactos graves |
| LOPDP, arts. 25, 37 y 39 | Categorías especiales de datos; medidas de seguridad; protección desde el diseño |
| LOPDP, arts. 42, 43 y 46 | Evaluación de impacto **antes de iniciar** un tratamiento de alto riesgo; notificación de vulneraciones |
| Reglamento General de la LOPDP (2023) | Desarrollo de las obligaciones anteriores |
| Resolución SPDP-SPD-2025-0030-R (2025) | Reglas para seudonimizar, anonimizar, bloquear y eliminar datos personales |
| Resolución SPDP-SPD-2026-0009-R (febrero de 2026) | Norma sobre protección de datos en sistemas de IA: información clara al titular, gestión de riesgos y evaluación de impacto previa, registro de las actividades de tratamiento con IA, medidas de seguridad y auditorías según el riesgo |

**Comparación con el RGPD.** La ley ecuatoriana sigue una estructura parecida: bases de licitud (RGPD art. 6; LOPDP art. 7), consentimiento cuando los titulares son menores (art. 8; art. 21), decisiones automatizadas (art. 22; art. 20) y evaluación de impacto (art. 35; art. 42). Una diferencia que nos afecta: el RGPD habla de decisiones basadas *únicamente* en el tratamiento automatizado, y la ley ecuatoriana incluye las basadas *parcialmente* en él.

Ecuador no tiene una ley general de IA: en septiembre de 2026 la Asamblea archivó el proyecto de ley que buscaba regularla, tras el informe de la comisión que lo estudió. Sí existe una estrategia nacional para el uso ético y responsable de la IA (Acuerdo MINTEL-MINTEL-2025-0030, publicado en enero de 2026), que incluye la educación entre sus ámbitos.

**Estado de cumplimiento.**

La columna *Estado* es la valoración del equipo técnico, no una calificación jurídica.

| Requisito | Estado | Detalle |
|---|---|---|
| Finalidad limitada | Implementado | Uso permitido y prohibido por escrito |
| Minimización | Parcial | La regla usa tres variables; el modelo de apoyo usa más (sección 14, punto 9) |
| Seguridad y protección desde el diseño | Implementado | Seudonimización, dos modos, supresión de celdas pequeñas |
| Sin efectos jurídicos ni impactos graves | Implementado | La lista solo ordena contactos de apoyo y no decide cupos, reservas ni becas. Por eso entendemos que queda fuera del art. 20; que decida una persona no basta por sí solo, porque la ley también cubre decisiones *parcialmente* automatizadas |
| Explicación disponible | Implementado hacia el personal | Motivo por familia y regla pública |
| Autorización institucional del estudio | Implementado | 30-sep-2026 |
| **Base legal para datos de menores** | **Por verificar por LEMAS** | No comprobamos que lo que firman los representantes al matricular cubra este análisis. En versiones anteriores de este documento invocamos el interés legítimo; tras leer el art. 21 creemos que no debe darse por suficiente sin que lo confirme el asesor de LEMAS |
| **Información a las familias** | **Pendiente** | Texto propuesto en el anexo A |
| **Evaluación de impacto** | **Pendiente** | La ley la pide antes de iniciar un tratamiento de alto riesgo, y la norma de la SPDP sobre IA la sitúa antes de desarrollar o implementar el sistema. No se hizo antes del estudio académico. Este documento y la tabla de riesgos del documento técnico sirven de insumo |
| **Registro de actividades de tratamiento** | **Pendiente (LEMAS)** | Incluir este tratamiento con IA |
| **Canal de consultas y reclamos** | **Pendiente (LEMAS)** | Sección 9.3 |
| Delegado de protección de datos | Por verificar por LEMAS | Evaluar si corresponde designarlo por tratar datos de categoría especial |
| Procesamiento en la nube | Limitación reconocida | El análisis académico usó Google Colab, fuera del Ecuador, con la base seudonimizada. LEMAS debe revisar si eso cuenta como transferencia internacional (sección 14, punto 6) |

## 12. Consideraciones prácticas de implementación

Lo que LEMAS tendría que hacer, en orden, para pasar del estudio al uso real.

**Antes de la primera campaña**
1. Confirmar con su asesor la base legal para tratar datos de menores con este fin y, si hace falta, incorporar la autorización en los documentos de matrícula o reserva.
2. Informar a las familias (anexo A) y abrir un canal de consultas y reclamos.
3. Hacer la evaluación de impacto y anotar el tratamiento en su registro de actividades.
4. Designar por escrito al custodio de la clave y a quienes pueden ver la lista con nombres.
5. Capacitar a Secretaría con el Excel de práctica ficticio y el protocolo de contacto.
6. Validar la aplicación con el personal (anexo E del documento técnico).

**En cada campaña (20 de febrero a 30 de abril)**
1. Usar solo el modo institucional, en un equipo de LEMAS.
2. Verificar la huella de la clave y anotar quién generó la lista, cuándo y con qué k.
3. Reservar una parte de los contactos para familias elegidas al azar.
4. Registrar el resultado de cada contacto y cualquier queja.
5. Al terminar, borrar la sesión y eliminar las copias de la lista con nombres.

**Cada mayo**
1. Comparar la lista con las matrículas reales: Lift@k con su intervalo y métricas por grupo.
2. Presentar el informe a Dirección, que decide si el sistema se mantiene, se ajusta o se retira.
3. Revalidar la regla si cambiaron las políticas de cobro, de reservas o de becas.

**Costo y capacidad.** El sistema no requiere servidores ni licencias: corre en un computador de la institución. Lo que sí requiere es tiempo de personas: el custodio, quien llama y quien revisa. Sin ese tiempo las salvaguardas de este documento no se cumplen.

## 13. Honestidad sobre las capacidades
- **No se exageran resultados:** los modelos de aprendizaje automático no superaron a la regla D2 en la prueba final, y así se informa en el README, en la app y en el pitch.
- Las probabilidades individuales **no mejoran a la tasa histórica** (Brier 0,0648 frente a 0,0647): la app lo advierte.
- Las métricas se reportan con **intervalos de confianza** y en una cohorte nunca usada para ajustar.
- El sistema **no predice** estudiantes nuevos, reservas pendientes ni abandono durante el año.
- El Lift de la regla **no es un número fijo**: fue 1,38, 1,49, 1,93 y 1,97 en cuatro cohortes, y en C4 cambia de 1,53 a 1,99 según el sorteo entre familias empatadas (media 1,75). La regla ayuda al inicio de la campaña y deja de hacerlo hacia la cuarta semana ([alcance_lista.md](alcance_lista.md)).

## 14. Limitaciones éticas reconocidas
1. **Las familias no fueron consultadas ni informadas** sobre el uso de sus datos para este análisis. El estudio se hizo con autorización de LEMAS y con datos seudonimizados. Antes de un uso operativo, LEMAS debe informar a las familias y confirmar con su asesor la base legal para tratar datos de menores con este fin.
2. El número de eventos por grupo es pequeño: la equidad por beca, subnivel o nacionalidad no puede afirmarse con certeza.
3. La regla D2 refleja el pasado. Si cambian las políticas de cobro o de reservas, debe revalidarse.
4. **No se midió el efecto del contacto:** no se sabe aún si llamar a una familia cambia su decisión. Predecir bien no garantiza ayudar.
5. Con D45 la aplicación institucional muestra nombres y permite descargar una lista con datos personales. Esto facilita el trabajo de Secretaría, pero amplía el número de personas que pueden verlos: la protección depende de que LEMAS limite quién usa el equipo y quién tiene la clave. Además, como la clave se sube en cada uso, pasa por más manos que si estuviera en un solo equipo.
6. El análisis académico con la base seudonimizada se ejecutó en Google Colab, un servicio en la nube fuera del Ecuador, con autorización de LEMAS. La clave nunca salió de LEMAS, pero unos datos seudonimizados siguen siendo datos personales, y allí se entrenó también el modelo. Los datos con nombres y la clave no salieron de la institución. Para el uso permanente, el modo institucional evita este paso: todo se procesa en un equipo de LEMAS.
7. La voz de las familias y de los estudiantes no estuvo en el diseño. La validación con usuarios prevista incluye solo al personal.
8. No se hizo una evaluación de impacto formal ni una revisión por un comité de ética antes de empezar.
9. **Minimización incompleta.** La regla usa tres variables, pero la aplicación pide también el promedio, la conducta y otros campos para un modelo de apoyo cuyas probabilidades no mejoran a la tasa histórica. Si el modelo sigue sin aportar, lo coherente es retirarlo y pedir solo lo que la regla necesita.
10. **Supresión de celdas pequeñas.** Ocultar una celda no impide deducirla cuando se publican las demás y el total. En la tabla de equidad se oculta una segunda celda para evitarlo (D48). Dos tablas no cumplían la regla hasta el 03-oct-2026 y se corrigieron (D53): la proyección, que por sede y subnivel dejaba ver conteos de 2 a 4 estudiantes al restar elegibles y matrículas, ahora se publica por subnivel y por sede, sin su cruce; y en la exploración del cuaderno de diagnóstico, un grupo de menos de 5 estudiantes se suma a otro en lugar de ocultarse. Los valores anteriores siguen en el historial del repositorio: son conteos dentro de grupos de 44 a 128 estudiantes, sin ningún identificador.
11. **Desempate.** Hasta el 02-oct-2026 la aplicación resolvía los empates con la probabilidad del modelo, que no era el desempate validado. Desde D48 usa el mismo sorteo con semilla fija que dio el Lift@k de 1,97. Tiene un costo: entre familias con el mismo puntaje, quién entra en la lista depende de un sorteo reproducible y no de un criterio.
12. **Probabilidad por familia.** Hasta el 02-oct-2026 las listas mostraban una probabilidad estimada junto a cada familia: un número que no mejora a la tasa histórica y que puede leerse como un juicio. Se retiró (D49). La probabilidad queda solo en el formulario individual y, en forma agregada, en el histograma y la proyección.

## 15. Lista de verificación
- [x] Autorización institucional (30-sep-2026)
- [x] Seudonimización con clave custodiada y acta con huella SHA-256
- [x] Repositorio sin datos reales ni modelos reales
- [x] Supresión de celdas menores a 5
- [x] Variables sensibles excluidas (nacionalidad, DECE, texto libre)
- [x] Análisis de equidad por sede, beca y subnivel (la cédula genérica no se pudo evaluar: no hubo casos en C5)
- [x] Decisión humana obligatoria; la app no actúa sola
- [x] Datos personales solo en el modo institucional, en el mismo equipo y en memoria (D45)
- [x] Explicación por familia (motivo) y regla pública
- [x] Usos prohibidos y límites de uso documentados
- [x] Cadena de responsabilidad y plan de monitoreo definidos
- [x] Ficha del modelo y hoja de datos
- [x] Plan de respuesta a incidentes y compromiso ético del equipo
- [x] Limitaciones comunicadas en la app, el README y el pitch
- [ ] Confirmar la base legal para datos de menores (LEMAS)
- [ ] Informar a las familias (anexo A)
- [ ] Evaluación de impacto y registro del tratamiento (LEMAS)
- [ ] Canal de consultas y reclamos (LEMAS)
- [x] Mismo desempate en la validación y en la aplicación (D48)
- [x] Supresión complementaria en la tabla de equidad (D48)
- [x] Las listas de contacto no muestran una probabilidad por familia (D49)
- [x] Proyección publicada sin el cruce de sede y subnivel, y exploración del cuaderno de diagnóstico sin grupos deducibles (D53)
- [ ] Validación con usuarios y medición del efecto del contacto

## Anexo A. Texto propuesto para informar a las familias

> Borrador para que LEMAS lo revise con su asesor jurídico antes de usarlo. Es un aviso informativo, no reemplaza la autorización que la ley pueda exigir. Los corchetes son datos que debe completar la institución.

**Uso de datos para el acompañamiento en la matrícula.** La Unidad Educativa LEMAS usa datos administrativos que ya constan en la institución (por ejemplo, curso, sede, tipo de reserva, puntualidad de pagos anteriores y promedio) para organizar, entre febrero y abril, las llamadas de acompañamiento a las familias con reserva aprobada. Una regla ordena a qué familias llamar primero; **ninguna decisión se toma de forma automática** y aparecer o no en ese orden no afecta el cupo, la reserva, las becas ni ningún servicio.

No se usan datos de salud, del DECE ni de nacionalidad. Los datos se analizan sin nombres ni cédulas y solo el personal autorizado de Secretaría ve la lista de contactos.

**Responsable:** Unidad Educativa LEMAS, [dirección y contacto]. **Base legal:** [la que confirme el asesor jurídico]. **Conservación:** la lista de contactos se elimina al terminar la campaña, el 30 de abril. **Transferencias:** los datos no se entregan a terceros [confirmar si se usa algún servicio externo].

Usted puede pedir que le expliquemos por qué fue contactado, qué datos se usaron, corregirlos u oponerse a este uso, escribiendo a [correo o ventanilla que defina LEMAS]. También puede presentar un reclamo ante la Superintendencia de Protección de Datos Personales.

## Referencias

**Normativa**
- República del Ecuador. *Ley Orgánica de Protección de Datos Personales*. Registro Oficial, Quinto Suplemento n.º 459, 26 de mayo de 2021.
- República del Ecuador. *Reglamento General de la Ley Orgánica de Protección de Datos Personales*. Decreto Ejecutivo 904, noviembre de 2023.
- Superintendencia de Protección de Datos Personales. *Resolución SPDP-SPD-2025-0030-R*, reglamento para la seudonimización, anonimización, bloqueo y eliminación de datos personales, 7 de agosto de 2025. https://spdp.gob.ec/wp-content/uploads/2025/08/0030-R.pdf
- Superintendencia de Protección de Datos Personales. *Resolución SPDP-SPD-2026-0009-R*, Norma general para la garantía del derecho de protección de datos personales en el uso de sistemas de inteligencia artificial, 12 de febrero de 2026. https://spdp.gob.ec/wp-content/uploads/2026/02/ResolIA.pdf
- Ministerio de Telecomunicaciones y de la Sociedad de la Información. *Estrategia para el Fomento del Desarrollo y Uso Ético y Responsable de la Inteligencia Artificial en el Ecuador*. Acuerdo MINTEL-MINTEL-2025-0030, Registro Oficial, Suplemento n.º 206, 19 de enero de 2026.
- Unión Europea. *Reglamento (UE) 2024/1689* (Ley de Inteligencia Artificial), anexo III, punto 3.

**Marcos de referencia**
- UNESCO (2021). *Recomendación sobre la ética de la inteligencia artificial*. https://www.unesco.org/es/artificial-intelligence/recommendation-ethics
- OCDE (2019, actualizada en 2024). *Recommendation of the Council on Artificial Intelligence*. https://oecd.ai/en/ai-principles
- NIST (2023). *Artificial Intelligence Risk Management Framework (AI RMF 1.0)*. NIST AI 100-1. https://www.nist.gov/itl/ai-risk-management-framework
- ISO/IEC 42001:2023. *Information technology — Artificial intelligence — Management system*.
- UNICEF Innocenti (2025). *Guidance on AI and children 3.0*. https://www.unicef.org/innocenti/reports/policy-guidance-ai-children
- Mitchell, M. et al. (2019). Model cards for model reporting. *Proc. FAT\**, 220–229. https://doi.org/10.1145/3287560.3287596
- Gebru, T. et al. (2021). Datasheets for datasets. *Communications of the ACM*, 64(12), 86–92. https://doi.org/10.1145/3458723
- Weerts, H. et al. (2023). Fairlearn: Assessing and improving fairness of AI systems. *JMLR*, 24(257).

**Estudios y casos**
- Perdomo, J. C., Britton, T., Hardt, M. y Abebe, R. (2025). Difficult lessons on social prediction from Wisconsin public schools. *Proc. ACM FAccT*. https://doi.org/10.1145/3715275.3732175
- Feathers, T. (2023). False alarm: How Wisconsin uses race and income to label students "high risk". *The Markup*. https://themarkup.org/machine-learning/2023/04/27/false-alarm-how-wisconsin-uses-race-and-income-to-label-students-high-risk
- Baker, R. S. y Hawn, A. (2022). Algorithmic bias in education. *International Journal of Artificial Intelligence in Education*, 32, 1052–1092. https://doi.org/10.1007/s40593-021-00285-9
- Slade, S. y Prinsloo, P. (2013). Learning analytics: Ethical issues and dilemmas. *American Behavioral Scientist*, 57(10), 1510–1529. https://doi.org/10.1177/0002764213479366
