# Hoja de datos del conjunto de datos

Documenta el origen, la composición y los límites de los datos del proyecto, con las preguntas de *Datasheets for Datasets* (Gebru et al., 2021). Complementa la [ficha del modelo](ficha_modelo.md). El detalle técnico está en [`data/README.md`](../data/README.md) y en [analisis_datos.md](analisis_datos.md).

Hay dos conjuntos: el **real**, que nunca sale de LEMAS con nombres ni se publica, y el **sintético**, que es el único que contiene este repositorio.

## 1. Motivación

| Pregunta | Respuesta |
|---|---|
| ¿Para qué se creó? | Los registros son administrativos: LEMAS los lleva para gestionar reservas, matrículas, notas y pagos. No se crearon para investigar. Este proyecto les da un **uso secundario**: ordenar a qué familias con reserva aprobada ofrecer primero una llamada de apoyo |
| ¿Quién lo creó? | Secretaría y Administración de la Unidad Educativa LEMAS (Guayaquil). El equipo del proyecto (Guillermo Granizo y José Ulloa) preparó la versión seudonimizada y la sintética |
| ¿Quién lo financió? | Nadie. Es un proyecto académico de la Maestría en Inteligencia Artificial de la UEES, sin costo para la institución |

## 2. Composición

| Pregunta | Respuesta |
|---|---|
| ¿Qué representa cada fila? | Un estudiante matriculado en un ciclo lectivo, con el pago que confirmó ese ciclo, su desempeño del año y su reserva para el ciclo siguiente |
| ¿Cuántas filas hay? | 9.031 filas de seis ciclos (2021–2022 a 2026–2027), de 2.733 estudiantes y 2.017 representantes. Entre 1.299 y 1.582 filas por ciclo |
| ¿Es una muestra? | No. Son todos los estudiantes matriculados en las dos sedes en esos ciclos. No representa a otros colegios |
| ¿Qué variables tiene? | 18 columnas tras seudonimizar: tres de ciclo (hoja, año del ciclo y año siguiente), sede, curso y paralelo, promedio (0 a 10), conducta (A a E), fecha de pago de la matrícula, reserva y respuesta del colegio, fecha y tipo de reserva, beca, pensiones pagadas tarde, año de ingreso y dos seudónimos. Diccionario completo en `data/README.md` |
| ¿Hay una etiqueta? | Se deriva: `y_no_matricula = 1` si el estudiante con reserva aprobada no registra el pago de la matrícula entre el 20 de febrero y el 30 de abril del año siguiente. Ocurre en el 6 a 11 % de los casos según el ciclo |
| ¿Faltan datos? | Pocos: fecha de pago vacía en el 0,13 % de las filas, año de ingreso en el 0,01 % y conducta sin valor en menos de 5 casos. La hoja 2026–2027 solo aporta la fecha de pago, porque el ciclo está en curso |
| ¿Hay relaciones entre filas? | Sí. El seudónimo del estudiante enlaza sus ciclos y el del representante agrupa a los hermanos. La familia es la unidad de contacto |
| ¿Hay particiones recomendadas? | Sí, por tiempo. Entrenamiento: cohortes C2 y C3 (2.541 estudiantes, 193 eventos). Selección y calibración: C4 (1.374 y 122). Prueba: C5 (1.411 estudiantes y 98 eventos; 1.093 familias y 74 eventos), usada una sola vez. C1 se excluyó por no ser comparable |
| ¿Hay errores o ruido conocidos? | Encabezados distintos entre hojas; dos formatos para el nombre del curso; una cédula genérica compartida por 39 estudiantes de familias extranjeras; la conducta de 2021 y 2022 se convirtió a letras antes de la extracción (D10). Los tres primeros se corrigen en la limpieza (decisiones D26 a D29) |
| ¿Contiene datos confidenciales? | Sí: datos personales de niñas, niños y adolescentes, que la ley ecuatoriana trata como categoría especial, y de sus representantes |
| ¿Contiene datos sensibles? | No contiene salud, etnia, religión ni informes del DECE, y tampoco la nacionalidad o la condición migratoria de forma directa. La cédula genérica señala de forma indirecta a familias extranjeras: por eso esa marca nunca se usa como predictor (D33). Sí contiene dos variables que reflejan la situación económica: la beca y los atrasos de pago |
| ¿Se puede identificar a personas? | En la base real, sí. En la seudonimizada, solo con la clave y el Excel original; aun así conserva campos que, combinados, podrían identificar a alguien para quien conozca los registros. Por eso no se publica |

## 3. Proceso de recolección

| Pregunta | Respuesta |
|---|---|
| ¿Cómo se obtuvieron los datos? | Del sistema administrativo de LEMAS, exportados a un Excel con una hoja por ciclo. Las pensiones pagadas tarde se calculan del registro mensual de pagos |
| ¿Quién los recolectó? | El personal administrativo, como parte de su trabajo habitual. La extracción para el proyecto la hizo un integrante del equipo que trabaja en LEMAS |
| ¿En qué periodo? | Ciclos 2021–2022 a 2026–2027. La extracción se hizo a fines de septiembre de 2026 |
| ¿Hubo revisión ética? | No hubo comité de ética ni evaluación de impacto previa. Hubo autorización institucional (30-sep-2026) |
| ¿Se informó a las personas? | **No.** Las familias no fueron informadas ni dieron una autorización específica para este análisis. Es una limitación reconocida (ver [consideraciones_eticas.md](consideraciones_eticas.md), secciones 11 y 14) |
| ¿Pueden revocar su consentimiento? | No existe todavía un canal. Está propuesto para LEMAS, junto con el aviso a las familias |

## 4. Preprocesamiento y limpieza

| Pregunta | Respuesta |
|---|---|
| ¿Qué se hizo antes de analizar? | 1) Seudonimización: las cédulas del estudiante y del representante se reemplazan por códigos HMAC-SHA256 con una clave que guarda el custodio. Se eliminan nombres, cédulas, código interno, saldo, deuda y estado de pago. 2) Unificación de encabezados y de nombres de curso. 3) Cálculo de las variables con lo conocido al 20 de febrero. 4) Construcción de cohortes y de la etiqueta |
| ¿Se conservan los datos originales? | Solo dentro de LEMAS. El equipo trabajó con la versión seudonimizada, en Google Colab y con autorización de la institución. Es un servicio en la nube fuera del Ecuador: LEMAS debe revisar si cuenta como transferencia internacional |
| ¿El código está disponible? | Sí: `tools/seudonimizar.py`, `src/data_processing.py` y los cuadernos `00a` a `02` |

## 5. Usos

| Pregunta | Respuesta |
|---|---|
| ¿Para qué se ha usado? | Para comparar tres modelos de aprendizaje automático con reglas simples, validar la regla D2 y analizar el alcance de la lista de contactos |
| ¿Para qué más podría servir? | Para revalidar la regla cada año con la cohorte nueva y para planificar cupos con cifras agregadas |
| ¿Para qué no debe usarse? | Para decidir cupos, becas o reservas; para cobrar; para evaluar al personal; ni para sacar conclusiones sobre otros colegios, estudiantes nuevos o abandono durante el año |
| ¿Algo de su composición condiciona usos futuros? | Sí. Es una sola institución privada con dos sedes y solo incluye a estudiantes con reserva aprobada. Las tasas cambian entre años (6 a 11 %) y hay pocos eventos por grupo: las conclusiones sobre equidad son inciertas |

## 6. Distribución

| Pregunta | Respuesta |
|---|---|
| ¿Se distribuye el conjunto real? | No. El `.gitignore` bloquea el Excel, la base seudonimizada, las claves, las actas y los modelos entrenados con datos reales |
| ¿Qué se publica? | Resultados **agregados**, con las celdas de menos de 5 casos ocultas (en la tabla de proyección aún se puede deducir algún conteo pequeño por diferencia; está pendiente de corregir), y la base **sintética** (`data/synthetic/base_sintetica.csv`): 9.000 filas artificiales con la misma estructura, calibradas con totales agregados y marcadas con `origen_datos = SINTETICO` |
| ¿Con qué licencia? | La del repositorio (MIT) para el código y la base sintética |

La base sintética sirve para ejecutar el código y probar la aplicación. No describe a LEMAS: sus fechas de pago son inventadas y sus resultados no deben citarse como hallazgos.

## 7. Mantenimiento

| Pregunta | Respuesta |
|---|---|
| ¿Quién lo mantiene? | LEMAS mantiene los registros de origen. El equipo mantiene el código y la base sintética en el repositorio |
| ¿Se actualizará? | Sí, con una hoja nueva por ciclo. Cada mayo se añade la cohorte que cierra |
| ¿Cuánto tiempo se conserva? | Las copias de trabajo en Colab se borran al terminar cada sesión. El manual indica eliminar la lista con nombres al terminar la campaña. Se propone eliminar el modelo entrenado con datos reales 30 días después de la aceptación académica |
| ¿Cómo se reportan errores? | A través del repositorio de GitHub, sin incluir datos personales |

## Referencia

Gebru, T., Morgenstern, J., Vecchione, B., Vaughan, J. W., Wallach, H., Daumé III, H. y Crawford, K. (2021). Datasheets for datasets. *Communications of the ACM*, 64(12), 86–92. https://doi.org/10.1145/3458723
