# Banco de preguntas para la defensa

Respuestas cortas (20–40 segundos) con las cifras reales del proyecto. Las cifras provienen de [modelado.md](modelado.md), [optimizacion.md](optimizacion.md) y [consideraciones_eticas.md](consideraciones_eticas.md).

Sugerencia de reparto: **Guillermo** responde problema, resultados, app y negocio; **José** responde datos, metodología, optimización y ética (secciones B, C, D, F y G).

## A. Problema y alcance

**1. ¿Por qué este problema necesita IA y no basta con una hoja de cálculo?**
Porque la pregunta es de priorización bajo capacidad limitada: con 10 personas y 69 días hay que ordenar a más de mil familias. La IA nos permitió probar de forma rigurosa qué señales ordenan mejor y medir la incertidumbre. El resultado fue que una regla simple (D2) ordena mejor que los modelos, y eso solo se puede afirmar después de compararlos con validación temporal.

**2. ¿Qué significa exactamente "no matrícula"?**
`y_no_matricula = 1` cuando un estudiante con reserva aprobada al 20 de febrero (t0) no tiene la matrícula pagada al 30 de abril (H). La unidad de decisión es la familia (representante), porque la llamada se hace al representante.

**3. ¿Qué es k y por qué es 118 y 47?**
Es el número de familias que cada sede contacta en la ventana. Se fijó en el doble del promedio histórico de casos por sede: 118 en Mucho Lote 1 y 47 en Mucho Lote 2. Fue una decisión, no una medida de la capacidad real: son menos de dos contactos por persona y semana. No cambia al cambiar el ciclo en la app.

**4. Si la regla D2 gana, ¿dónde está la IA del proyecto?**
En el proceso: preprocesamiento, tres modelos optimizados con Optuna, calibración, SHAP y permutación, bootstrap y prueba única. La explicabilidad mostró que la información útil está en el pago y el tipo de reserva, lo que justifica D2. Además, el modelo híbrido calibrado sigue en uso para las probabilidades y la proyección de matrícula.

## B. Datos y privacidad

**5. ¿Cuántos datos usaron y de dónde vienen?**
9.031 registros de seis ciclos de la base de LEMAS, con 2.733 estudiantes y 2.017 familias, con autorización formal de la institución.

**6. ¿Cómo protegieron los datos personales?**
Las cédulas se reemplazaron por seudónimos HMAC-SHA256 antes de cualquier análisis; la clave la guarda solo el custodio de LEMAS. Nombres, teléfonos y correos se eliminan. En GitHub solo hay código, datos sintéticos y agregados; las celdas con menos de 5 casos se muestran como `<5`.

**7. ¿Qué problemas de calidad encontraron?**
Tres que cambiaban los resultados: dos formatos de nombre de curso, un último curso de bachillerato que no se reconocía como terminal, y una cédula genérica usada para varias familias extranjeras (se marcó como representante atípico cuando tiene más de 6 estudiantes por año). También encabezados distintos entre hojas (`anoaa`, `Fecha`), que se unificaron.

**8. ¿Por qué excluyeron el ciclo C1?**
Una auditoría comparó entrenar con y sin C1: incluirlo bajaba la Precision@k en 0,027, más que la tolerancia de 0,02 que fijamos antes de mirar (IC [−0,061; +0,012]). Se decidió excluirlo por no ser comparable.

**9. ¿El desbalance de clases fue un problema?**
Sí: la tasa es de 6–11 %. Por eso no usamos exactitud, sino métricas que miran la clase minoritaria (PR-AUC, Precision@k, Lift@k), y probamos pesos balanceados como hiperparámetro.

## C. Metodología y modelos

**10. ¿Por qué validación temporal y no validación cruzada aleatoria?**
Porque el sistema se usará para predecir el año siguiente. Mezclar años filtraría información del futuro. Entrenamos con C2–C3, seleccionamos y calibramos en C4 y probamos una sola vez en C5. Detalle de técnicas aplicadas y no aplicadas en [evaluacion_robusta.md](evaluacion_robusta.md).

**11. ¿Qué es el Lift@k?**
Cuántas veces más casos encuentra la lista que una selección al azar del mismo tamaño. Lift 1,97 significa casi el doble de casos que llamando al azar a k familias.

**12. ¿Qué modelos probaron?**
Regresión logística con elastic-net, HistGradientBoosting con monotonía creciente en atrasos, y una logística híbrida con las señales de D2 más variables académicas. Se compararon con el azar (A), la regla D (más atrasos primero) y la regla D2.

**13. ¿Qué es la regla D2?**
Un puntaje administrativo: 100 por pago tardío de la matrícula anterior, más 20 por reserva extraordinaria, más el número de pensiones atrasadas. Se ordena de mayor a menor. Los empates se resuelven al azar con semilla fija, igual en la validación y en la aplicación.

**14. ¿No es injusto comparar modelos con una regla diseñada mirando los datos?**
La regla se definió con conocimiento del negocio y se evaluó con la misma disciplina que los modelos: seleccionada en C4 y probada una sola vez en C5. Allí mantuvo su desempeño (1,97, IC [1,24; 2,56]).

**14 bis. ¿Cómo evitaron la fuga de información (*data leakage*)?**
De cuatro formas:
- Cada predictor se mide con lo que se sabe el 20 de febrero. Los atrasos se cuentan de mayo a enero, confirmado con LEMAS: la pensión de febrero vence después del corte y no entra.
- El preprocesamiento va dentro del *pipeline*, así que imputación y escalado se ajustan solo con el entrenamiento. Optuna afinó en C2 → C3 y la calibración se hizo en C4, nunca en C5.
- Los hermanos se consolidan por familia, para que un mismo caso no cuente dos veces.
- C5 se abrió una sola vez, con el sistema congelado y su huella registrada.

Además encontramos y corregimos una fuga real: un falso grupo de 38 hermanos que inflaba el ROC-AUC de 0,54 a 0,59 (D29).

## D. Optimización y diagnóstico

**15. ¿Cómo optimizaron los hiperparámetros?**
Con Optuna (TPE, semilla 42), 60 pruebas por modelo, 180 en total, maximizando PR-AUC entrenando en C2 y evaluando en C3. Ejemplo: la logística pasó de 0,062 a 0,106 de PR-AUC entre la peor y la mejor prueba.

**15 bis. ¿Qué hiperparámetros importaron y cómo lo saben?**
Lo medimos sobre las 180 pruebas de Optuna, sin volver a entrenar, con importancia por fANOVA, dependencia parcial e interacciones. En la regresión logística lo decisivo es `C`: con regularización fuerte el modelo se aplana hacia la tasa base, y desde `C` ≈ 1 hay una meseta. En el gradient boosting, el tamaño mínimo de hoja explica el 90 %: con hojas de menos de 80 estudiantes memoriza. La logística híbrida casi no responde a sus hiperparámetros. Las interacciones son débiles. La búsqueda mejoró la validación interna (la regresión logística pasó de 0,079 a 0,106), pero esa ganancia no se trasladó a C4: el límite es de señal, no de hiperparámetros. Detalle en [optimizacion.md](optimizacion.md), sección 2 bis.

**16. ¿Hubo sobreajuste o subajuste?**
El gradient boosting se sobreajustó: PR-AUC 0,245 en entrenamiento y 0,103 en C4. La logística mostró subajuste leve (0,140 frente a 0,113), porque las señales son débiles. La híbrida fue estable (0,126 frente a 0,125) pero con poca capacidad.

**17. ¿Por qué el mejor modelo en C3 no fue el mejor en C4?**
Con unos 200 casos positivos por año y tasas que cambian, las diferencias pequeñas en C3 no se repiten. Por eso la selección final se hizo en C4 frente a reglas simples, no solo por el ranking de Optuna.

**18. ¿Qué hicieron para no "hacer trampa" con el conjunto de prueba?**
El sistema se congeló con un hash SHA-256 antes de abrir C5, y C5 se evaluó una sola vez con una bandera explícita. El modelo híbrido se registró como intento único (decisión D39) antes de verlo en C4.

## E. Resultados y evaluación

**19. ¿Cuál es el resultado principal?**
En C5, D2 logra Lift@k 1,97 [1,24; 2,56], Precision@k 0,133 y Recall@k 0,30: llamando al 15 % de las familias se llega al 30 % de las que no se matriculan. La meta era 1,20.

**20. ¿Y los modelos de IA en C5?**
La logística híbrida obtuvo Lift 0,98 [0,47; 1,52], sin diferencia con el azar (1,08). Esto confirma que la decisión tomada en C4 de usar D2 fue correcta.

**21. ¿Las probabilidades del modelo sirven?**
Están bien calibradas en promedio (Brier 0,0648), pero empatan con usar la tasa histórica (0,0647). En la proyección de matrícula por sede y subnivel el MAPE es 2,8 %, igual que la tasa histórica. Lo reportamos tal cual: cumple el umbral de 15 %, pero no mejora a la referencia.

**22. ¿Qué es lo que el sistema no puede detectar?**
La lista no alcanza a cerca del 70 % de los casos: encontró 22 de 74. Tenía 165 cupos, más que casos, así que el límite es de señal y no de capacidad. No sabemos por qué no continúan esas familias, porque no tenemos datos de motivos. Sí sabemos que no es un problema de retrasos: en C2 a C4, el 86 % de los casos no registra ningún pago, y a esas familias la regla las encuentra peor (24 %) que a las que pagan tarde o en parte (43 %). Lo analizamos con C2 a C4, sin tocar C5: tres de cada cuatro familias pagan en las primeras cuatro semanas, y hacia el día 35 quedan unas 200 pendientes por año, de las que el 44 % son casos. La mejora no viene de un modelo mejor, sino de una segunda etapa a mitad de campaña con quienes siguen sin pagar. Es una propuesta para 2027, sin validar (`docs/alcance_lista.md`). La aplicación ya lista a esas familias en la pestaña *Seguimiento*; es un listado de pagos, no una predicción.

**22 bis. ¿Por qué no eligieron el umbral que minimiza el costo esperado?**
Porque el número de llamadas lo fija la capacidad del personal. Una llamada de más cuesta minutos; un estudiante perdido, un año de pensiones. Con esa diferencia, el umbral de costo mínimo pediría llamar a más familias de las que se pueden atender, así que minimizar el costo con k llamadas es encontrar el mayor número de casos: eso mide Lift@k. Lo cuantificamos sin montos reales con la razón de equilibrio: si una llamada rescata al 10 % de los casos, en C5 la lista compensa si un caso vale más de 75 llamadas, frente a 148 al azar. Y la capacidad extra rinde más en una segunda llamada a quienes siguen sin pagar en la semana 5 (38 % son casos) que alargando la lista inicial (10 %, casi como al azar). Detalle en [evaluacion_robusta.md](evaluacion_robusta.md) §3.

**22 ter. ¿Lo evaluaron en condiciones parecidas al mundo real?**
Sí, de dos formas. La prueba final imita el uso: foto al 20 de febrero, un año nunca visto, sistema congelado, familias como unidad y el mismo k de la operación. Además simulamos sobre C4, sin tocar C5, errores de digitación, datos faltantes, un año con muy pocos casos, cambio entre sedes y entre becados, y una señal que llega constante. Con los datos reales, la lista tolera hasta un 10 % de errores de digitación y cae bajo el umbral hacia el 20 %. Sigue útil con hasta la mitad de una señal vacía, o con una señal constante, porque las tres se solapan; solo con las tres caídas queda en el azar (1,05). Con muy pocos casos la lista sirve, pero la medición de un solo año no es confiable. La logística híbrida no se transfiere entre sedes, mientras que la regla común no lo necesita. La aplicación avisa en amarillo si falla una señal y en rojo si fallan dos o más, y contra los errores de digitación Secretaría revisa los motivos de las 165 familias antes de llamar. Detalle en [escenarios_criticos.md](escenarios_criticos.md).

## F. Ética y aplicación

**23. ¿Qué sesgos encontraron?**
La regla detecta menos casos en familias becadas (recall 18 % frente a 32 %), aunque con solo 11 eventos la diferencia es incierta. Los atrasos reflejan la situación económica. Por eso la lista se usa para ofrecer apoyo, no para presionar, y recomendamos revisar también a becados con atrasos.

**24. ¿Usaron la nacionalidad o información sensible?**
No. La nacionalidad nunca es predictor, y no usamos motivos del DECE ni información de salud. La cédula genérica de familias extranjeras se trató como problema de calidad, no como variable.

**25. ¿Qué pasa si alguien sube datos reales a la app pública?**
La versión pública funciona en modo demostración y solo acepta archivos marcados como sintéticos; rechaza los que traen cédulas o nombres y no tiene carga de Excel ni pantalla con nombres. Es una barrera contra errores, no contra alguien que quiera saltársela. Los datos reales se procesan solo en el modo institucional, que corre en un computador de LEMAS y solo se abre en ese mismo equipo.

**25b. ¿Cómo usa LEMAS el sistema si su personal no conoce Colab?**
Con un doble clic abre la app en modo institucional y sube el Excel de siempre junto con la clave del custodio. La app seudonimiza en memoria con la misma técnica HMAC-SHA256, verifica que no queden nombres ni cédulas y genera la lista. Para llamar, el personal autorizado abre la pestaña "Lista con nombres". Nada se guarda en disco y la clave no se almacena.

**26. ¿Quién toma la decisión final?**
Siempre una persona de Secretaría. La app muestra el motivo de cada familia para que la decisión sea explicable y revisable.

**27. ¿Cómo se mantendría el sistema?**
Cada mayo, cuando se conoce el resultado del ciclo, se compara la lista con las matrículas reales, se actualiza el historial y se revalidan la regla y el modelo con la cohorte nueva. Si cambian las políticas de cobro o de reservas, D2 debe revalidarse antes de usarse. El siguiente paso es la validación con usuarios (anexo E del [documento técnico v6](Documento_Tecnico_Prediccion_Matricula_v6.docx)).

## G. Ética, responsabilidad y regulación

**28. ¿Cuál fue el dilema ético más difícil?**
Usar o no las señales de pago. Son lo único que ordena bien a las familias, pero reflejan su situación económica. Decidimos usarlas con una condición: la lista solo sirve para ofrecer apoyo, nunca para cobrar ni excluir, y siempre decide una persona. Fueron las únicas señales que mostraron capacidad de ordenar.

**29. ¿Quién responde si el sistema falla?**
El sistema no decide, propone un orden. LEMAS responde por el uso de la lista: Secretaría por el contacto, el custodio por los datos y la clave, y Dirección por autorizar y revisar el sistema cada año. Nosotros respondemos por el desarrollo y la validación. Queda registro en cada etapa: decisiones D01 a D50, sistema congelado con SHA-256 y acta de seudonimización.

**30. ¿Qué normativa aplica y la cumplen?**
Aplica la Ley Orgánica de Protección de Datos Personales del Ecuador y la norma de la Superintendencia sobre IA y datos personales, expedida en febrero de 2026. Implementamos medidas de seguridad, protección desde el diseño y decisión humana. Quedan pendientes para LEMAS antes de un uso operativo: confirmar la base legal para datos de menores, informar a las familias, hacer la evaluación de impacto y registrar el tratamiento. El RGPD y la CCPA no son directamente aplicables; los usamos como referencia.

**31. ¿Por qué no pidieron consentimiento a las familias?**
El estudio académico se hizo con autorización de LEMAS y con datos seudonimizados, y lo reconocemos como limitación. Según nuestra lectura, la ley pide autorización expresa del titular o de su representante para tratar datos de menores, así que no damos por suficiente el interés de la institución: LEMAS debe confirmarlo con su asesor. Dejamos redactado un aviso para las familias y lo marcamos como requisito antes de usar el sistema.

**32. ¿Podría usarse mal?**
Sí, dentro de la propia institución: para cobrar, para negar cupos o para perfilar familias. Las salvaguardas son que la lista no incluye montos, que los nombres solo aparecen en un equipo de LEMAS, que esos usos están prohibidos por escrito y que Dirección revisa el sistema cada año. Como referencia, la Ley de IA europea considera de alto riesgo los sistemas que deciden admisiones; el nuestro no decide, y por eso ese uso está prohibido.

**33. ¿Cómo sabrán si el sistema deja de funcionar o se vuelve injusto?**
Cada mayo se compara la lista con las matrículas reales. Si el Lift@k baja de 1,20 se revalida la regla; si no supera al azar, se suspende. También se revisa el Recall@k por beca, sede y subnivel, acumulando cohortes para tener más casos por grupo.

**34. ¿Qué aprendieron de otros sistemas parecidos?**
El caso más estudiado es el sistema de alerta de deserción de Wisconsin. Ordenaba bien a los estudiantes, pero un estudio de casi diez años de datos no pudo demostrar que mejorara la graduación, y una investigación mostró más falsas alarmas con estudiantes negros e hispanos. La lección es que predecir no es ayudar: por eso no usamos variables demográficas y reconocemos que falta medir si la llamada cambia la decisión.

## H. Preguntas de la revisión independiente (D59)

Una revisión independiente de la entrega señaló los puntos más discutibles del proyecto. Son las preguntas más probables del video de respuestas. Detalle y cifras en [modelado.md, sección 9](modelado.md#9-comprobaciones-de-la-revisión-final-d59).

**35. El análisis exploratorio usó las cinco cohortes. ¿Con qué fundamento dicen que D2 se confirmó fuera de muestra?**
Tiene razón en que el diseño vio C4 y C5: las tasas por señal del cuaderno 01 se calcularon con todas las cohortes, y no lo declaramos a tiempo. Por eso lo comprobamos: repetimos el cálculo solo con C1–C3 y el orden sale igual (riesgo relativo 2,88 para el pago tardío, 1,47 para la reserva extraordinaria y 1,27 para los atrasos). Con C2–C3, también. D2 se habría construido igual sin mirar C4 ni C5, así que la prueba en C5 vale también para el diseño. Cohorte a cohorte, el orden entre reserva y atrasos cambia: ese tramo de la regla descansa en diferencias pequeñas.

**36. El Lift@k depende del sorteo de empates. ¿El 1,97 de C5 no es un sorteo favorable?**
Puede serlo. En C4, con 500 sorteos, la media es 1,77 y la semilla oficial (1,93) supera al 87 % de los sorteos: elegimos D2 con un sorteo favorable. Con la media, D2 sigue sobre la logística híbrida (1,53) y sobre la meta de 1,20 en todos los sorteos (el mínimo es 1,40). El IC de C5 [1,24; 2,56] sí incluye esa variación, porque cada remuestra resuelve los empates de nuevo. No repetimos los sorteos en C5 para no volver a usarla.

**37. ¿Dónde está la IA, si la solución es una regla de tres señales con pesos puestos a mano?**
La IA está en el método, no en el producto final. Las señales salieron del análisis exploratorio; el aprendizaje automático sirvió para compararlas con tres modelos optimizados, comprobar que no había más señal que aprovechar, medir la incertidumbre y descartar lo que no generaliza. Con 193 eventos de entrenamiento, los modelos no superaron a la regla, y eso solo se puede afirmar después de compararlos con validación temporal. Los pesos 100, 20 y 1 no son parámetros estimados: solo fijan un orden lexicográfico. Una logística solo con esas tres señales no se probó: el protocolo permitía un único intento adicional, registrado antes de verlo en C4 (D39), y fue la logística híbrida, que ya las incluía y obtuvo 1,53. Probarla es una buena tarea para la próxima versión.

**38. La optimización empeoró la regresión logística en C4 (1,53 → 1,40). ¿Por qué mantuvieron esa función objetivo?**
Porque se fijó antes de ver C4 (PR-AUC en la validación C2 → C3) y cambiarla después habría sido ajustar a C4. La optimización sí mejoró la validación interna (de 0,079 a 0,106), pero esa mejora no se trasladó: con 81 eventos en C3, lo óptimo en una cohorte no lo es en la siguiente. El análisis de sensibilidad lo explica: la respuesta es casi plana y lo que importa es la regularización. Una validación con varias cohortes promediadas sería la mejora para una próxima versión.

**39. Los IC de D2 y de D se solapan. ¿Qué evidencia tienen de que D2 sea mejor que la regla más simple?**
Ninguna, y lo decimos así. Con un bootstrap pareado en C4, la diferencia D2 − D es 0,00 [−0,62; 0,62]: las dos reglas son igual de buenas. D2 se mantiene por la regla de decisión registrada de antemano (el mayor Lift@k en C4) y porque explica mejor a Secretaría por qué llama a cada familia, no por una ventaja medida.

**40. ¿Por qué el azar da 1,08 y no 1,00?**
Porque el sorteo es por estudiante y la familia toma el máximo, igual que con cualquier puntaje: una familia con más hijos tiene más números en el sorteo. Las familias con caso tienen más hijos en promedio (1,45 frente a 1,30), así que el azar por estudiante da 1,12 en C4. Con un sorteo uniforme por familia da 1,00. Nuestra referencia era, por lo tanto, algo más exigente que el azar puro.

**41. Nadie fuera de LEMAS puede reproducir los resultados y con la base sintética el cuaderno 03 concluye lo contrario. ¿Por qué confiar en las cifras?**
Porque son datos de menores y no se pueden publicar. Lo que sí se puede verificar: el código completo y sus 263 pruebas; los cuadernos 04, 05, 07, 08 y el de sobreajuste ejecutados con datos reales, con sus salidas agregadas; la huella SHA-256 del sistema congelado antes de abrir C5, y el registro de decisiones fechadas. La base sintética respeta los totales, no las relaciones entre variables: sirve para probar el código, no para reproducir conclusiones, y el README lo advierte.

**42. La razón de selección de las becadas es 0,66 y su recall casi la mitad. ¿Por qué no lo corrigieron en la lista?**
Porque con 11 eventos la diferencia es incierta y una corrección (reservar cupos para becadas) se habría ajustado a muy pocos casos. Lo que hicimos fue advertirlo en la aplicación, recomendar que Secretaría revise también a las becadas con atrasos y medirlo cada mayo acumulando cohortes. Si la brecha se confirma en 2027, la medida sería reservar una parte de la lista para ese grupo. Con intervalos de Wilson, el recall de las becadas va de 5 % a 48 % y el de las demás de 22 % a 44 %; la prueba exacta de Fisher da p = 0,49. No es una brecha demostrable, pero tampoco descartable.

**43. Procesaron datos seudonimizados de menores en Colab, fuera del país, sin informar a las familias. ¿Quién responde?**
LEMAS, como responsable del tratamiento, con nuestra participación como equipo técnico. Hubo autorización institucional, los datos estaban seudonimizados y la clave no salió de LEMAS; aun así, son datos personales y lo declaramos como limitación. Para el uso permanente, el modo institucional procesa todo en un equipo de LEMAS. Antes de usarlo, LEMAS debe informar a las familias, hacer la evaluación de impacto y confirmar la base legal.

**44. ¿Cómo se repartió el trabajo y qué parte puede explicar cada uno?**
Guillermo, Product Owner, aportó el dominio institucional, los datos reales y la validación con usuarios; José, Scrum Master, el repositorio, el modelado, la optimización y la aplicación. El historial de git muestra una sola cuenta porque acordamos revisar y conversar juntos cada cambio y que Guillermo, que custodia los datos reales, sea quien lo suba (D61). *Para preparar:* que cada uno elija dos o tres decisiones del registro que pueda explicar en detalle.

**45. ¿Cuánto esfuerzo ahorra la lista?**
Con la lista se hacen 7,5 llamadas por cada familia en riesgo encontrada (165 llamadas, 22 casos); al azar serían unas 15. Es la mitad del esfuerzo por caso, con el mismo personal.

**46. ¿Cómo sabrán si la llamada sirve, y cuánto tardarán?**
Reservando al azar una parte de la lista sin llamar y comparando su tasa de no matrícula con la de las familias llamadas. Con la mitad de la lista reservada, detectar que la llamada reduce los casos a la mitad exige unas 634 familias, unas 4 campañas; un efecto del 25 % exige unas 2.900, unas 18 campañas. Con 165 familias al año solo veríamos un efecto grande; por eso proponemos ampliar la reserva a la segunda etapa o acumular cohortes.

**47. ¿El promedio final ya se conocía el 20 de febrero?**
Sí. LEMAS confirmó que los promedios finales del ciclo de origen están cerrados al 20 de febrero de cada año, así que no es información posterior al corte. Además, solo lo usa el modelo de apoyo, no la regla D2.

## Consejos para responder

- Empezar por la respuesta corta y luego dar una cifra.
- Si no se sabe algo, decirlo y explicar cómo se comprobaría.
- No defender a los modelos de IA más de lo que muestran los datos: la honestidad sobre el resultado es una fortaleza del proyecto.
