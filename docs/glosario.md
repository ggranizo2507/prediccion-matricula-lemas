# Glosario

Siglas y términos que se repiten en la documentación, en el orden en que suelen aparecer.

## Población, tiempo y datos

| Término | Significado |
|---|---|
| **Evento (no matrícula)** | El estudiante tenía la reserva aprobada para el ciclo siguiente y no pagó la matrícula hasta el 30 de abril. Es lo que se predice (`y_no_matricula = 1`) |
| **Familia o representante** | La unidad de contacto: una persona representante, con uno o más estudiantes. Una familia "tiene caso" si al menos uno de sus estudiantes no se matriculó |
| **t0** | Fecha de corte de la predicción: 20 de febrero. Solo se usa lo que se sabía ese día |
| **H** | Fin del horizonte: 30 de abril. Un pago posterior cuenta como no matrícula |
| **C1 a C5** | Cohortes por ciclo de origen: C1 = 2021-2022 (excluida), C2 = 2022-2023 y C3 = 2023-2024 (entrenamiento), C4 = 2024-2025 (selección y calibración), C5 = 2025-2026, con la matrícula 2026-2027 (prueba final, usada una sola vez) |
| **k** | Número de familias que cada sede puede contactar: 118 en Mucho Lote 1 y 47 en Mucho Lote 2 (dos veces el promedio histórico de familias con caso) |
| **Seudónimo** | Código que reemplaza la cédula, calculado con HMAC-SHA256 y una clave que guarda un custodio de LEMAS. Sin la clave no se puede volver a la cédula |
| **Base sintética** | Datos artificiales con la estructura de la base real (`origen_datos = SINTETICO`). Sirven para probar el código; sus conclusiones no describen a LEMAS |
| **Modo demostración / institucional** | La app pública solo acepta datos sintéticos. El modo institucional, que solo funciona en un equipo de LEMAS, seudonimiza el Excel en memoria y muestra nombres a personal autorizado |

## Reglas, modelos y líneas base

| Término | Significado |
|---|---|
| **A** | Selección al azar de k familias (referencia mínima) |
| **D** | Regla "más atrasos primero": ordena por número de pensiones pagadas tarde |
| **D2** | **La solución elegida.** Regla de señales administrativas: primero quien pagó tarde la matrícula anterior, luego la reserva extraordinaria y, dentro de cada grupo, más pensiones pagadas tarde. Se define en `src/reglas.py` |
| **RL** | Regresión logística base, sin optimizar (referencia de la Fase 1) |
| **Logística híbrida** | El mejor modelo de aprendizaje automático: las señales de D2 más variables académicas. No ordena la lista; se usa, calibrado, para probabilidades y la proyección |
| **R, B0, B1** | Líneas base de las **probabilidades** (no ordenan familias): R = "si reservó, continúa"; B0 = clase mayoritaria; B1 = tasa histórica de no matrícula |
| **Calibración de Platt** | Ajuste que convierte el puntaje del modelo en una probabilidad que coincide, en promedio, con lo observado. Se hizo con C4 |
| **D01 a D62** | Decisiones fechadas del proyecto, en [planificacion.md](planificacion.md) |

## Métricas

| Término | Significado |
|---|---|
| **Precision@k** | De las k familias de la lista, qué parte tenía caso |
| **Recall@k** | De todas las familias con caso, qué parte entró en la lista |
| **Lift@k** | Precision@k dividida por la tasa de familias con caso. 1 = igual que el azar; 2 = el doble de casos que el azar. Meta del proyecto: 1,20 o más |
| **PR-AUC (AP)** | Área bajo la curva precisión-recall: calidad del orden completo, adecuada cuando el evento es poco frecuente |
| **ROC-AUC** | Probabilidad de que un caso quede por encima de un no caso. Con eventos raros es menos informativa que la PR-AUC |
| **Brier** | Error cuadrático medio de las probabilidades. Menor es mejor |
| **MAPE** | Error porcentual medio de la proyección de matrículas por sede y subnivel |
| **IC 95 %** | Intervalo de confianza: rango plausible del resultado. Aquí se obtiene por *bootstrap*, remuestreando familias |
| **Bootstrap pareado** | Se remuestrean las mismas familias para dos sistemas a la vez, para estimar la incertidumbre de su **diferencia** |
| **EPV** | Eventos por predictor: casos de no matrícula disponibles por cada variable del modelo. Con pocos, el modelo es inestable |
| **SMD** | Diferencia estandarizada de medias: cuánto difiere una variable entre dos cohortes. Sobre 0,20 se considera relevante |
| **Razón de selección** | Proporción de un grupo que entra en la lista dividida por la de otro grupo. Bajo 0,80 se suele considerar una alerta de equidad |

## Optimización

| Término | Significado |
|---|---|
| **Optuna / TPE** | Librería de optimización de hiperparámetros; TPE es su método de búsqueda bayesiana |
| **fANOVA** | Método que reparte la variación del resultado entre los hiperparámetros: indica cuáles importan |
| **Dependencia parcial (PDP)** | Cómo cambia el resultado al mover un hiperparámetro, promediando los demás |
| **H² de Friedman** | Fuerza de la interacción entre dos hiperparámetros: 0 = actúan por separado |
| **Sobreajuste / subajuste** | El modelo memoriza el entrenamiento y falla en datos nuevos / el modelo es demasiado simple incluso para el entrenamiento |

## Normas y documentos

| Término | Significado |
|---|---|
| **LOPDP** | Ley Orgánica de Protección de Datos Personales del Ecuador (2021) |
| **SPDP** | Superintendencia de Protección de Datos Personales del Ecuador |
| **RGPD / CCPA** | Reglamento General de Protección de Datos de la Unión Europea / ley de privacidad de California. Se citan como referencia |
| **v5 / v6** | Documento técnico integral del proyecto. El v5 se entregó en el curso; el v6, que lo actualiza, está en [`Documento_Tecnico_Prediccion_Matricula_v6.docx`](Documento_Tecnico_Prediccion_Matricula_v6.docx) |
| **Canvas, Checklist, Ficha técnica** | Entregas anteriores del curso (Canvas SMART, Checklist de validación y Ficha de decisión técnica). No forman parte del repositorio |
