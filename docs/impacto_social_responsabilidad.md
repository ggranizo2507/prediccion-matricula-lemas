# Impacto social y responsabilidad en nuestro proyecto de IA

**Workshop · Semana 4**

> Versión en Markdown del documento entregado en Word ([`Workshop_Impacto_Social_y_Responsabilidad_LEMAS.docx`](Workshop_Impacto_Social_y_Responsabilidad_LEMAS.docx)). El análisis completo está en [consideraciones_eticas.md](consideraciones_eticas.md).

Proyecto: Predicción de matrícula y continuidad estudiantil · Unidad Educativa LEMAS

**Integrantes:** Guillermo Leonidas Granizo Veintimilla (Product Owner) y José Farid Ulloa Manzur (Scrum Master)

Maestría en Inteligencia Artificial · Universidad de Especialidades Espíritu Santo (UEES) · Guayaquil, 3 de octubre de 2026

## Parte 1. Contexto del proyecto

### 1.1 Descripción del sistema

**Problema que resuelve.** En la Unidad Educativa LEMAS (Guayaquil, sedes Mucho Lote 1 y Mucho Lote 2), una reserva aprobada no garantiza la matrícula. Cada año, entre el 6 % y el 11 % de los estudiantes con reserva aprobada no paga la matrícula entre el 20 de febrero y el 30 de abril. La institución se entera tarde y no alcanza a ofrecer apoyo. Hay 69 días y 10 personas para las dos sedes.

**Funcionalidad principal.** El 20 de febrero el sistema ordena a las familias con reserva aprobada para decidir a cuáles llamar primero, y muestra el motivo de cada una. El orden sale de una regla simple (D2): primero quien pagó tarde la matrícula anterior, luego quien hizo reserva extraordinaria y luego quien tuvo más pensiones atrasadas. También proyecta la matrícula por sede y subnivel y, unas semanas después, lista a las familias que siguen sin pagar. Comparamos tres modelos de aprendizaje automático con esa regla y ninguno la superó: la IA nos sirvió para descubrir la regla, validarla y medir su incertidumbre.

**Usuarios objetivo.** Secretaría y Admisiones usan la lista, Dirección revisa los resultados y el custodio de datos guarda la clave de seudonimización. Las familias no usan el sistema: reciben la llamada.

**Dominio de aplicación.** Gestión de la matrícula en educación escolar privada, de Inicial a Bachillerato. Los titulares de los datos son menores de edad y sus representantes.

### 1.2 Alcance de implementación

**Dónde se implementaría.** En un computador de LEMAS: los datos se procesan en ese equipo y no salen a internet (modo institucional). La versión pública de la aplicación es una demostración y solo acepta datos sintéticos. Hoy el sistema es un prototipo validado con datos reales: no está en operación.

**A cuántas personas afectaría.** Cada año, a unos 1.400 estudiantes con reserva aprobada y a sus cerca de 1.090 familias (1.411 y 1.093 en la última cohorte). La lista contiene 165 familias, el 15 %. La usan unas 10 personas. Para construir el sistema se analizaron 9.031 registros de seis ciclos, de 2.733 estudiantes y 2.017 representantes.

**Qué decisiones toma o informa.** No toma ninguna. Informa dos: a qué familias ofrecer primero una llamada de apoyo y cuántas matrículas esperar por sede y subnivel. No decide cupos, reservas ni becas, y la aplicación no contacta a nadie.

**Resultado que enmarca este análisis.** En la prueba final, hecha una sola vez, la lista encontró 22 de las 74 familias que no pagaron en plazo, casi el doble que una selección al azar (Lift 1,97; IC 95 % de 1,24 a 2,56). No alcanzó a las otras 52: el 70 %.

## Parte 2. Análisis de stakeholders

**Tabla 1. Grupos afectados por el sistema**

| **Stakeholder**               | **Descripción**                                                                                  | **Beneficios**                                              | **Riesgos**                                                                         | **Poder / voz** |
|-------------------------------|--------------------------------------------------------------------------------------------------|-------------------------------------------------------------|-------------------------------------------------------------------------------------|-----------------|
| **Familias y representantes** | Cerca de 1.090 familias con reserva aprobada. Deciden y pagan la matrícula                       | Información y facilidades a tiempo, antes de perder el cupo | Sentirse vigiladas o presionadas; estigma por atrasos de pago; no fueron informadas | **Bajo**        |
| **Estudiantes**               | Unos 1.400 menores de edad, titulares de los datos                                               | Continuidad en su colegio                                   | Trato distinto si la etiqueta llega a docentes; exposición de sus datos             | **Bajo**        |
| **Secretaría y Admisiones**   | Diez personas que usan la lista y hacen las llamadas                                             | Enfocar su tiempo; saber por qué llamar a cada familia      | Confiar de más en la lista; que se mida su desempeño por los contactos              | **Medio**       |
| **Dirección de LEMAS**        | Decide si el sistema se usa y responde por LEMAS, que es la responsable del tratamiento de datos | Planificar cupos, paralelos y personal                      | Decidir con una proyección que no mejora a la tasa histórica; responsabilidad legal | **Alto**        |
| **Custodio de datos**         | Guarda la clave y hace la seudonimización                                                        | Proceso ordenado y trazable                                 | Concentra un riesgo: pérdida o fuga de la clave                                     | **Medio**       |
| **Equipo desarrollador**      | Dos estudiantes de maestría; uno trabaja en LEMAS                                                | Aprendizaje y resultado académico                           | Sesgo de confirmación; doble rol de quien desarrolla y maneja los datos             | **Alto**        |

**Tabla 2. Las tres preguntas para cada grupo**

| **Stakeholder**           | **¿Cómo afecta su vida o su trabajo?**                                      | **¿Fue considerado en el diseño?**                                                                         | **¿Cómo se protegen sus intereses?**                                                                                                                |
|---------------------------|-----------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------|
| Familias y representantes | Reciben o no una llamada de apoyo. Su cupo, su reserva y su beca no cambian | **No.** No fueron consultadas ni informadas. Es la principal limitación ética del proyecto                 | Uso prohibido para cobrar o negar cupos; la lista no muestra montos ni probabilidades; aviso a las familias redactado y canal de reclamos propuesto |
| Estudiantes               | De forma indirecta: su continuidad depende de la decisión de la familia     | No participaron. Sus datos se trataron seudonimizados                                                      | Cédulas reemplazadas por seudónimos; nunca se usan nacionalidad, salud ni informes del DECE; la lista es confidencial                               |
| Secretaría y Admisiones   | Organiza sus llamadas. Sigue decidiendo a quién llamar y qué ofrecer        | **En parte.** El sistema sigue su proceso de reservas y de contacto. Falta validar la aplicación con ellas | Número de contactos editable; manual y protocolo de contacto; la lista no es un indicador de desempeño                                              |
| Dirección de LEMAS        | Recibe la proyección y un informe anual                                     | **Sí.** Autorizó el estudio el 30-sep-2026                                                                 | Resultados con intervalos de confianza y limitaciones; criterio escrito para suspender el sistema                                                   |
| Custodio de datos         | Sube la clave en cada uso y aprueba cada extracción                         | **Sí.** El flujo de datos se diseñó alrededor de su rol                                                    | La aplicación no guarda la clave; muestra su huella para comprobarla; acta en cada extracción                                                       |
| Equipo desarrollador      | Responde por la calidad técnica y por lo que afirma                         | Sí                                                                                                         | Decisiones registradas antes de ver resultados; prueba final una sola vez; resultados publicados aunque no favorezcan a la IA                       |

## Parte 3. Evaluación de impacto social

### 3.1 Impactos positivos

**Tabla 3. Impactos positivos**

| **Impacto**                                | **Descripción**                                                                                                                                                             | **Grupos beneficiados**                            | **Evidencia**                                                                                                                                 |
|--------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------|
| **1. Apoyo más oportuno y mejor dirigido** | La lista queda disponible el 20 de febrero, 69 días antes del cierre, y concentra los casos                                                                                 | Familias en riesgo de no matricularse; estudiantes | Prueba final: 22 de 74 casos con una lista de 165 familias. Al azar serían unos 11. Lift 1,97 (IC 95 %: 1,24 a 2,56)                          |
| **2. Trabajo del personal mejor enfocado** | Diez personas saben por dónde empezar. No reemplaza ningún puesto                                                                                                           | Secretaría y Admisiones                            | La aplicación genera la lista en segundos y cada familia lleva su motivo. Son 118 y 47 familias por sede                                      |
| **3. Planificación con cifras**            | Proyección de matrículas por sede y subnivel al 20 de febrero                                                                                                               | Dirección y Coordinación académica                 | Error del 2,8 % en la prueba final. Es el mismo error que da la tasa histórica: sirve, pero no mejora lo que ya se podía calcular             |
| **4. Datos de menores mejor protegidos**   | El análisis se hace con seudónimos. Los datos con nombres y la clave no salen de LEMAS; la base seudonimizada se analizó en Google Colab con autorización de la institución | Estudiantes y familias; la institución             | Seudonimización HMAC-SHA256 con clave custodiada; la aplicación pública solo acepta datos sintéticos; el repositorio no contiene datos reales |

### 3.2 Impactos negativos y riesgos

**Tabla 4. Impactos negativos y riesgos**

| **Riesgo**                                        | **Descripción**                                                                                                                                      | **Grupos vulnerables**                                                     | **Severidad** | **Probabilidad**               |
|---------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------|---------------|--------------------------------|
| **1. Que la lista se use para cobrar**            | La misma lista que sirve para ayudar sirve para presionar. El listado de familias que siguen sin pagar se parece todavía más a una lista de cobranza | Familias con dificultades económicas                                       | **Alta**      | **Media**                      |
| **2. Menos apoyo a familias becadas**             | La lista encuentra al 18 % de los casos entre becadas y al 32 % entre no becadas (2 de 11 frente a 20 de 63)                                         | Familias becadas                                                           | **Media**     | **Media** (incierta: 11 casos) |
| **3. Falsa confianza en la lista**                | No alcanza al 70 % de los casos. Si el personal atiende solo a la lista, ese 70 % queda peor que antes                                               | Familias que la regla no prioriza: el 70 % de los casos en la prueba final | **Media**     | **Media**                      |
| **4. Exposición de datos de menores**             | En LEMAS la aplicación muestra nombres y permite descargar la lista                                                                                  | Estudiantes y familias                                                     | **Alta**      | **Baja**                       |
| **5. Datos tratados sin informar a las familias** | El estudio se hizo con autorización de la institución, sin aviso a los representantes                                                                | Todas las familias                                                         | **Alta**      | **Alta** (ya ocurrió)          |

### 3.3 Análisis de equidad

**¿El sistema reduce o aumenta las desigualdades?** No podemos afirmar que las reduzca, y hay una señal de que podría aumentarlas para las familias becadas. El beneficio del sistema es una llamada de apoyo, y no se reparte por igual.

- **Distribución de beneficios.** La llamada llega más a las familias con atrasos de pago, que probablemente son las que más la necesitan. Pero llega menos a las becadas: entran en la lista el 10,4 % de ellas frente al 15,9 % de las demás (razón de 0,66; suele tomarse como alerta un valor menor que 0,80). Entre sedes también hay diferencia: 18,4 % en Mucho Lote 1 y 10,4 % en Mucho Lote 2.

- **Distribución de riesgos.** El riesgo de quedar etiquetada o de recibir presión recae en las familias con atrasos. La institución recibe el beneficio de planificar y casi ningún riesgo.

- **Acceso.** Todas las familias con reserva aprobada entran en el ordenamiento. Quedan fuera por diseño los estudiantes nuevos y las reservas pendientes.

- **Barreras.** Las familias extranjeras que comparten una cédula genérica (39 estudiantes) se tratan como contactos individuales, pero no pudimos evaluar la equidad para ellas. Y las familias que la regla no prioriza quedan fuera: el 70 % de los casos en la prueba final.

Con 11 casos entre becadas no sabemos si la diferencia es real. La informamos como alerta y la vigilamos (Parte 5).

## Parte 4. Riesgos éticos específicos

**Tabla 5. Checklist de riesgos éticos aplicado al proyecto**

| **Categoría**        | **Respuesta**                                                                                                                                                                                                                                                                                                                                        |
|----------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Fairness y sesgo** | No usa género, etnia, edad, religión ni nacionalidad. Sí usa señales de pago, que reflejan la situación económica. El evento es minoritario (6 a 11 %) y lo tratamos con métricas de ordenamiento. Evaluamos selección, precisión y recall por sede, beca y subnivel, con el enfoque de Fairlearn \[8\] y código propio                              |
| **Privacidad**       | Datos administrativos de menores y representantes: curso, promedio, conducta, pagos, reserva y beca. No hubo consentimiento informado específico, solo autorización institucional. Las cédulas se reemplazan por seudónimos y se eliminan nombres y saldos. Reidentificar exige la clave y el Excel original; la base seudonimizada nunca se publica |
| **Transparencia**    | El personal entiende el sistema: la regla cabe en una frase y cada familia lleva su motivo. Las limitaciones están en la aplicación, el README y la ficha del modelo. Las familias todavía no saben que existe                                                                                                                                       |
| **Autonomía**        | Una persona decide a quién llamar y qué ofrecer. La aplicación no contacta a nadie. El riesgo de coacción está en el uso: llamar para cobrar                                                                                                                                                                                                         |
| **Seguridad**        | Si la regla falla, la familia recibe la atención habitual. Los errores posibles son una llamada innecesaria o una familia no listada. Hay 176 pruebas automáticas y un criterio para suspender el sistema                                                                                                                                            |
| **Accountability**   | Responde LEMAS, a través de Dirección. No existe todavía un proceso de apelación para las familias. La auditoría anual está propuesta                                                                                                                                                                                                                |

**Tabla 6. Riesgos éticos analizados**

| **Riesgo**                                                                           | **Descripción**                                                                                                                       | **Evidencia**                                                                                                                                                                                                                                     | **Severidad** | **Grupo afectado**                     |
|--------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------|----------------------------------------|
| **R1. Señales de pago como indicador económico** (fairness, autonomía)               | La regla ordena por atrasos de pago. Aparecer en la lista dice algo de la economía de la familia                                      | Las tres variables de la regla son de pago o de reserva. Son las únicas que ordenaron a las familias                                                                                                                                              | **Alta**      | Familias con menos recursos            |
| **R2. Menor detección en familias becadas** (fairness)                               | La lista encuentra menos casos entre las becadas. Una explicación posible, que no comprobamos: quien paga menos acumula menos atrasos | Recall 0,18 frente a 0,32; razón de selección 0,66; 11 casos                                                                                                                                                                                      | **Media**     | Familias becadas                       |
| **R3. Datos de menores sin informar a las familias** (privacidad)                    | El análisis usó datos de niñas, niños y adolescentes sin aviso ni autorización específica                                             | Solo hubo autorización institucional (30-sep-2026). Según nuestra lectura, la ley pide autorización del representante                                                                                                                             | **Alta**      | Todas las familias y estudiantes       |
| **R4. Fuga o reidentificación** (privacidad, seguridad)                              | La lista con nombres se descarga, y la clave pasa por las manos de quien la sube                                                      | En LEMAS la aplicación muestra nombres a personal autorizado; la base seudonimizada conserva campos que, combinados, podrían identificar a alguien que conozca los registros; el análisis académico se ejecutó en Google Colab, fuera del Ecuador | **Alta**      | Estudiantes y familias                 |
| **R5. Confianza excesiva en una regla que no es estable** (seguridad, transparencia) | El resultado cambia con el año y con el sorteo entre familias empatadas, y la regla deja de ayudar desde la cuarta semana             | Lift de 1,38 a 1,97 en cuatro ciclos; en uno va de 1,53 a 1,99 según el sorteo. En tres ciclos anteriores (C2 a C4), el 86 % de los casos no registra ningún pago y la lista encuentra al 24 % de ellos                                           | **Media**     | Familias fuera de la lista; Secretaría |
| **R6. Responsabilidad concentrada y sin vía de reclamo** (accountability)            | Un integrante del equipo trabaja en LEMAS y manejó los datos. Las familias no tienen dónde preguntar o reclamar                       | Doble rol declarado; el canal de consultas no existe                                                                                                                                                                                              | **Media**     | Familias; la institución               |

**Cómo asignamos la severidad.** Es alta cuando el daño toca derechos de las familias o de los menores y es difícil de revertir: la presión económica (R1), el tratamiento de datos sin informar (R3) y la exposición de datos personales (R4). Es media cuando afecta a cómo se reparte el apoyo y se puede corregir en la campaña siguiente (R2, R5 y R6). R1 es un sesgo de medición, porque una variable de pago mide también otra cosa, y R2 puede ser un sesgo de representación, por los pocos casos del grupo. Son dos tipos de sesgo descritos en la literatura sobre educación \[9\].

## Parte 5. Estrategias de mitigación

Una estrategia por riesgo. La última columna dice qué está hecho y qué queda como propuesta para LEMAS.

**Tabla 7. Mitigación de cada riesgo**

<table>
<thead>
<tr class="header">
<th><strong>Riesgo y estrategia</strong></th>
<th><strong>Tipo</strong></th>
<th><strong>Implementación</strong></th>
<th><strong>Cuándo y responsable</strong></th>
<th><strong>Efectividad y estado</strong></th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td><strong>R1.</strong> Limitar el uso a llamadas de apoyo y quitar de la lista lo que sirve para cobrar</td>
<td>Política y diseño</td>
<td><p>1. Usos prohibidos por escrito: cobrar, negar cupos, perfilar.</p>
<p>2. La lista no muestra montos, saldos ni probabilidades; solo el motivo.</p>
<p>3. Protocolo de contacto y capacitación de Secretaría</p></td>
<td>Antes de la primera campaña y en cada una. Dirección (política), equipo (diseño), Secretaría (protocolo)</td>
<td><strong>Media:</strong> depende de que las personas cumplan la política. Pasos 1 y 2 hechos; capacitación pendiente</td>
</tr>
<tr class="even">
<td><strong>R2.</strong> Medir el recall por grupo y reservar contactos al azar</td>
<td>Técnica y política</td>
<td><p>1. Calcular selección y recall por beca, sede y subnivel, acumulando cohortes.</p>
<p>2. Revisar a las becadas con atrasos aunque no estén en la lista.</p>
<p>3. Reservar parte de los contactos para familias elegidas al azar</p></td>
<td>Cada campaña y cada mayo. Equipo técnico (métricas), Secretaría (revisión)</td>
<td><strong>Media.</strong> Métricas implementadas; reserva al azar propuesta</td>
</tr>
<tr class="odd">
<td><strong>R3.</strong> Informar a las familias y confirmar la base legal antes del uso real</td>
<td>Política y educación</td>
<td><p>1. El asesor jurídico confirma la base legal.</p>
<p>2. Aviso a las familias (texto ya redactado) y canal de consultas.</p>
<p>3. Evaluación de impacto y registro del tratamiento</p></td>
<td>Antes de la primera campaña. Dirección de LEMAS con su asesor</td>
<td><strong>Alta.</strong> Propuesta: depende de LEMAS</td>
</tr>
<tr class="even">
<td><strong>R4.</strong> Seudonimizar y separar la aplicación en dos modos</td>
<td>Técnica y diseño</td>
<td><p>1. Seudónimos HMAC-SHA256 con clave del custodio; se eliminan nombres y saldos.</p>
<p>2. Versión pública solo con datos sintéticos; versión de LEMAS solo en el mismo equipo, en memoria y con nombres tras confirmar.</p>
<p>3. Celdas con menos de 5 casos ocultas; repositorio sin datos reales</p></td>
<td>Desde el inicio y de forma continua. Equipo técnico y custodio</td>
<td><strong>Alta.</strong> Implementada en lo técnico. Pendientes: ocultar una celda más en la tabla de proyección y que LEMAS designe quién ve los nombres</td>
</tr>
<tr class="odd">
<td><strong>R5.</strong> Decir lo que el sistema no hace y fijar cuándo se suspende</td>
<td>Educación, política y técnica</td>
<td><p>1. Limitaciones visibles en la aplicación, el README y la ficha del modelo.</p>
<p>2. Informe cada mayo con el Lift y su intervalo: revalidar si baja de 1,20 y suspender si no supera al azar dos años seguidos.</p>
<p>3. Segunda ronda con las familias que siguen sin pagar</p></td>
<td>Continuo y cada mayo. Equipo técnico y Dirección</td>
<td><strong>Media.</strong> Paso 1 hecho; el informe anual es una propuesta; la segunda ronda ya está en la aplicación, sin validar</td>
</tr>
<tr class="even">
<td><strong>R6.</strong> Separar funciones y abrir un canal de reclamos</td>
<td>Política</td>
<td><p>1. Dirección designa por escrito al custodio, distinto de quien mantiene el sistema.</p>
<p>2. Bitácora por campaña: quién generó la lista, cuándo y con cuántos contactos.</p>
<p>3. Canal para preguntar, corregir datos o reclamar</p></td>
<td>Antes de la primera campaña. Dirección de LEMAS</td>
<td><strong>Media.</strong> Propuesta</td>
</tr>
</tbody>
</table>

*De las estrategias de prioridad alta, R4 está implementada, R1 lo está en lo que depende del equipo y R3 depende de LEMAS.*

## Parte 6. Framework de responsabilidad

Nos guiamos por los principios de la Recomendación de la UNESCO sobre la ética de la IA \[4\] y por las cuatro funciones del marco de gestión de riesgos del NIST \[5\]: gobernar, mapear, medir y gestionar.

### 6.1 Cadena de responsabilidad

**Tabla 8. Quién responde de qué**

| **Rol**                                              | **Responsabilidades**                                        | **Rendición de cuentas**                                                                                                   |
|------------------------------------------------------|--------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------|
| **Desarrolladores** (Guillermo Granizo y José Ulloa) | Implementación técnica correcta y documentación              | 176 pruebas automáticas e integración continua en cada cambio; los cambios entran por pull request                         |
| **Científicos de datos** (el mismo equipo)           | Calidad de los datos, protocolo de validación y equidad      | Sistema congelado con huella SHA-256 antes de la prueba final, hecha una sola vez; tabla de equidad por grupo              |
| **Product Owner** (Guillermo Granizo)                | Decisiones de diseño y de alcance                            | Registro de 52 decisiones con fecha y motivo                                                                               |
| **Custodio de datos** (LEMAS)                        | Extracción, seudonimización y resguardo de la clave          | Acta con huella SHA-256 en cada extracción; huella de la clave en pantalla                                                 |
| **Secretaría y Admisiones**                          | Generar la lista, decidir a quién llamar y hacer el contacto | Bitácora por campaña y resultado de cada contacto (propuesto)                                                              |
| **Dirección de LEMAS** (organización)                | Autorizar el uso, fijar sus límites y dar recursos           | Autorización del estudio (30-sep-2026); informe anual (propuesto); decide si el sistema se mantiene, se ajusta o se retira |

### 6.2 Mecanismos de accountability

**Tabla 9. Estado de cada mecanismo**

| **Mecanismo**                                           | **Estado** | **Dónde o cómo**                                                                                              |
|---------------------------------------------------------|------------|---------------------------------------------------------------------------------------------------------------|
| **Documentación:** model card \[6\]                     | Hecho      | docs/ficha_modelo.md                                                                                          |
| Datasheet del conjunto de datos \[7\]                   | Hecho      | docs/hoja_de_datos.md                                                                                         |
| Ethics statement con análisis de riesgos                | Hecho      | docs/consideraciones_eticas.md y este documento                                                               |
| **Supervisión:** revisión humana en decisiones críticas | Hecho      | Secretaría decide; la aplicación no contacta ni decide                                                        |
| Proceso de apelación                                    | Propuesto  | Canal de consultas y reclamos, a cargo de LEMAS                                                               |
| Auditoría periódica                                     | Propuesto  | Frecuencia: anual, cada mayo, al cerrar la matrícula                                                          |
| **Monitoreo:** métricas de fairness                     | Parcial    | El código las calcula; el seguimiento anual es una propuesta                                                  |
| Alertas por deriva o anomalías                          | Parcial    | Umbrales definidos (Lift menor que 1,20; cambio de políticas de cobro o reserva). No son automáticas          |
| Reportes de incidentes                                  | Parcial    | Registro de decisiones, con el primer incidente documentado (6.3). Falta un registro propio para la operación |
| **Transparencia:** información sobre el uso de IA       | Parcial    | Al personal, en la aplicación. A las familias, pendiente                                                      |
| Comunicación de limitaciones                            | Hecho      | Aplicación, README, ficha del modelo y pitch                                                                  |
| Acceso a explicaciones                                  | Parcial    | Al personal: motivo por familia y regla pública. A las familias, pendiente del canal                          |

### 6.3 Plan de respuesta a incidentes

**Tabla 10. Cinco pasos, con el incidente real del 3 de octubre de 2026**

| **Paso**                   | **Qué hacemos**                                                                                                                                                      | **Incidente del 3-oct: error en la aplicación pública**                                            |
|----------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------|
| **1. Detección**           | Pruebas automáticas en cada cambio, avisos de la aplicación al cargar datos, quejas de familias y revisión de mayo                                                   | El Product Owner vio un error al generar la lista después de una actualización                     |
| **2. Respuesta inmediata** | Avisar al custodio y a Dirección. Contener: retirar el archivo o el acceso; si la clave se expuso, dejar de usarla. Volver al contacto habitual                      | Se reinició la aplicación. No había datos personales: la versión pública solo usa datos sintéticos |
| **3. Investigación**       | Qué falló, qué datos y cuántas personas están afectados. Reproducir el fallo con una prueba                                                                          | La plataforma ejecutó el programa nuevo con un módulo antiguo que seguía en memoria                |
| **4. Corrección**          | Reparar. Si hay datos personales, notificar a la autoridad y a los titulares en los plazos de ley (LOPDP, arts. 43 y 46) y dar una explicación a la familia afectada | La aplicación ahora detecta el código que cambió y lo vuelve a cargar                              |
| **5. Prevención**          | Dejar una prueba que reproduzca el fallo, registrar lo ocurrido y ajustar el protocolo                                                                               | Dos pruebas nuevas reproducen el fallo; quedó registrado como decisión D51                         |

## Parte 7. Consideraciones de compliance

**Tabla 11. Regulaciones revisadas**

| **Regulación**                                                                                                        | **¿Aplica?**    | **Qué requiere**                                                                                                                                                                                                                                                | **¿Cumplimos?**                                                                                                                                              | **Cambios necesarios**                                                                                                                                                             |
|-----------------------------------------------------------------------------------------------------------------------|-----------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **LOPDP** (Ecuador, 2021) y su reglamento \[1\]                                                                       | **Sí**          | Base legítima; autorización del representante para datos de menores (art. 21, según nuestra lectura); informar a los titulares (art. 12); seguridad y protección desde el diseño; evaluación de impacto (art. 42); límites a decisiones automatizadas (art. 20) | **Parcial.** Seguridad y diseño, sí. Solo ordena llamadas de apoyo, sin efectos jurídicos ni impactos graves: por eso entendemos que queda fuera del art. 20 | LEMAS: confirmar la base legal, informar a las familias, hacer la evaluación de impacto, registrar el tratamiento y revisar si el uso de Colab fue una transferencia internacional |
| **Norma de la SPDP sobre IA y datos personales** (Resolución SPDP-SPD-2026-0009-R) \[2\]                              | **Sí**          | Información clara al titular, gestión de riesgos, evaluación de impacto previa, registro y auditorías según el riesgo                                                                                                                                           | **Parcial**                                                                                                                                                  | Evaluación de impacto y registro                                                                                                                                                   |
| **No discriminación e interés superior del niño** (Constitución, arts. 11.2, 44 y 66.19; Código de la Niñez, art. 11) | **Sí**          | No discriminar y poner primero el interés de niñas, niños y adolescentes                                                                                                                                                                                        | **Sí en el diseño:** no usa nacionalidad, etnia, religión ni salud. La brecha en becadas está en observación                                                 | Seguimiento anual por grupo                                                                                                                                                        |
| **AI Act de la UE** (Reglamento 2024/1689) \[3\]                                                                      | No (referencia) | Clasifica como alto riesgo los sistemas que determinan el acceso o la admisión a instituciones educativas                                                                                                                                                       | A nuestro juicio queda fuera: no decide admisiones                                                                                                           | Mantener prohibido el uso para negar cupos                                                                                                                                         |
| **GDPR, CCPA, HIPAA**                                                                                                 | No              | Titulares y responsable están en Ecuador; no hay datos de salud. Usamos el GDPR como referencia                                                                                                                                                                 | —                                                                                                                                                            | —                                                                                                                                                                                  |
| **Leyes laborales**                                                                                                   | No              | El sistema no decide sobre empleo                                                                                                                                                                                                                               | —                                                                                                                                                            | No usar la lista para evaluar al personal                                                                                                                                          |

*Esta lectura es de un equipo técnico. Para una implementación real, LEMAS necesita la asesoría de su abogado o de su delegado de protección de datos.*

## Parte 8. Reflexión y compromiso

### 8.1 Reflexión grupal

**1. El dilema más difícil: usar o no las señales de pago.** Las únicas variables que ordenaron bien a las familias son de pago y de reserva, y las de pago reflejan su situación económica. Entran en conflicto dos valores. Uno es el beneficio: llegar a tiempo a quien necesita apoyo. El otro es la justicia y la dignidad: no marcar a una familia por cómo paga. Decidimos usarlas con tres condiciones: la lista solo sirve para ofrecer ayuda, la decisión es de una persona y la lista no muestra montos ni probabilidades. Si LEMAS no puede garantizar ese límite de uso, la lista no debería usarse.

**2. Lo que aprendimos y no habíamos considerado.**

- Dimos por suficiente el interés legítimo de la institución. Al leer el art. 21 de la LOPDP entendimos que, con datos de menores, hace falta confirmar la base legal e informar a las familias.

- Predecir no es ayudar. Medimos a quién encuentra la lista, pero no si la llamada cambia la decisión de la familia. Es lo que pasó con el sistema de alerta de deserción de Wisconsin: ordenaba bien a los estudiantes y no se pudo demostrar que mejorara la graduación \[10\].

- El 70 % que la lista no alcanza no es un problema de capacidad, sino de información. En los ciclos anteriores (C2 a C4), el 86 % de los casos son familias que no registran ningún pago, y la regla las encuentra peor que a las que pagan tarde.

- Un detalle técnico puede ser un asunto de justicia: entre familias con el mismo puntaje, quién entra en la lista lo decide un sorteo.

- Una lista de familias que siguen sin pagar es útil para ayudar y también es casi una lista de cobranza.

**3. Lo que cambiamos y lo que cambiaríamos.** A raíz del análisis ético de esta semana cambiamos tres cosas: la aplicación usa el mismo sorteo que se validó, las listas ya no muestran una probabilidad junto a cada familia y el listado de seguimiento advierte que no es una predicción. Si empezáramos de nuevo, informaríamos a las familias y haríamos la evaluación de impacto antes de tocar los datos, incluiríamos a representantes en el diseño y reservaríamos desde la primera campaña una parte de los contactos para familias elegidas al azar.

### 8.2 Compromiso ético

Como creadores de este sistema de IA, nos comprometemos a:

- Entregar a Dirección, cada mayo, el Lift de la lista con su intervalo y el recall por beca, sede y subnivel, y recomendar la suspensión si la regla no supera al azar dos años seguidos.

- No recomendar el uso operativo mientras LEMAS no informe a las familias y confirme la base legal para tratar datos de menores.

- No sacar de LEMAS datos con nombres ni la clave, no volver a procesar la base seudonimizada en servicios externos y mantener en el repositorio solo datos sintéticos y resultados agregados.

- Actuar responsablemente si se identifican daños: avisar, corregir y dejar registro.

- Priorizar el bienestar de las familias con dificultades económicas, de las becadas y de los estudiantes, que son menores de edad.

- Mantener la transparencia sobre las limitaciones: la lista no alcanza al 70 % de los casos y los modelos de IA no superaron a una regla simple.

<table>
<tbody>
<tr class="odd">
<td><p><strong>Guillermo Leonidas Granizo Veintimilla</strong></p>
<p>Product Owner</p></td>
<td><p><strong>José Farid Ulloa Manzur</strong></p>
<p>Scrum Master</p></td>
</tr>
</tbody>
</table>

Guayaquil, 3 de octubre de 2026

## Referencias

1.  República del Ecuador, Ley Orgánica de Protección de Datos Personales, Registro Oficial, Quinto Suplemento n.º 459, 26 de mayo de 2021.

2.  Superintendencia de Protección de Datos Personales, Resolución SPDP-SPD-2026-0009-R, Norma general para la garantía del derecho de protección de datos personales en el uso de sistemas de inteligencia artificial, 12 de febrero de 2026.

3.  Unión Europea, Reglamento (UE) 2024/1689 (Ley de Inteligencia Artificial), anexo III, punto 3.

4.  UNESCO, Recomendación sobre la ética de la inteligencia artificial, 2021.

5.  NIST, Artificial Intelligence Risk Management Framework (AI RMF 1.0), NIST AI 100-1, 2023.

6.  M. Mitchell et al., «Model cards for model reporting», Proc. FAT\*, 2019, pp. 220–229.

7.  T. Gebru et al., «Datasheets for datasets», Communications of the ACM, vol. 64, n.º 12, pp. 86–92, 2021.

8.  H. Weerts et al., «Fairlearn: Assessing and improving fairness of AI systems», JMLR, vol. 24, n.º 257, 2023.

9.  R. S. Baker y A. Hawn, «Algorithmic bias in education», Int. J. Artif. Intell. Educ., vol. 32, pp. 1052–1092, 2022.

10. J. C. Perdomo, T. Britton, M. Hardt y R. Abebe, «Difficult lessons on social prediction from Wisconsin public schools», Proc. ACM FAccT, 2025.

*Repositorio y documentación completa: github.com/ggranizo2507/prediccion-matricula-lemas (docs/consideraciones_eticas.md, docs/ficha_modelo.md, docs/hoja_de_datos.md).*
