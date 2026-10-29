# Guion del video de respuestas (10 preguntas)

Guion con el que se grabó el [video de respuestas](https://drive.google.com/file/d/1jeZcgmn2UCN8TkpYqUtu-z1yCMgseG8G/view?usp=sharing) a las preguntas de la profesora. **Guillermo Granizo** responde las impares (1, 3, 5, 7 y 9) y **José Ulloa** las pares (2, 4, 6, 8 y 10), en el orden entregado y con un máximo de 2 minutos por pregunta. Cada cifra lleva su fuente en el repositorio (sección 4).

## 1. Reglas que cumple este video

- **Orden y número:** se responde en el orden entregado y cada respuesta empieza diciendo «Pregunta N».

- **Nombre y cámara:** cada integrante dice su nombre antes de su primera respuesta y responde en cámara solo las suyas. Si uno responde las del otro, o no aparece en cámara, esas preguntas valen 0.

- **Duración:** máximo 2 minutos por pregunta; lo que pase de ese tiempo no se califica. Cada guion está calculado para durar entre 1:30 y 1:50, incluidos los cambios de pantalla.

- **Interfaz real:** la pregunta 8 se graba con la aplicación desplegada desde el repositorio, nunca con una maqueta. Las preguntas 1 y 5 también la muestran.

- **Coherencia:** una respuesta que contradiga el repositorio vale como máximo 4 puntos; por eso cada cifra lleva su fuente en la sección 4.

- **Entrega:** MP4, o YouTube no listado o Google Drive con acceso para la profesora, y el enlace en la sección Videos del README.

### Reparto y tiempos

| **\#** | **Tema**                                                                 | **Responde**      | **Palabras** | **Duración estimada** | **Pantalla**        |
|--------|--------------------------------------------------------------------------|-------------------|--------------|-----------------------|---------------------|
| 1      | Problema, usuario y qué hace hoy sin el sistema                          | Guillermo Granizo | 227          | 1:45                  | 2 momentos          |
| 2      | Datos, limitaciones y preprocesamiento clave                             | José Ulloa        | 215          | 1:40                  | 2 momentos          |
| 3      | Por qué este modelo y comparación con el baseline                        | Guillermo Granizo | 206          | 1:36                  | 2 momentos          |
| 4      | Sensibilidad de hiperparámetros (Workshop S5)                            | José Ulloa        | 208          | 1:41                  | 3 momentos          |
| 5      | Por qué esta métrica y un caso donde falla                               | Guillermo Granizo | 204          | 1:35                  | 2 momentos          |
| 6      | Sobreajuste y datos nuevos                                               | José Ulloa        | 195          | 1:32                  | 2 momentos          |
| 7      | Riesgo ético principal, medidas y usos prohibidos                        | Guillermo Granizo | 202          | 1:35                  | 2 momentos          |
| 8      | Entrada inválida, error y diseño para el usuario (grabación de pantalla) | José Ulloa        | 167          | 1:48                  | Grabación de la app |
| 9      | Opción A · Variables importantes y fuga de datos                         | Guillermo Granizo | 213          | 1:39                  | 2 momentos          |
| 10     | La decisión más difícil: medir por familia con k fijo                    | José Ulloa        | 205          | 1:36                  | 2 momentos          |

*Duración total estimada: unos 16 minutos, a 140 palabras por minuto, más unos 4 segundos por cada cambio de pantalla. Si en el ensayo una respuesta pasa de 1:50, se recorta un ejemplo, nunca una cifra ni la limitación.*

### Cómo sonar natural

- **Hablen, no lean:** el guion está escrito para decirse en voz alta. Úsenlo para ensayar y graben mirando a la cámara; si cambian una palabra no pasa nada, pero las cifras se dicen tal cual.

- **Cada respuesta tiene un arco:** una respuesta corta al inicio, la historia con la evidencia en pantalla, el porqué de la decisión y un límite honesto al final.

- **Pausas:** una pausa breve después de cada cifra grande y antes de la limitación. Las preguntas retóricas («¿Y la híbrida?») se dicen con una pausa corta antes de responder.

- **Señalar lo que se ve:** frases como «fíjense en este escalón» o «aquí está» se dicen mientras el cursor señala ese punto de la pantalla.

### Cómo grabar

- **Formato sugerido:** pantalla compartida con la cámara del que responde en una esquina, siempre visible (OBS, Zoom o Loom). Así se cumple «en cámara» y a la vez se muestra la evidencia.

- **Por turnos:** se graban por separado las respuestas de cada uno y se montan en orden 1 a 10. Guillermo graba 1, 3, 5, 7 y 9; José, 2, 4, 6, 8 y 10.

- **Presentación:** Guillermo dice su nombre al inicio de la pregunta 1 y José al inicio de la pregunta 2 (texto incluido en el guion).

- **Antes de grabar:** dejar abiertas las pestañas de la sección 2 y despertar la aplicación unos minutos antes. Nunca abrir la pestaña «Lista con nombres» ni el Excel real.

## 2. Pestañas y archivos que hay que tener listos

| **Pregunta** | **Qué abrir**                                           | **Enlace**                                                                                                                                                                                                                                           |
|--------------|---------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 1            | README.md · Descripción del problema                    | [github.com/ggranizo2507/prediccion-matricula-lemas/blob/main/README.md#descripción-del-problema](https://github.com/ggranizo2507/prediccion-matricula-lemas/blob/main/README.md#descripción-del-problema)                                           |
| 1            | Aplicación · Lista de contactos (datos sintéticos)      | [continuidad-matricula-lemas.streamlit.app/](https://continuidad-matricula-lemas.streamlit.app/)                                                                                                                                                     |
| 2            | docs/hoja_de_datos.md                                   | [github.com/ggranizo2507/prediccion-matricula-lemas/blob/main/docs/hoja_de_datos.md](https://github.com/ggranizo2507/prediccion-matricula-lemas/blob/main/docs/hoja_de_datos.md)                                                                     |
| 2            | docs/analisis_datos.md · problemas de calidad           | [github.com/ggranizo2507/prediccion-matricula-lemas/blob/main/docs/analisis_datos.md](https://github.com/ggranizo2507/prediccion-matricula-lemas/blob/main/docs/analisis_datos.md)                                                                   |
| 2            | src/data_processing.py · marcar_representantes_atipicos | [github.com/ggranizo2507/prediccion-matricula-lemas/blob/main/src/data_processing.py](https://github.com/ggranizo2507/prediccion-matricula-lemas/blob/main/src/data_processing.py)                                                                   |
| 3            | docs/modelado.md · secciones 2, 3 y 9.3                 | [github.com/ggranizo2507/prediccion-matricula-lemas/blob/main/docs/modelado.md](https://github.com/ggranizo2507/prediccion-matricula-lemas/blob/main/docs/modelado.md)                                                                               |
| 3            | results/figures/real_09_seleccion_c4.png                | [github.com/ggranizo2507/prediccion-matricula-lemas/blob/main/results/figures/real_09_seleccion_c4.png](https://github.com/ggranizo2507/prediccion-matricula-lemas/blob/main/results/figures/real_09_seleccion_c4.png)                               |
| 3            | results/figures/real_12_prueba_c5.png                   | [github.com/ggranizo2507/prediccion-matricula-lemas/blob/main/results/figures/real_12_prueba_c5.png](https://github.com/ggranizo2507/prediccion-matricula-lemas/blob/main/results/figures/real_12_prueba_c5.png)                                     |
| 3            | src/reglas.py (definición única de D y D2)              | [github.com/ggranizo2507/prediccion-matricula-lemas/blob/main/src/reglas.py](https://github.com/ggranizo2507/prediccion-matricula-lemas/blob/main/src/reglas.py)                                                                                     |
| 4            | docs/optimizacion.md · sección 2 bis                    | [github.com/ggranizo2507/prediccion-matricula-lemas/blob/main/docs/optimizacion.md](https://github.com/ggranizo2507/prediccion-matricula-lemas/blob/main/docs/optimizacion.md)                                                                       |
| 4            | results/figures/real_31_importancia_hiperparametros.png | [github.com/ggranizo2507/prediccion-matricula-lemas/blob/main/results/figures/real_31_importancia_hiperparametros.png](https://github.com/ggranizo2507/prediccion-matricula-lemas/blob/main/results/figures/real_31_importancia_hiperparametros.png) |
| 4            | results/figures/real_32_dependencia_parcial.png         | [github.com/ggranizo2507/prediccion-matricula-lemas/blob/main/results/figures/real_32_dependencia_parcial.png](https://github.com/ggranizo2507/prediccion-matricula-lemas/blob/main/results/figures/real_32_dependencia_parcial.png)                 |
| 4            | src/sensibilidad.py                                     | [github.com/ggranizo2507/prediccion-matricula-lemas/blob/main/src/sensibilidad.py](https://github.com/ggranizo2507/prediccion-matricula-lemas/blob/main/src/sensibilidad.py)                                                                         |
| 5            | Aplicación · Evaluar un estudiante                      | [continuidad-matricula-lemas.streamlit.app/](https://continuidad-matricula-lemas.streamlit.app/)                                                                                                                                                     |
| 5            | results/figures/real_24_alcance_desglose.png            | [github.com/ggranizo2507/prediccion-matricula-lemas/blob/main/results/figures/real_24_alcance_desglose.png](https://github.com/ggranizo2507/prediccion-matricula-lemas/blob/main/results/figures/real_24_alcance_desglose.png)                       |
| 5            | docs/alcance_lista.md                                   | [github.com/ggranizo2507/prediccion-matricula-lemas/blob/main/docs/alcance_lista.md](https://github.com/ggranizo2507/prediccion-matricula-lemas/blob/main/docs/alcance_lista.md)                                                                     |
| 6            | results/metrics/resultados_finales_real.json            | [github.com/ggranizo2507/prediccion-matricula-lemas/blob/main/results/metrics/resultados_finales_real.json](https://github.com/ggranizo2507/prediccion-matricula-lemas/blob/main/results/metrics/resultados_finales_real.json)                       |
| 6            | docs/optimizacion.md · sección 5                        | [github.com/ggranizo2507/prediccion-matricula-lemas/blob/main/docs/optimizacion.md](https://github.com/ggranizo2507/prediccion-matricula-lemas/blob/main/docs/optimizacion.md)                                                                       |
| 6            | docs/diagnostic_report.pdf                              | [github.com/ggranizo2507/prediccion-matricula-lemas/blob/main/docs/diagnostic_report.pdf](https://github.com/ggranizo2507/prediccion-matricula-lemas/blob/main/docs/diagnostic_report.pdf)                                                           |
| 6            | notebooks/overfitting_analysis.ipynb                    | [github.com/ggranizo2507/prediccion-matricula-lemas/blob/main/notebooks/overfitting_analysis.ipynb](https://github.com/ggranizo2507/prediccion-matricula-lemas/blob/main/notebooks/overfitting_analysis.ipynb)                                       |
| 7            | docs/consideraciones_eticas.md · sección 5              | [github.com/ggranizo2507/prediccion-matricula-lemas/blob/main/docs/consideraciones_eticas.md](https://github.com/ggranizo2507/prediccion-matricula-lemas/blob/main/docs/consideraciones_eticas.md)                                                   |
| 7            | docs/ficha_modelo.md · Usos fuera de alcance            | [github.com/ggranizo2507/prediccion-matricula-lemas/blob/main/docs/ficha_modelo.md](https://github.com/ggranizo2507/prediccion-matricula-lemas/blob/main/docs/ficha_modelo.md)                                                                       |
| 8            | Aplicación desplegada (modo demostración)               | [continuidad-matricula-lemas.streamlit.app/](https://continuidad-matricula-lemas.streamlit.app/)                                                                                                                                                     |
| 8            | src/inferencia.py · validar_entrada y revisar_senales   | [github.com/ggranizo2507/prediccion-matricula-lemas/blob/main/src/inferencia.py](https://github.com/ggranizo2507/prediccion-matricula-lemas/blob/main/src/inferencia.py)                                                                             |
| 8            | docs/manual_usuario.md                                  | [github.com/ggranizo2507/prediccion-matricula-lemas/blob/main/docs/manual_usuario.md](https://github.com/ggranizo2507/prediccion-matricula-lemas/blob/main/docs/manual_usuario.md)                                                                   |
| 9            | results/metrics/revision_senales_real.csv               | [github.com/ggranizo2507/prediccion-matricula-lemas/blob/main/results/metrics/revision_senales_real.csv](https://github.com/ggranizo2507/prediccion-matricula-lemas/blob/main/results/metrics/revision_senales_real.csv)                             |
| 9            | results/metrics/permutacion_real.csv                    | [github.com/ggranizo2507/prediccion-matricula-lemas/blob/main/results/metrics/permutacion_real.csv](https://github.com/ggranizo2507/prediccion-matricula-lemas/blob/main/results/metrics/permutacion_real.csv)                                       |
| 9            | src/data_processing.py · verificar_sin_fuga             | [github.com/ggranizo2507/prediccion-matricula-lemas/blob/main/src/data_processing.py](https://github.com/ggranizo2507/prediccion-matricula-lemas/blob/main/src/data_processing.py)                                                                   |
| 9            | config.yaml · prohibidas_en_X                           | [github.com/ggranizo2507/prediccion-matricula-lemas/blob/main/config.yaml](https://github.com/ggranizo2507/prediccion-matricula-lemas/blob/main/config.yaml)                                                                                         |
| 10           | src/evaluate.py · consolidar_familias                   | [github.com/ggranizo2507/prediccion-matricula-lemas/blob/main/src/evaluate.py](https://github.com/ggranizo2507/prediccion-matricula-lemas/blob/main/src/evaluate.py)                                                                                 |
| 10           | config.yaml · capacidad                                 | [github.com/ggranizo2507/prediccion-matricula-lemas/blob/main/config.yaml](https://github.com/ggranizo2507/prediccion-matricula-lemas/blob/main/config.yaml)                                                                                         |
| 10           | docs/modelado.md · sección 9.4                          | [github.com/ggranizo2507/prediccion-matricula-lemas/blob/main/docs/modelado.md](https://github.com/ggranizo2507/prediccion-matricula-lemas/blob/main/docs/modelado.md)                                                                               |
| 10           | docs/planificacion.md · D32                             | [github.com/ggranizo2507/prediccion-matricula-lemas/blob/main/docs/planificacion.md](https://github.com/ggranizo2507/prediccion-matricula-lemas/blob/main/docs/planificacion.md)                                                                     |

**Para la pregunta 8:** cuatro archivos de prueba hechos a partir de `data/synthetic/base_sintetica.csv`, cada uno con un solo cambio: una columna `CI` con 0000000000, `origen_datos = REAL`, las pensiones pagadas tarde en cero, y las pensiones en cero más el tipo de reserva vacío. No contienen datos reales.

## 3. Guion por pregunta

*El texto entre comillas se dice; las marcas «EN PANTALLA» indican qué mostrar en ese momento. Cuando un párrafo termina en dos puntos, se muestra la pantalla y se sigue hablando sobre ella. No hace falta leer literal, pero sí decir las cifras exactas y la limitación final.*

### Pregunta 1 · Problema, usuario y qué hace hoy sin el sistema

**RESPONDE: Guillermo Granizo (en cámara)** · unas 227 palabras, ≈ 1:45 (máximo 2:00)

**Pregunta de la profesora:** *¿Qué problema resuelve su sistema, quién es el usuario y qué haría hoy esa persona sin él?*

> **Al empezar:** «Hola, soy Guillermo Granizo. Trabajo en LEMAS y en este proyecto fui el Product Owner. Me tocan las preguntas impares.»
>
> «Pregunta 1. Les cuento cómo se vive esto en el colegio. Entre septiembre y noviembre, las familias reservan el cupo del año siguiente. Y cada año pasa lo mismo: entre 6 y 11 de cada 100 estudiantes con la reserva aprobada no pagan la matrícula a tiempo. Lo peor es que nos enteramos al final, el 30 de abril, cuando ya no queda tiempo para conversar con nadie.»
>
> **EN PANTALLA →** README, sección «Descripción del problema».
>
> «¿Quién vive ese problema? Secretaría y Admisiones de las dos sedes: unas 10 personas que, el 20 de febrero, tienen por delante más de mil familias y 69 días.»
>
> «Hoy, sin el sistema, se llama como se puede, sin un orden basado en datos, y no se alcanza a todas. Con el sistema, Secretaría carga el mismo Excel de siempre y recibe esto:»
>
> **EN PANTALLA →** Aplicación: pestaña «Lista de contactos», columna «Motivo» (5 segundos).
>
> «una lista de 165 familias, 118 en Mucho Lote 1 y 47 en Mucho Lote 2, cada una con el motivo de la llamada. En la prueba con la matrícula 2026–2027, la lista encontró a 22 de las 74 familias que no pagaron a tiempo; al azar habríamos encontrado unas 11. Eso sí, siendo honestos: el sistema nos dice a quién llamar primero, pero todavía no sabemos si esa llamada cambia la decisión de la familia.»

**Nota:** En la demostración la app usa datos sintéticos, así que la barra lateral muestra otros valores de k (119 y 88). Los 118 y 47 son los de los datos reales.

| **Criterio de la rúbrica**     | **Cómo lo cubre esta respuesta**                                                  |
|--------------------------------|-----------------------------------------------------------------------------------|
| Precisión técnica (0–4)        | Cifras: 6–11 de cada 100, 10 personas, 69 días, 165 familias (118 y 47), 22 de 74 |
| Defensa de decisiones (0–3)    | Por qué importa: el colegio se entera tarde y no alcanza a llamar a todos         |
| Evidencia (0–2)                | README y lista con motivo en la app                                               |
| Honestidad sobre límites (0–1) | No sabemos si la llamada cambia la decisión                                       |

### Pregunta 2 · Datos, limitaciones y preprocesamiento clave

**RESPONDE: José Ulloa (en cámara)** · unas 215 palabras, ≈ 1:40 (máximo 2:00)

**Pregunta de la profesora:** *¿De dónde vienen sus datos y qué limitaciones tienen (tamaño, sesgos, desbalance)? ¿Qué decisión de preprocesamiento fue la más importante y qué habría pasado sin ella?*

> **Al empezar:** «Hola, soy José Ulloa, el Scrum Master del proyecto. Yo respondo las preguntas pares.»
>
> «Pregunta 2. Nuestros datos no vienen de internet: son los registros reales de LEMAS, el Excel que Secretaría lleva desde 2021. Son seis años, 9.031 registros, 2.733 estudiantes y 2.017 familias, usados con autorización del colegio. Lo primero que hicimos fue cambiar las cédulas por seudónimos; la clave se quedó con una persona de LEMAS.»
>
> **EN PANTALLA →** docs/hoja_de_datos.md (tabla de la hoja de datos).
>
> «Tienen tres limitaciones. Son pocos casos: para entrenar había 193, unos 6 por variable cuando lo recomendable es 10; por eso usamos modelos simples. Hay desbalance: el evento es del 6 a 11 %. Y hay sesgos: solo vemos datos administrativos, no los motivos de la familia, y los pagos reflejan su situación económica.»
>
> «¿La decisión de preprocesamiento más importante? Una que casi se nos pasa. Un representante aparecía con 39 estudiantes. No era una familia enorme: era una cédula genérica que se usa para familias extranjeras.»
>
> **EN PANTALLA →** docs/analisis_datos.md, tabla de problemas de calidad (D27, D28, D29).
>
> «Sin corregirla, el modelo veía un grupo falso de 38 hermanos con 92 % de no matrícula. El ROC-AUC subía de 0,54 a 0,59 por un error, y la nacionalidad se colaba por la puerta de atrás. Desde la decisión D29, cada uno de esos estudiantes cuenta como un contacto individual, y esa marca nunca se usa para predecir.»

| **Criterio de la rúbrica**     | **Cómo lo cubre esta respuesta**                                                          |
|--------------------------------|-------------------------------------------------------------------------------------------|
| Precisión técnica (0–4)        | 9.031 registros, 193 eventos, EPV ≈ 6, 6–11 %, 38 hermanos, ROC-AUC 0,54 → 0,59           |
| Defensa de decisiones (0–3)    | Por qué la cédula genérica era la decisión clave y qué se descartó (usarla como variable) |
| Evidencia (0–2)                | Hoja de datos y tabla de problemas de calidad                                             |
| Honestidad sobre límites (0–1) | Sin motivos de la familia; EPV bajo; pagos que reflejan la situación económica            |

### Pregunta 3 · Por qué este modelo y comparación con el baseline

**RESPONDE: Guillermo Granizo (en cámara)** · unas 206 palabras, ≈ 1:36 (máximo 2:00)

**Pregunta de la profesora:** *¿Por qué eligieron este modelo y no las otras técnicas que compararon? Muestren la comparación con el baseline.*

> «Pregunta 3. La respuesta corta: elegimos la regla D2 porque fue la que mejor funcionó en un año que nunca había visto, y porque explica cada llamada. Les muestro cómo llegamos ahí.»
>
> **EN PANTALLA →** docs/modelado.md, sección 2 (tabla de selección en C4) y figura real_09_seleccion_c4.
>
> «Pusimos a competir seis opciones: tres modelos de aprendizaje automático, una regresión logística, un gradient boosting y una logística híbrida, contra tres referencias: llamar al azar, la regla D, que ordena por más atrasos, y la regla D2, de tres señales administrativas. En el año de selección, C4, ganó D2 con un Lift de 1,93. Detrás quedaron D con 1,86, la híbrida con 1,53, la logística con 1,40 y el gradient boosting con 1,06.»
>
> **EN PANTALLA →** docs/modelado.md, sección 3 (prueba final en C5) y figura real_12_prueba_c5.
>
> «Después vino la prueba de verdad: un año nuevo, una sola vez y con todo congelado. D2 dio 1,97, con un intervalo de 1,24 a 2,56 que no toca el 1. El azar dio 1,08. ¿Y la híbrida? 0,98, lo mismo que el azar. Ahí confirmamos la decisión.»
>
> «Algo que queremos decir con claridad: D2 no le gana a la regla D de forma demostrable. La diferencia entre las dos es 0,00, con un intervalo de −0,62 a 0,62. Las dos superan al azar, y nos quedamos con D2 porque le dice a Secretaría por qué llamar a cada familia.»

| **Criterio de la rúbrica**     | **Cómo lo cubre esta respuesta**                                                       |
|--------------------------------|----------------------------------------------------------------------------------------|
| Precisión técnica (0–4)        | C4: 1,93 / 1,86 / 1,53 / 1,40 / 1,06; C5: 1,97 \[1,24; 2,56\], azar 1,08, híbrida 0,98 |
| Defensa de decisiones (0–3)    | Regla de decisión previa, generalización y explicabilidad; alternativas descartadas    |
| Evidencia (0–2)                | Tablas y figuras de C4 y C5                                                            |
| Honestidad sobre límites (0–1) | D2 no supera a D de forma demostrable                                                  |

### Pregunta 4 · Sensibilidad de hiperparámetros (Workshop S5)

**RESPONDE: José Ulloa (en cámara)** · unas 208 palabras, ≈ 1:41 (máximo 2:00)

**Pregunta de la profesora:** *Según el análisis de sensibilidad del Workshop S5, ¿qué hiperparámetros pesaron más y qué mejora cuantificable lograron entre antes y después?*

> «Pregunta 4. En pocas palabras: lo que más pesó fue lo que controla cuánto memoriza el modelo. Les explico cómo lo medimos.»
>
> «Optimizamos con Optuna: 60 pruebas por modelo, 180 en total, entrenando con un año y validando con el siguiente para no mirar nunca el futuro. Después analizamos esas 180 pruebas, sin reentrenar, con fANOVA, dependencia parcial y el H² de Friedman.»
>
> **EN PANTALLA →** docs/optimizacion.md, sección 2 bis, y figura real_31_importancia_hiperparametros.
>
> «En el gradient boosting, un solo hiperparámetro explica el 90 % de la variación: el tamaño mínimo de hoja. Fíjense en este escalón:»
>
> **EN PANTALLA →** Figura real_32_dependencia_parcial (escalón del tamaño de hoja y meseta de C).
>
> «con hojas de menos de unos 80 estudiantes, la PR-AUC cae a 0,073, porque el árbol empieza a memorizar casos. En la regresión logística manda la regularización C: si es muy fuerte, el modelo se aplana, y desde C cerca de 1 hay una meseta. fANOVA pone primero al balanceo, pero las otras dos medidas ponen a C. Las interacciones son débiles, con un H² de 0,04 como máximo.»
>
> «¿Cuánto mejoramos? En la validación interna, la regresión logística pasó de 0,079 a 0,106, un 34 % más. Pero aquí está la lección: esa mejora no llegó al año siguiente. En C4, la logística bajó de 1,53 a 1,40. El límite no estaba en los hiperparámetros, sino en la señal de los datos.»
>
> **EN PANTALLA →** docs/optimizacion.md, tabla «Antes y después de la búsqueda».

| **Criterio de la rúbrica**     | **Cómo lo cubre esta respuesta**                                                                   |
|--------------------------------|----------------------------------------------------------------------------------------------------|
| Precisión técnica (0–4)        | min_samples_leaf 90 %; C con meseta desde ≈ 1; H² ≤ 0,04; 0,079 → 0,106 (+34 %); 1,53 → 1,40 en C4 |
| Defensa de decisiones (0–3)    | Por qué la PR-AUC como objetivo y por qué seleccionar en C4                                        |
| Evidencia (0–2)                | Figuras 31 y 32 y tabla antes/después                                                              |
| Honestidad sobre límites (0–1) | La mejora interna no se trasladó a C4                                                              |

### Pregunta 5 · Por qué esta métrica y un caso donde falla

**RESPONDE: Guillermo Granizo (en cámara)** · unas 204 palabras, ≈ 1:35 (máximo 2:00)

**Pregunta de la profesora:** *¿Por qué la métrica que eligieron es la adecuada para su problema? Muestren un caso donde el modelo falla y expliquen por qué.*

> «Pregunta 5. Usamos el Lift por familia, y la razón es muy práctica. Secretaría no decide con un umbral de probabilidad: decide a quién llamar con un número fijo de llamadas, 165. Entonces la pregunta útil es: con esas llamadas, ¿cuántas familias en riesgo encontramos, frente a llamar al azar? Medimos por familia porque se llama al representante, no a cada hijo. Y descartamos la exactitud por el desbalance: con 6,8 % de casos, decir que todos se matriculan acierta el 93 %, y no sirve para nada.»
>
> «Ahora, un caso donde falla. Miren esta familia:»
>
> **EN PANTALLA →** Aplicación: pestaña «Evaluar un estudiante», con pago en plazo, reserva ordinaria y 0 pensiones atrasadas → prioridad baja.
>
> «pagó a tiempo el año anterior, hizo una reserva ordinaria y no tiene pensiones atrasadas. La regla le da prioridad baja. Si esta familia no se matricula, no la vamos a llamar. Y no es un caso raro: es el más común.»
>
> **EN PANTALLA →** Figura real_24_alcance_desglose (a quién encuentra la lista).
>
> «En los años anteriores, el 86 % de los casos fueron familias que no registran ningún pago, y la lista solo encontró al 24 % de ellas. Falla porque, el 20 de febrero, esas familias no dejan ninguna huella en los datos. También hay falsos positivos: de cada 8 familias que llamamos, unas 7 sí se matriculan. Por suerte, ese error cuesta solo una llamada amable.»

| **Criterio de la rúbrica**     | **Cómo lo cubre esta respuesta**                                 |
|--------------------------------|------------------------------------------------------------------|
| Precisión técnica (0–4)        | 165 llamadas, 6,8 %, 93 % trivial, 22 de 74, 86 % sin pago, 24 % |
| Defensa de decisiones (0–3)    | Por qué Lift@k por familia y por qué no exactitud ni F1          |
| Evidencia (0–2)                | Consulta en la app y figura 24                                   |
| Honestidad sobre límites (0–1) | 70 % de los casos sin señal; 7 de cada 8 llamadas sin caso       |

### Pregunta 6 · Sobreajuste y datos nuevos

**RESPONDE: José Ulloa (en cámara)** · unas 195 palabras, ≈ 1:32 (máximo 2:00)

**Pregunta de la profesora:** *¿Cómo comprobaron que el modelo no sufre overfitting y que funcionaría con datos nuevos?*

> «Pregunta 6. Lo comprobamos de tres maneras, y la más importante fue no hacernos trampa con el tiempo.»
>
> «Primero, validación temporal: entrenamos con dos años, elegimos con el tercero y probamos una sola vez con el último, C5. Antes de abrirlo congelamos el sistema y registramos su huella SHA-256; aquí está.»
>
> **EN PANTALLA →** results/metrics/resultados_finales_real.json, campo sha256_sistema.
>
> «Segundo, comparamos el entrenamiento con el año de selección. El gradient boosting tenía 0,245 de PR-AUC entrenando y 0,103 en C4: una brecha de 58 %. Eso es sobreajuste de libro, y por eso lo descartamos.»
>
> **EN PANTALLA →** docs/optimizacion.md, sección 5 (tabla de diagnóstico) y docs/diagnostic_report.pdf (curvas de pérdida).
>
> «Las logísticas casi no tienen brecha, 0,140 frente a 0,113 y 0,126 frente a 0,125: no memorizan, simplemente no hay más señal. Las curvas de aprendizaje lo confirman, y ninguna de las siete estrategias que probamos, como regularizar más o parar antes, cambió la validación de forma demostrable.»
>
> «Tercero, datos nuevos: en C5, D2 mantuvo 1,97, mientras la híbrida cayó a 0,98. Y D2 superó al azar en los cuatro años: 1,38, 1,49, 1,93 y 1,97. ¿Los límites? Solo tenemos cuatro años comparables, el 1,93 de C4 salió de un sorteo de empates favorable, porque el promedio es 1,77, y la híbrida se diseñó después de ver C4.»

| **Criterio de la rúbrica**     | **Cómo lo cubre esta respuesta**                                                             |
|--------------------------------|----------------------------------------------------------------------------------------------|
| Precisión técnica (0–4)        | 0,245 / 0,103 (58 %); 0,140 / 0,113; 0,126 / 0,125; C5 1,97 frente a 0,98; 1,38–1,97         |
| Defensa de decisiones (0–3)    | Por qué validación temporal y no cruzada aleatoria; por qué se descartó el gradient boosting |
| Evidencia (0–2)                | Huella SHA-256, tabla de diagnóstico y curvas                                                |
| Honestidad sobre límites (0–1) | Cuatro cohortes, sorteo favorable (media 1,77), selección adaptativa                         |

### Pregunta 7 · Riesgo ético principal, medidas y usos prohibidos

**RESPONDE: Guillermo Granizo (en cámara)** · unas 202 palabras, ≈ 1:35 (máximo 2:00)

**Pregunta de la profesora:** *¿Cuál es el riesgo ético o social más importante de su proyecto (sesgo, privacidad, uso indebido) y qué medida concreta implementaron? ¿En qué casos no debería usarse?*

> «Pregunta 7. Para mí, el riesgo más serio no es técnico: es que la lista se use mal. Las señales que funcionan son de pagos, y los pagos reflejan cómo está económicamente una familia. Si alguien usara esta lista para cobrar, o para negar un cupo o una beca, castigaría justo a quien más ayuda necesita.»
>
> «Hay además un posible sesgo que no escondemos:»
>
> **EN PANTALLA →** docs/consideraciones_eticas.md, sección 5 (tabla de equidad con intervalos de Wilson).
>
> «la lista encontró menos casos entre las familias becadas, 18 frente a 32 de cada 100. Con solo 11 casos no podemos afirmar que sea real, la prueba de Fisher da 0,49, pero tampoco descartarlo, así que se revisa cada mayo.»
>
> «¿Qué hicimos en concreto? La lista muestra el motivo de la llamada, nunca probabilidades ni montos. La nacionalidad no se usa. Las cédulas se cambian por seudónimos. La aplicación pública solo acepta datos inventados, y los nombres solo se ven dentro de LEMAS. Siempre decide una persona, y la ficha del modelo prohíbe por escrito usarla para cobrar o excluir.»
>
> **EN PANTALLA →** docs/ficha_modelo.md, sección 2, «Usos fuera de alcance».
>
> «No debe usarse para decidir cupos, reservas o becas, para evaluar al personal, con estudiantes nuevos, ni en otro colegio sin validarla otra vez. Y antes de usarla de verdad, LEMAS tiene que informar a las familias.»

| **Criterio de la rúbrica**     | **Cómo lo cubre esta respuesta**                                          |
|--------------------------------|---------------------------------------------------------------------------|
| Precisión técnica (0–4)        | 18 % frente a 32 %, 11 casos, p = 0,49                                    |
| Defensa de decisiones (0–3)    | Por qué el uso indebido es el riesgo principal y qué medidas se eligieron |
| Evidencia (0–2)                | Tabla de equidad y ficha del modelo                                       |
| Honestidad sobre límites (0–1) | Familias aún no informadas; base legal pendiente                          |

### Pregunta 8 · Entrada inválida, error y diseño para el usuario (grabación de pantalla)

**RESPONDE: José Ulloa (en cámara)** · unas 167 palabras, ≈ 1:48 (máximo 2:00)

**Pregunta de la profesora:** *Con grabación de pantalla, muestren cómo la interfaz maneja una entrada inválida y un error. ¿Qué decisiones de diseño tomaron pensando en el usuario final?*

> «Pregunta 8. Lo mejor es verlo. Esta es la aplicación real, la que se despliega desde nuestro repositorio.»
>
> **EN PANTALLA →** Pestaña «Evaluar un estudiante»: escribir 11 en «Promedio final (0–10)» y pulsar «Estimar».
>
> «Empiezo con una entrada inválida: pongo 11 de promedio. La aplicación no calcula; me dice que debe ser un número entre 0 y 10.»
>
> **EN PANTALLA →** Barra lateral, «…o suba la base (CSV)»: subir prueba_con_cedulas.csv. Luego subir prueba_no_sintetica.csv.
>
> «Ahora un error más serio: subo un archivo que trae una columna de cédulas. Lo rechaza antes de procesarlo y explica por qué: la versión pública nunca recibe cédulas. Igual si los datos no vienen marcados como sintéticos.»
>
> **EN PANTALLA →** Subir prueba_una_senal_en_cero.csv y pulsar «Generar lista» (aviso amarillo). Luego prueba_dos_senales_caidas.csv (aviso rojo).
>
> «Y este es mi favorito: si el Excel llega con las pensiones atrasadas en cero, la lista se genera, pero avisa en amarillo. Si fallan dos señales, el aviso se pone rojo y pide corregir el Excel antes de usarla.»
>
> «Todo esto lo diseñamos pensando en Secretaría: en español y con coma decimal, con un botón para practicar con un ejemplo, con el motivo de cada familia en palabras y sin probabilidades ni montos. Una limitación: estos controles evitan errores, pero no detienen a quien quiera saltárselos.»

**Nota:** Los cuatro archivos de prueba se hicieron a partir de `data/synthetic/base_sintetica.csv`, con un solo cambio cada uno (columna `CI` con 0000000000; `origen_datos = REAL`; pensiones en cero; pensiones en cero y tipo de reserva vacío). Los mensajes de este guion se comprobaron con la aplicación del repositorio.

| **Criterio de la rúbrica**     | **Cómo lo cubre esta respuesta**                              |
|--------------------------------|---------------------------------------------------------------|
| Precisión técnica (0–4)        | Mensajes reales de la app (verificados)                       |
| Defensa de decisiones (0–3)    | Por qué rechazar antes de procesar y por qué avisos por nivel |
| Evidencia (0–2)                | Grabación de la app real del repositorio                      |
| Honestidad sobre límites (0–1) | Barrera contra errores, no contra mala fe                     |

### Pregunta 9 · Opción A · Variables importantes y fuga de datos

**RESPONDE: Guillermo Granizo (en cámara)** · unas 213 palabras, ≈ 1:39 (máximo 2:00)

**Pregunta de la profesora:** *Opción A (datos tabulares): ¿Qué variables resultaron más importantes y coincide eso con lo que esperaban del dominio? ¿Cómo evitaron fuga de datos (data leakage) al dividir los datos?*

> «Pregunta 9, opción A, porque nuestro proyecto es de datos tabulares. Lo que más pesó fueron tres señales que el colegio ya tenía.»
>
> **EN PANTALLA →** results/metrics/revision_senales_real.csv (riesgos relativos) y results/metrics/permutacion_real.csv.
>
> «Quien pagó tarde la matrícula anterior tiene casi tres veces más riesgo, 2,95; la reserva extraordinaria, 1,50; y tener pensiones atrasadas, 1,32. Esto lo calculamos solo con los años de entrenamiento, y la permutación en el modelo híbrido apunta a lo mismo.»
>
> «¿Coincide con lo que esperábamos? En buena parte, sí. Desde Secretaría intuíamos que los pagos dicen mucho. Lo que me sorprendió fue lo académico: el promedio y la conducta casi no ayudan. El 94 % de los estudiantes tiene A en conducta, así que no distingue a nadie.»
>
> **EN PANTALLA →** src/data_processing.py, función verificar_sin_fuga, y config.yaml, lista prohibidas_en_X.
>
> «La fuga de datos la cuidamos desde el diseño. Dividimos por años, nunca al azar, y el último año se abrió una sola vez. Cada dato es lo que se sabía el 20 de febrero: los atrasos se cuentan de mayo a enero, y LEMAS confirmó que el promedio final ya está cerrado ese día. El preprocesamiento se ajusta solo con el entrenamiento, y esta función detiene todo si se cuela el resultado o un identificador. Un límite: el orden de las señales lo vimos primero con todos los años; lo repetimos solo con los tres primeros y sale igual.»

| **Criterio de la rúbrica**     | **Cómo lo cubre esta respuesta**                                     |
|--------------------------------|----------------------------------------------------------------------|
| Precisión técnica (0–4)        | RR 2,95 / 1,50 / 1,32; 94 % con A; atrasos mayo a enero              |
| Defensa de decisiones (0–3)    | Por qué división temporal y no aleatoria; por qué pipeline           |
| Evidencia (0–2)                | Tablas de riesgo y permutación, código anti-fuga                     |
| Honestidad sobre límites (0–1) | Orden de señales visto con todas las cohortes (comprobado con C1–C3) |

### Pregunta 10 · La decisión más difícil: medir por familia con k fijo

**RESPONDE: José Ulloa (en cámara)** · unas 205 palabras, ≈ 1:36 (máximo 2:00)

**Pregunta de la profesora:** *Elijan la decisión técnica más difícil o importante de su proyecto (distinta de las ya preguntadas). ¿Qué alternativas consideraron y por qué eligieron esa?*

> «Pregunta 10. La decisión que más discutimos fue algo que parece simple: cómo medir si el sistema funciona. Al final decidimos medir por familia, con un número fijo de llamadas, y no por estudiante con un umbral.»
>
> «Teníamos alternativas. Podíamos clasificar estudiantes con un umbral de 0,5 y medir exactitud o F1, pero con 6,8 % de casos eso premia decir que todos se matriculan. Podíamos buscar el umbral de menor costo, pero no hay montos confiables, y el número de llamadas no lo fija un umbral: lo fija el personal.»
>
> «¿Por qué la familia? Porque se llama al representante. Si dos hermanos están en riesgo, es una sola llamada; contarlos dos veces inflaría el resultado.»
>
> **EN PANTALLA →** src/evaluate.py, función consolidar_familias, y config.yaml, sección capacidad (multiplicador_k: 2).
>
> «Por eso esta función consolida por familia, y k se fijó por sede en el doble del promedio histórico de casos: 118 y 47, menos de dos llamadas por persona a la semana.»
>
> «Tuvo consecuencias que reconocemos. Nuestro azar da 1,08 y no 1,00, porque las familias con más hijos tenían más números en el sorteo. Lo comprobamos: con un sorteo por familia da 1,00, así que nuestra comparación era más exigente, no menos. Y k fue una decisión, no una medición; la Dirección puede cambiarla en la aplicación.»
>
> **EN PANTALLA →** docs/modelado.md, sección 9.4.

| **Criterio de la rúbrica**     | **Cómo lo cubre esta respuesta**                            |
|--------------------------------|-------------------------------------------------------------|
| Precisión técnica (0–4)        | k = 118 y 47 (2 × promedio), 6,8 %, azar 1,08 frente a 1,00 |
| Defensa de decisiones (0–3)    | Tres alternativas descartadas y por qué                     |
| Evidencia (0–2)                | Código de consolidación y configuración de k                |
| Honestidad sobre límites (0–1) | k fue una decisión, no una medición                         |

## 4. Cifras de respaldo y dónde están

Si alguna cifra se dice distinto en la grabación, la respuesta puede contradecir el repositorio. Esta tabla sirve para revisar el video antes de entregarlo.

| **Cifra**                                                                                         | **Pregunta** | **Fuente en el repositorio**                                 |
|---------------------------------------------------------------------------------------------------|--------------|--------------------------------------------------------------|
| 9.031 registros, 2.733 estudiantes, 2.017 familias, seis ciclos                                   | 1, 2         | docs/hoja_de_datos.md                                        |
| No matrícula entre 6 y 11 de cada 100 según el ciclo; 6,8 % de familias en C5                     | 1, 2, 5, 10  | docs/ficha_modelo.md §5; modelado.md §3                      |
| 10 personas, 69 días (20-feb a 30-abr), k = 118 y 47 (165)                                        | 1, 10        | README; config.yaml (capacidad)                              |
| 193 eventos de entrenamiento, EPV ≈ 6,2 (umbral 10)                                               | 2            | docs/modelado.md §2.1                                        |
| Cédula genérica: 39 estudiantes, falso grupo de 38 hermanos con 92 %; ROC-AUC 0,54 → 0,59         | 2            | docs/analisis_datos.md; banco_preguntas.md 14 bis; D29 y D33 |
| C4: D2 1,93 · D 1,86 · híbrida 1,53 · logística 1,40 · gradient boosting 1,06                     | 3            | docs/modelado.md §2                                          |
| C5: D2 1,97 \[1,24; 2,56\] · D 1,70 · híbrida 0,98 · azar 1,08 · 22 de 74 casos                   | 1, 3, 5, 6   | docs/modelado.md §3                                          |
| D2 − D en C4: 0,00 \[−0,62; 0,62\]                                                                | 3            | docs/modelado.md §9.3                                        |
| Optuna: 60 pruebas por modelo, 180 en total, C2 → C3, PR-AUC                                      | 4            | docs/optimizacion.md §1                                      |
| Tamaño mínimo de hoja 90 %; balanceo 58 % y C 38 % (fANOVA); H² ≤ 0,04                            | 4            | docs/optimizacion.md §2 bis                                  |
| Antes y después: logística 0,079 → 0,106 (+34 %); gradient boosting 0,075 → 0,089; C4 1,53 → 1,40 | 4            | docs/optimizacion.md §2 y §2 bis                             |
| PR-AUC entrenamiento / C4: 0,245 / 0,103 (58 %); 0,140 / 0,113; 0,126 / 0,125                     | 6            | docs/optimizacion.md §5                                      |
| Lift de D2 por cohorte: 1,38 · 1,49 · 1,93 · 1,97; media de 500 sorteos en C4: 1,77               | 6            | docs/modelado.md §7 y §9.2                                   |
| 86 % de los casos sin ningún pago; la lista encuentra al 24 % (C2–C4)                             | 5            | docs/alcance_lista.md; figura 24                             |
| Becadas 18 % frente a 32 % de Recall@k, 11 casos, Fisher p = 0,49                                 | 7            | docs/consideraciones_eticas.md §5                            |
| Riesgo relativo C2–C3: 2,95 · 1,50 · 1,32; conducta A en el 94 %                                  | 9            | revision_senales_real.csv; analisis_datos.md §5              |
| Azar por estudiante 1,12 y por familia 1,00 en C4                                                 | 10           | docs/modelado.md §9.4                                        |

## 5. Después de grabar

- Revisar que cada respuesta dure menos de 2:00 y empiece con «Pregunta N».

- Comprobar que Guillermo aparece en las impares y José en las pares, con la cara visible.

- Verificar que no aparece ningún dato real, nombre ni cédula en pantalla.

- Subir el video y agregar el enlace en la sección Videos del README .
