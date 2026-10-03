# Guion del pitch y plan de grabación

Duración total: **5:00**. Presentación en línea (10 diapositivas), con las notas del orador ya cargadas en cada diapositiva. Formato de entrega: MP4 o YouTube "no listado", 720p como mínimo.

## 1. Guion cronometrado

| # | Diapositiva | Tiempo | Bloque de la guía | Orador |
|---|---|---|---|---|
| 1 | Portada | 0:00–0:15 | Introducción y problema (30 s) | Guillermo |
| 2 | Problema | 0:15–0:30 | | Guillermo |
| 3 | Datos | 0:30–1:00 | Datos y metodología (1 min) | José |
| 4 | Metodología | 1:00–1:30 | | José |
| 5 | Optimización | 1:30–2:15 | Desarrollo y optimización (45 s) | José |
| 6 | Demo (grabación de pantalla) | 2:15–3:15 | Solución en acción (1 min) | Guillermo |
| 7 | Resultados | 3:15–3:40 | Evaluación (45 s) | Guillermo |
| 8 | Alcance | 3:40–4:00 | | Guillermo |
| 9 | Ética | 4:00–4:45 | Ética (45 s) | José |
| 10 | Cierre con QR | 4:45–5:00 | Cierre (15 s) | Guillermo |

### Texto por diapositiva

**1 · Portada (Guillermo, 0:00–0:15).** Hola, somos Guillermo Granizo y José Ulloa. Presentamos "Continuidad estudiantil en LEMAS", un sistema de IA que ayuda a la Unidad Educativa LEMAS a decidir a qué familias llamar primero cuando una reserva aprobada todavía no se convierte en matrícula pagada.

**2 · Problema (Guillermo, 0:15–0:30).** Cada año, entre el 6 y el 11 % de los estudiantes con reserva aprobada no paga la matrícula a tiempo. La institución se entera tarde. Tenemos 69 días, del 20 de febrero al 30 de abril, y solo 10 personas para las dos sedes. La pregunta es simple: ¿a quién llamar primero?

**3 · Datos (José, 0:30–1:00).** Trabajamos con datos reales de LEMAS, autorizados: 9.031 registros de seis ciclos, 2.733 estudiantes y 2.017 familias. Antes de tocarlos, reemplazamos las cédulas con HMAC-SHA256; la clave queda solo con el custodio. En la limpieza encontramos tres problemas que cambiaban los resultados: dos formatos de nombre de curso, un último curso que no se reconocía y una cédula genérica usada para familias extranjeras. Solo publicamos agregados.

**4 · Metodología (José, 1:00–1:30).** Usamos validación temporal: entrenamos con C2 y C3, elegimos en C4 y probamos una sola vez en C5, la matrícula 2026–2027. C1 se excluyó porque una auditoría mostró que no era comparable. Comparamos tres modelos de IA con dos reglas sin IA y con el azar. La métrica es el Lift por familia: cuántas veces más casos encontramos que al azar, contactando solo a las familias que cada sede puede atender.

**5 · Optimización (José, 1:30–2:15).** Optimizamos con Optuna: 180 combinaciones, siempre respetando el orden temporal. Encontramos dos problemas. El modelo de árboles se sobreajustó: duplicó su desempeño en entrenamiento pero no en C4. Y el modelo que ganó en C3 perdió en C4: con unos 200 casos y tasas que cambian cada año, lo óptimo en un año no se repite en el siguiente. Por eso decidimos en C4 frente a reglas simples, y registramos un único intento adicional antes de verlo.

**6 · Demo (Guillermo, 2:15–3:15).** Se reproduce la grabación de pantalla (ver sección 2). Narración sugerida: "Esta es la aplicación pública, que solo trabaja con datos sintéticos. Con un clic genera la lista de familias por sede, cada una con su motivo. En Proyección vemos las matrículas esperadas frente a la tasa histórica. Aquí evaluamos un estudiante con pago tardío y reserva extraordinaria: prioridad alta; y otro sin señales: prioridad baja. Si alguien intenta subir un archivo con cédulas, la aplicación lo rechaza."

**7 · Resultados (Guillermo, 3:15–3:40).** En la prueba final, que hicimos una sola vez, la regla D2 encontró casi el doble de casos que el azar: Lift de 1,97, con un intervalo de confianza que no incluye el 1. En términos prácticos: llamando al 15 % de las familias, LEMAS llega al 30 % de las que no completarán la matrícula a tiempo. Superamos la meta de 1,20 que nos pusimos.

**8 · Alcance (Guillermo, 3:40–4:00).** La regla supera al azar en los cuatro ciclos, con un Lift de 1,4 a 2,0: el 1,97 es el valor alto. No alcanza al 70 % de los casos: el 20 de febrero los datos no los distinguen. Y los modelos de IA no superaron a la regla: la IA sirvió para descubrirla, validarla y medir su incertidumbre.

**9 · Ética (José, 4:00–4:45).** Trabajamos con datos de menores, así que la ética guió el diseño. Sesgos: los atrasos reflejan la situación económica y la regla detecta menos casos entre familias becadas. Impacto: bien usada, la lista lleva ayuda a tiempo; usada para cobrar, dañaría a quienes más la necesitan, y por eso ese uso está prohibido. Mitigaciones: seudónimos con clave custodiada, una app pública que solo acepta datos sintéticos, la nacionalidad nunca se usa y siempre decide una persona. Limitaciones: las familias aún no fueron informadas, y es un requisito pendiente antes de usarla en la práctica; hay pocos casos por grupo y no medimos si la llamada cambia la decisión.

**10 · Cierre (Guillermo, 4:45–5:00).** Nuestro logro: una regla validada con datos reales que LEMAS puede usar cada 20 de febrero. Lo siguiente: una segunda etapa a mitad de campaña con las familias que sigan sin pagar, por probar en 2027. Aquí están el repositorio y la aplicación. ¡Gracias!

## 2. Guion de la grabación de pantalla (60 s)

Grabar la **aplicación real desplegada**: https://continuidad-matricula-lemas.streamlit.app/ (modo demostración, datos sintéticos).

| Segundo | Acción en pantalla | Caso que demuestra |
|---|---|---|
| 0–5 | Abrir la app; mostrar el aviso "Modo demostración" | Contexto y seguridad |
| 5–22 | Pestaña **Lista de contactos** → "Prueba con ejemplo" → "Generar lista". Desplazar la tabla de una sede mostrando la columna *motivo*; cambiar k de una sede | Caso 1: lista priorizada |
| 22–35 | Pestaña **Proyección**: matrícula esperada por sede y subnivel frente a la tasa histórica | Caso 2: proyección |
| 35–50 | Pestaña **Evaluar un estudiante**: (a) pago tardío + reserva extraordinaria → prioridad alta; (b) sin señales → prioridad baja | Caso 3: consulta individual |
| 50–60 | Volver a Lista de contactos y subir un CSV con una columna `CI` → mostrar el mensaje de rechazo | Manejo de errores |

Preparación previa:

- Tener listo un CSV de prueba con columna `CI` (por ejemplo, el ejemplo sintético descargado desde la app con una columna `CI` añadida a mano y valores inventados como `0000000000`). **Nunca usar datos reales.**
- Abrir la app unos minutos antes (Streamlit Cloud tarda en "despertar" si estuvo inactiva).
- Navegador en ventana limpia, zoom al 110–125 % para que el texto se lea en 720p; ocultar marcadores y extensiones.

## 3. Plan de grabación

**Herramientas sugeridas.** OBS Studio (gratuito) o Loom / grabación de Zoom. Resolución 1920×1080 (cumple de sobra el mínimo de 720p), 30 fps.

**Opción recomendada: grabar por partes y unir.**

1. **Pista de diapositivas.** Abrir la presentación en línea a pantalla completa. Cada orador graba su bloque con su voz (y cámara pequeña en una esquina, si lo desean). Las notas del orador están en cada diapositiva.
2. **Pista de demo.** Grabar la sección 2 por separado, con la narración de Guillermo.
3. **Montaje.** Unir en el orden 1–5, demo, 7–10 con un editor sencillo (Clipchamp, iMovie, DaVinci Resolve o Shotcut). Comprobar que el total no pase de 5:00.

**Ensayo.** Hacer dos ensayos completos cronometrados antes de grabar. Si un bloque se pasa del tiempo, recortar ejemplos, no cifras.

**Audio.** Usar audífonos con micrófono o un micrófono externo; grabar en un lugar silencioso; misma distancia al micrófono para ambos oradores.

**Exportación y publicación.**

- Exportar en MP4 (H.264), 1080p o 720p.
- Subir a YouTube como **no listado**, título "Continuidad estudiantil en LEMAS – Proyecto final IA UEES 2026".
- Añadir el enlace del video al README (sección de presentación) y a la entrega.

**Lista de verificación final.**

- [ ] Duración ≤ 5:00.
- [ ] Están los 7 bloques de la guía con sus tiempos.
- [ ] La demo usa la app real desplegada, con 3 casos de uso y el manejo de errores.
- [ ] No aparece ningún dato real ni cédula en pantalla.
- [ ] Los QR del cierre se ven nítidos y abren el repositorio y la app.
- [ ] Hablan los dos integrantes.
- [ ] Video en 720p o más, MP4 o YouTube no listado.

## 4. Presentación efectiva: comprobación

Recomendaciones de la semana 4 del curso y de la guía del proyecto, con lo que ya está resuelto y lo que falta hacer al grabar.

| Recomendación | Cómo se aplica | Estado |
|---|---|---|
| Empezar por el problema, no por la técnica | Las diapositivas 1 y 2 presentan a quién llamar primero con 10 personas y 69 días | Hecho |
| Un mensaje por diapositiva | La mayoría de los títulos enuncia la conclusión («Optimizar no bastó: la señal es débil y cambia entre años»); 10 diapositivas para 5 minutos | Hecho |
| Poco texto y cifras grandes | Frases cortas en pantalla y las cifras clave en grande; el detalle va en las notas del orador | Hecho |
| Contar una historia | Problema, datos, lo que probamos, lo que funcionó, lo que no y lo que sigue | Hecho |
| Mostrar la solución real | Grabación de la app desplegada con tres casos y un error controlado | Por grabar |
| Ser honestos con las limitaciones | Diapositivas 8 y 9: la IA no superó a la regla; la lista no alcanza al 70 % de los casos; el Lift fue de 1,4 a 2,0 según el ciclo | Hecho |
| Cubrir los cuatro puntos de ética que pide la guía | Sesgos, impacto social, mitigaciones y limitaciones en la diapositiva 9 | Hecho |
| Hablar para una audiencia no experta | "Lift" se explica como "cuántas veces más casos que al azar"; sin siglas sin explicar | Revisar en el ensayo |
| Ensayar y cronometrar | Dos ensayos completos; si un bloque se pasa, recortar ejemplos y no cifras | Por hacer |
| Repartir la palabra | Guillermo: problema, demo, resultados y cierre. José: datos, método, optimización y ética | Hecho |
| Cerrar con una acción clara | Logro, siguiente paso y los dos QR | Hecho |
| Preparar las preguntas | [Banco de 35 preguntas](banco_preguntas.md), con una sección de ética y regulación | Hecho |
| Cuidar audio e imagen | Micrófono externo, lugar silencioso, 1080p, zoom del navegador al 110–125 % | Por hacer |

Errores frecuentes que conviene evitar: leer las diapositivas, pasarse de los 5 minutos, mostrar código, dejar la ética para una frase final y presentar el resultado como mejor de lo que es.
