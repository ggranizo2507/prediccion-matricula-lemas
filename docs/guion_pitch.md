# Guion del video pitch (5 minutos)

Guion con el que se grabó el [video pitch](https://drive.google.com/file/d/1Ro0GUAUccS-o9rC0LBZr2Z77k66DGZuU/view?usp=sharing). Acompaña a la presentación de 10 diapositivas, que está en [`docs/pitch/Pitch_Continuidad_LEMAS.pdf`](pitch/Pitch_Continuidad_LEMAS.pdf). El video está pensado para quien necesita la solución (la Dirección y Secretaría de LEMAS) y cubre los siete bloques obligatorios de la guía del proyecto.

Hablan Guillermo Granizo (Product Owner) y José Ulloa (Scrum Master).

## 1. Enfoque del pitch

El video no es una clase: le habla a quien necesita la solución, la Dirección y Secretaría de LEMAS, que no son personas técnicas. Cumple los siete bloques obligatorios de la guía, pero cada término técnico se traduce a lo que cambia en el trabajo del colegio.

### La propuesta de valor en una frase

> Para la Dirección y Secretaría de LEMAS, que cada febrero no alcanzan a llamar a todas las familias con reserva aprobada, **Continuidad estudiantil** es una herramienta que ordena a quién llamar primero y **encuentra el doble de familias en riesgo con las mismas llamadas**. A diferencia de llamar al azar o por orden de lista, cada familia llega con el motivo de la llamada, y solo usa el Excel que el colegio ya tiene.

### Antes y después, con los números del colegio

| **Indicador (prueba con la matrícula 2026–2027)** | **Hoy (al azar)** | **Con la lista**                |
|---------------------------------------------------|-------------------|---------------------------------|
| Familias en riesgo encontradas con 165 llamadas   | ≈ 11 de 74        | 22 de 74                        |
| Llamadas por cada caso encontrado                 | ≈ 15              | 7,5                             |
| Casos alcanzados llamando al 15 % de las familias | 15 %              | 30 %                            |
| Costo adicional                                   | —                 | Ninguno: usa el Excel existente |

*Fuente: prueba única en C5 (1.093 familias, 74 casos); Lift 1,97 con margen de 1,24 a 2,56. Detalle en [ficha_modelo.md](ficha_modelo.md).*

### Del modelo al valor: cómo traducimos lo técnico

| **Lo que dice el equipo técnico**       | **Lo que el cliente se pregunta** | **Cómo lo decimos**                                                                                    |
|-----------------------------------------|-----------------------------------|--------------------------------------------------------------------------------------------------------|
| Lift@k = 1,97 \[1,24; 2,56\]            | ¿Cuánto mejor que hoy?            | Con 165 llamadas encontramos 22 familias en riesgo; al azar, unas 11                                   |
| Seudonimización HMAC-SHA256             | ¿Mis datos están seguros?         | Nombres y cédulas cambiados por códigos; la clave la guarda una persona del colegio                    |
| Validación temporal, prueba única en C5 | ¿Funciona con un año nuevo?       | Aprendimos de años pasados y lo probamos una sola vez con un año nuevo, sin mirarlo antes              |
| Optuna, sensibilidad de hiperparámetros | ¿Por qué no algo más avanzado?    | Probamos 180 ajustes de tres modelos de IA; ninguno superó a la regla, que además explica cada llamada |
| Recall@k = 0,30                         | ¿Y cuándo falla?                  | Llega a 3 de cada 10 casos; los otros 7 no dejan señal el 20 de febrero                                |

## 2. Quién habla y cuándo entra

Hablan los dos. Hay cuatro cambios de voz; cada uno empieza justo después de una frase de paso del compañero. Guillermo abre, presenta la demostración y cierra; José explica los datos, el desarrollo y la ética.

| **\#** | **Tiempo** | **Bloque de la guía**                | **Diapositiva**           | **Habla** | **Palabras** |
|--------|------------|--------------------------------------|---------------------------|-----------|--------------|
| 1      | 0:00–0:15  | 1\. Introducción y problema (30 s)   | Portada                   | Guillermo | 37           |
| 2      | 0:15–0:30  | 1\. Introducción y problema (30 s)   | El problema               | Guillermo | 41           |
| 3      | 0:30–1:00  | 2\. Datos y metodología (1 min)      | Los datos                 | José      | 77           |
| 4      | 1:00–1:30  | 2\. Datos y metodología (1 min)      | Cómo lo construimos       | José      | 76           |
| 5      | 1:30–2:15  | 3\. Desarrollo y optimización (45 s) | Desarrollo y optimización | José      | 106          |
| 6      | 2:15–3:15  | 4\. La solución en acción (1 min)    | La solución en acción     | Guillermo | 104          |
| 7      | 3:15–3:40  | 5\. Evaluación y resultados (45 s)   | Resultados                | Guillermo | 65           |
| 8      | 3:40–4:00  | 5\. Evaluación y resultados (45 s)   | Dónde funciona y dónde no | Guillermo | 53           |
| 9      | 4:00–4:45  | 6\. Consideraciones éticas (45 s)    | Ética                     | José      | 109          |
| 10     | 4:45–5:00  | 7\. Cierre (15 s)                    | Cierre                    | Guillermo | 41           |

*Total: 709 palabras en 5:00, dentro de las 650 a 750 que recomienda la guía. Ninguna diapositiva pasa de unas 165 palabras por minuto.*

### Los cuatro cambios de voz

| **Momento** | **Pasa de → a**  | **Señal de entrada**                                                                                 |
|-------------|------------------|------------------------------------------------------------------------------------------------------|
| 0:30        | Guillermo → José | Guillermo termina: «¿A quién llamar primero?». José empieza: «Para resolverlo…»                      |
| 2:15        | José → Guillermo | José termina: «Guillermo les muestra cómo se usa». Empieza la grabación de pantalla                  |
| 4:00        | Guillermo → José | Guillermo termina: «José les explica cómo la cuidamos». José empieza: «Son datos de menores…»        |
| 4:45        | José → Guillermo | José termina: «hay que informar a las familias». Guillermo cierra: «Con lo que el colegio ya tiene…» |

## 3. Guion palabra por palabra

*No hace falta leerlo literal: lo importante es decir las cifras exactas y respetar los tiempos. Pausa breve después de cada cifra grande.*

### Bloque 1. Introducción y problema (30 s)

**Diapositiva 1 · Portada** 0:00–0:15 (15 s)

**HABLA: Guillermo Granizo** *· Abre el video.*

> «Hola, soy Guillermo Granizo y él es José Ulloa. Les presentamos Continuidad estudiantil en LEMAS: una herramienta que le dice al colegio a qué familias llamar primero, para no enterarnos tarde de que un estudiante no volverá.»

**En pantalla:** Portada: nombre del proyecto, frase de valor y los dos integrantes.

**Diapositiva 2 · El problema** 0:15–0:30 (15 s)

**HABLA: Guillermo Granizo**

> «Cada año, entre 6 y 11 de cada 100 estudiantes con reserva aprobada no pagan la matrícula a tiempo, y lo sabemos cuando ya es tarde. Hay 69 días y 10 personas para más de mil familias. ¿A quién llamar primero?»

**En pantalla:** Tres cifras grandes (6 a 11 de cada 100 · 69 días · 10 personas) y la pregunta.

### Bloque 2. Datos y metodología (1 min)

**Diapositiva 3 · Los datos** 0:30–1:00 (30 s)

**HABLA: José Ulloa** *· Entra José cuando Guillermo termina «¿A quién llamar primero?».*

> «Para resolverlo usamos lo que el colegio ya tiene: seis años del Excel de Secretaría, unos 9.000 registros de 2.700 estudiantes, con autorización de LEMAS. Antes de tocarlos, cambiamos nombres y cédulas por códigos; la clave la guarda una persona del colegio. En la limpieza corregimos tres problemas que cambiaban los resultados, como cursos escritos de dos formas. Y solo usamos lo que se sabe el 20 de febrero, el día en que se arma la lista.»

**En pantalla:** Cifras de los datos a la izquierda; a la derecha, protegidos, limpios y sin mirar el futuro.

**Diapositiva 4 · Cómo lo construimos** 1:00–1:30 (30 s)

**HABLA: José Ulloa**

> «Aprendimos de los años pasados y probamos con un año nuevo, la matrícula 2026–2027, una sola vez y sin mirarlo antes. Pusimos a competir tres modelos de inteligencia artificial, dos regresiones logísticas y un modelo de árboles de decisión, contra dos reglas simples y contra llamar al azar. Ganó una regla de tres señales: primero quien pagó tarde la matrícula anterior, luego quien hizo reserva extraordinaria y, dentro de cada grupo, quien tiene más pensiones atrasadas.»

**En pantalla:** Línea de tiempo: aprender, elegir y probar una vez. Los competidores y la regla ganadora en tres pasos.

### Bloque 3. Desarrollo y optimización (45 s)

**Diapositiva 5 · Desarrollo y optimización** 1:30–2:15 (45 s)

**HABLA: José Ulloa**

> «El reto principal fue que hay pocos casos, unos 200 en dos años, y cada año es distinto. Con tan pocos casos, un programa complejo memoriza el pasado y falla con el año nuevo. Probamos 180 ajustes con Optuna, siempre respetando el orden del tiempo. El análisis de sensibilidad mostró que lo que más importa es frenar esa memorización: en el modelo de árboles, el tamaño mínimo de cada hoja explica el 90 % de la diferencia. Ajustar mejoró la práctica interna, pero no el año siguiente. Por eso elegimos la regla: rinde igual o mejor y explica cada llamada. Guillermo les muestra cómo se usa.»

**En pantalla:** El reto, los 180 ajustes y lo que más importa; abajo, la conclusión.

### Bloque 4. La solución en acción (1 min)

**Diapositiva 6 · La solución en acción** 2:15–3:15 (60 s)

**HABLA: Guillermo Granizo** *· Entra Guillermo cuando José termina «Guillermo les muestra cómo se usa».*

> «Esta es la aplicación real, en modo demostración, con datos inventados. El 20 de febrero, Secretaría carga el Excel que ya usa y, con un clic, obtiene la lista de cada sede, ordenada, con el motivo de cada llamada al lado. Si la Dirección amplía la capacidad, cambia este número y la lista se ajusta. Aquí ve cuántas matrículas esperar por sede y nivel, frente a lo que pasó en años anteriores. Y puede consultar un caso: con pago tardío y reserva extraordinaria, prioridad alta; sin señales, prioridad baja. Si alguien sube un archivo con cédulas, la aplicación lo rechaza y explica por qué.»

**En pantalla:** Aquí entra la grabación de pantalla de la aplicación (sección 4). La diapositiva sirve de respaldo.

### Bloque 5. Evaluación y resultados (45 s)

**Diapositiva 7 · Resultados** 3:15–3:40 (25 s)

**HABLA: Guillermo Granizo**

> «¿Funciona? Lo probamos con la matrícula 2026–2027: 1.093 familias, de las cuales 74 no pagaron a tiempo. Con 165 llamadas al azar habríamos encontrado unas 11. Con la lista encontramos 22: el doble, con el mismo personal. Son 7,5 llamadas por caso en lugar de 15. Técnicamente es un Lift de 1,97, y aun con el margen de error supera la meta que nos pusimos.»

**En pantalla:** Gráfico 11 frente a 22 y la tabla antes y después.

**Diapositiva 8 · Dónde funciona y dónde no** 3:40–4:00 (20 s)

**HABLA: Guillermo Granizo**

> «Funcionó en los cuatro años revisados, entre 1,4 y 2 veces mejor que el azar. Pero tiene límites: llega a 3 de cada 10 casos, porque los otros 7 no dejan ninguna señal el 20 de febrero. Y los modelos de IA no superaron a la regla. José les explica cómo la cuidamos.»

**En pantalla:** Dos columnas: dónde funciona y dónde no.

### Bloque 6. Consideraciones éticas (45 s)

**Diapositiva 9 · Ética** 4:00–4:45 (45 s)

**HABLA: José Ulloa** *· Entra José cuando Guillermo termina «José les explica cómo la cuidamos».*

> «Son datos de menores y de la economía de las familias, así que la ética fue parte del diseño. Sesgos: las señales tienen que ver con pagos, y la lista encontró menos casos entre becadas, 18 frente a 32 de cada 100; con solo 11 casos no es concluyente, por eso se revisa cada año. Impacto: bien usada, lleva ayuda a tiempo; usada para cobrar, dañaría a quien más la necesita, y ese uso está prohibido. Mitigaciones: códigos en lugar de nombres, la aplicación pública solo acepta datos inventados, la nacionalidad nunca se usa y siempre decide una persona. Limitación: antes de usarla hay que informar a las familias.»

**En pantalla:** Cuatro tarjetas: sesgos, impacto social, mitigaciones y limitaciones.

### Bloque 7. Cierre (15 s)

**Diapositiva 10 · Cierre** 4:45–5:00 (15 s)

**HABLA: Guillermo Granizo** *· Entra Guillermo cuando José termina «hay que informar a las familias».*

> «Con lo que el colegio ya tiene, encontramos el doble de familias en riesgo con el mismo esfuerzo. Proponemos un piloto en la campaña 2027, con una segunda llamada a mitad de campaña. Aquí están el repositorio y la aplicación. ¡Gracias!»

**En pantalla:** La propuesta y los QR del repositorio y de la aplicación. Dejarlos 3 segundos quietos.

## 4. Grabación de pantalla (2:15–3:15)

Grabar la aplicación real desplegada, en modo demostración (datos sintéticos): continuidad-matricula-lemas.streamlit.app. Es el bloque crítico de la guía: muestra tres casos de uso, explica lo que se ve y el manejo de errores.

| **Segundo** | **Acción en pantalla**                                                                                           | **Lo que dice Guillermo**                                                                                                                                           |
|-------------|------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 0–5         | App abierta; señalar el aviso «Modo demostración»                                                                | «Esta es la aplicación real, en modo demostración, con datos inventados.»                                                                                           |
| 5–24        | Lista de contactos → «Prueba con ejemplo» → «Generar lista». Recorrer la columna Motivo. Cambiar k de una sede   | «El 20 de febrero, Secretaría carga el Excel… con el motivo de cada llamada al lado. Si la Dirección amplía la capacidad, cambia este número y la lista se ajusta.» |
| 24–36       | Pestaña Proyección: gráfico por sede y nivel                                                                     | «Aquí ve cuántas matrículas esperar por sede y nivel, frente a lo que pasó en años anteriores.»                                                                     |
| 36–50       | Pestaña Evaluar un estudiante: (a) pago tardío + reserva extraordinaria → prioridad alta; (b) sin señales → baja | «Y puede consultar un caso: con pago tardío y reserva extraordinaria, prioridad alta; sin señales, prioridad baja.»                                                 |
| 50–60       | Volver a la barra lateral y subir un CSV con columna CI → mensaje de rechazo                                     | «Si alguien sube un archivo con cédulas, la aplicación lo rechaza y explica por qué.»                                                                               |

### Preparación

- Tener listo un CSV de prueba: el ejemplo sintético descargado de la app, con una columna CI añadida a mano y valores inventados como 0000000000. Nunca usar datos reales.

- Abrir la app unos minutos antes: si estuvo inactiva, tarda en despertar.

- Ventana limpia del navegador, zoom al 110–125 % y sin marcadores ni extensiones a la vista.

- Nunca abrir la pestaña «Lista con nombres» ni el Excel real.

## 5. Cómo grabar entre los dos

- **Por partes y unir.** Cada uno graba sus bloques con la presentación a pantalla completa (OBS, Zoom o Loom), con su voz y, si quieren, cámara pequeña en una esquina.

- **Guillermo graba:** diapositivas 1–2, la grabación de pantalla (6), 7–8 y 10.

- **José graba:** diapositivas 3–5 y 9.

- **Montaje en orden:** 1–2 (G) · 3–5 (J) · demo (G) · 7–8 (G) · 9 (J) · 10 (G). Clipchamp, iMovie, Shotcut o DaVinci Resolve.

- **Audio parejo:** audífonos con micrófono, lugar silencioso y la misma distancia al micrófono para los dos; normalizar el volumen al unir.

- **Ensayo:** dos pasadas completas con cronómetro. Si un bloque se pasa, recortar ejemplos, no cifras.

### Exportación

- MP4 (H.264), 1080p (mínimo 720p), 30 fps.

- YouTube «no listado» o Google Drive con acceso para la profesora. Título: «Continuidad estudiantil en LEMAS – Proyecto final IA UEES 2026».

- Agregar el enlace en la sección Videos del README.

## 6. Lista de verificación contra la guía

| **Requisito**                        | **Dónde se cumple**                                                                    | **Estado**        |
|--------------------------------------|----------------------------------------------------------------------------------------|-------------------|
| 1\. Introducción y problema (30 s)   | Diapositivas 1–2: nombre, equipo, problema y por qué importa                           | ✔                 |
| 2\. Datos y metodología (1 min)      | Diapositivas 3–4: dataset, limpieza, protección, modelos comparados y por qué la regla | ✔                 |
| 3\. Desarrollo y optimización (45 s) | Diapositiva 5: reto, 180 ajustes con Optuna, sensibilidad (tamaño de hoja 90 %)        | ✔                 |
| 4\. Solución en acción (1 min)       | Grabación: 3 casos de uso, explicación de salidas y error controlado                   | Por grabar        |
| 5\. Evaluación y resultados (45 s)   | Diapositivas 7–8: métrica, comparación con el azar, dónde funciona y dónde no          | ✔                 |
| 6\. Ética (45 s)                     | Diapositiva 9: sesgos, impacto, mitigaciones y limitaciones                            | ✔                 |
| 7\. Cierre (15 s)                    | Diapositiva 10: logro, siguiente paso y QR del repositorio y la app                    | ✔                 |
| Máximo 10 diapositivas, poco texto   | 10 diapositivas con cifras grandes, íconos, un gráfico y una tabla                     | ✔                 |
| Duración ≤ 5:00                      | 709 palabras; cronometrar en el ensayo                                                 | Por ensayar       |
| Hablan los dos integrantes           | Cuatro cambios de voz (sección 2)                                                      | ✔                 |
| Sin datos reales en pantalla         | La demo usa datos sintéticos                                                           | Revisar al grabar |
