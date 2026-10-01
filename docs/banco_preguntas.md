# Banco de preguntas para la defensa

Respuestas cortas (20–40 segundos) con las cifras reales del proyecto. Las cifras provienen de [modelado.md](modelado.md), [optimizacion.md](optimizacion.md) y [consideraciones_eticas.md](consideraciones_eticas.md).

Sugerencia de reparto: **Guillermo** responde problema, resultados, app y negocio; **José** responde datos, metodología, optimización y ética.

## A. Problema y alcance

**1. ¿Por qué este problema necesita IA y no basta con una hoja de cálculo?**
Porque la pregunta es de priorización bajo capacidad limitada: con 10 personas y 69 días hay que ordenar a más de mil familias. La IA nos permitió probar de forma rigurosa qué señales ordenan mejor y medir la incertidumbre. El resultado fue que una regla simple (D2) ordena mejor que los modelos, y eso solo se puede afirmar después de compararlos con validación temporal.

**2. ¿Qué significa exactamente "no matrícula"?**
`y_no_matricula = 1` cuando un estudiante con reserva aprobada al 20 de febrero (t0) no tiene la matrícula pagada al 30 de abril (H). La unidad de decisión es la familia (representante), porque la llamada se hace al representante.

**3. ¿Qué es k y por qué es 118 y 47?**
Es el número de familias que cada sede puede contactar en la ventana. Se fijó en el doble del promedio histórico de casos por sede (decisión de la institución): 118 en Mucho Lote 1 y 47 en Mucho Lote 2. Representa capacidad, por eso no cambia al cambiar el ciclo en la app.

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
Porque el sistema se usará para predecir el año siguiente. Mezclar años filtraría información del futuro. Entrenamos con C2–C3, seleccionamos y calibramos en C4 y probamos una sola vez en C5.

**11. ¿Qué es el Lift@k?**
Cuántas veces más casos encuentra la lista que una selección al azar del mismo tamaño. Lift 1,97 significa casi el doble de casos que llamando al azar a k familias.

**12. ¿Qué modelos probaron?**
Regresión logística con elastic-net, HistGradientBoosting con monotonía creciente en atrasos, y una logística híbrida con las señales de D2 más variables académicas. Se compararon con el azar (A), la regla D (más atrasos primero) y la regla D2.

**13. ¿Qué es la regla D2?**
Un puntaje administrativo: 100 por pago tardío de la matrícula anterior, más 20 por reserva extraordinaria, más el número de pensiones atrasadas. Se ordena de mayor a menor, y los empates se rompen con la probabilidad del modelo.

**14. ¿No es injusto comparar modelos con una regla diseñada mirando los datos?**
La regla se definió con conocimiento del negocio y se evaluó con la misma disciplina que los modelos: seleccionada en C4 y probada una sola vez en C5. Allí mantuvo su desempeño (1,97, IC [1,24; 2,56]).

## D. Optimización y diagnóstico

**15. ¿Cómo optimizaron los hiperparámetros?**
Con Optuna (TPE, semilla 42), 60 pruebas por modelo, 180 en total, maximizando PR-AUC entrenando en C2 y evaluando en C3. Ejemplo: la logística pasó de 0,062 a 0,106 de PR-AUC entre la peor y la mejor prueba.

**16. ¿Hubo sobreajuste o subajuste?**
El gradient boosting se sobreajustó: PR-AUC 0,245 en entrenamiento y 0,104 en C4. La logística mostró subajuste leve (0,140 frente a 0,113), porque las señales son débiles. La híbrida fue estable (0,126 frente a 0,125) pero con poca capacidad.

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
Cerca del 70 % de los casos no deja señales en los datos: mudanzas, cambios de colegio o decisiones familiares. Para esos casos haría falta información nueva, como una encuesta de intención.

## F. Ética y aplicación

**23. ¿Qué sesgos encontraron?**
La regla detecta menos casos en familias becadas (recall 18 % frente a 32 %), aunque con solo 11 eventos la diferencia es incierta. Los atrasos reflejan la situación económica. Por eso la lista se usa para ofrecer apoyo, no para presionar, y recomendamos revisar también a becados con atrasos.

**24. ¿Usaron la nacionalidad o información sensible?**
No. La nacionalidad nunca es predictor, y no usamos motivos del DECE ni información de salud. La cédula genérica de familias extranjeras se trató como problema de calidad, no como variable.

**25. ¿Qué pasa si alguien sube datos reales a la app pública?**
La versión pública funciona en modo demostración y solo acepta datos sintéticos. Además, en cualquier modo rechaza archivos con columnas de identificación (CI, cédula, nombre, teléfono, correo, dirección). El modo institucional se ejecuta solo en un equipo local dentro de LEMAS.

**26. ¿Quién toma la decisión final?**
Siempre una persona de Secretaría. La app muestra el motivo de cada familia para que la decisión sea explicable y revisable.

**27. ¿Cómo se mantendría el sistema?**
Cada mayo, cuando se conoce el resultado del ciclo, se compara la lista con las matrículas reales, se actualiza el historial y se revalidan la regla y el modelo con la cohorte nueva. Si cambian las políticas de cobro o de reservas, D2 debe revalidarse antes de usarse. El siguiente paso es la validación con usuarios (anexo E del documento técnico).

## Consejos para responder

- Empezar por la respuesta corta y luego dar una cifra.
- Si no se sabe algo, decirlo y explicar cómo se comprobaría.
- No defender a los modelos de IA más de lo que muestran los datos: la honestidad sobre el resultado es una fortaleza del proyecto.
