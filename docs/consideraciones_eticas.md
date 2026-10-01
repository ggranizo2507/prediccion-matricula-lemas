# Consideraciones éticas

El sistema trata datos de **menores de edad y sus familias** y orienta acciones de una institución educativa sobre ellas. Por eso la ética no es un anexo: condicionó el diseño de los datos, del modelo, de la aplicación y de la forma de comunicar los resultados.

## 1. Propósito y uso permitido

| Uso permitido | Uso prohibido |
|---|---|
| Priorizar **contactos de apoyo** (información, planes de pago, atención de inquietudes) entre el 20 de febrero y el 30 de abril | Negar, condicionar o retirar cupos, reservas, becas o servicios |
| Planificar cupos, paralelos y personal con la proyección agregada | Presionar o cobrar a familias por aparecer en la lista |
| Evaluar el proceso de reservas de forma agregada | Perfilar a estudiantes o familias con fines distintos al aprobado |

La lista es un **apoyo a la decisión humana**. La aplicación no contacta a nadie ni toma decisiones: Secretaría revisa cada caso.

## 2. Privacidad y protección de datos

**Marco:** Ley Orgánica de Protección de Datos Personales del Ecuador (LOPDP) e interés superior del niño. Autorización institucional de LEMAS del 01-oct-2026.

| Riesgo | Medida implementada | Dónde |
|---|---|---|
| Exposición de identidades | Seudonimización **HMAC-SHA256** de las cédulas del estudiante y del representante, con clave custodiada por LEMAS. Se eliminan nombres, código interno y columnas financieras | `tools/seudonimizar.py`, `00a` |
| Reidentificación por terceros | Solo el custodio puede revertir los seudónimos, con la clave y dentro de LEMAS | `seudonimizar.py reidentificar` |
| Publicación accidental | `.gitignore` bloquea Excel, `base_seud.csv`, claves, actas, perfiles y modelos reales; el repositorio contiene solo código, datos **sintéticos** y agregados | `.gitignore` |
| Inferencia a partir de agregados | Supresión de celdas con **menos de 5 casos** en tablas y figuras; con datos reales, el gráfico SHAP por estudiante no se muestra | `privacidad.min_celda`, cuadernos |
| Datos reales en un servidor público | **Aplicación en dos modos (D42):** la versión pública rechaza todo archivo no sintético, y ambos modos rechazan archivos con cédulas, nombres o códigos | `src/inferencia.py` |
| Retención | Las copias de trabajo en Colab se borran al terminar cada sesión; los modelos reales no salen de LEMAS; se propone eliminarlos 30 días después de la aceptación académica | Manual de usuario, v5 5.7 |
| Minimización | Solo se usan variables necesarias y conocidas en t0. No se usan diagnósticos, motivos sensibles (DECE) ni texto libre | `config.yaml`, v5 5.6 |

## 3. Sesgos identificados y cómo se abordaron

| Sesgo o riesgo | Evidencia | Mitigación |
|---|---|---|
| **Proxy socioeconómico:** los atrasos en pensiones reflejan la capacidad de pago | La regla D2 se apoya en señales de pago | Uso exclusivo para contacto de **apoyo**: ofrecer planes de pago y no presionar. La decisión final es humana. Se documenta como limitación |
| **Menor detección en familias becadas** | Recall de D2 en C5: 0,18 en becadas frente a 0,32 en no becadas (11 eventos; diferencia incierta) | Se advierte en la app y en el manual; se recomienda revisar también a becadas con atrasos; se monitoreará con nuevas cohortes |
| **Diferencias entre sedes** | Mucho Lote 1 tiene más familias seleccionadas (18 %) que Mucho Lote 2 (10 %) | k proporcional al historial de cada sede y editable en la app; la precisión es similar (0,12 y 0,17) |
| **Familias extranjeras con cédula genérica** | Un representante figuraba con 39 estudiantes | Cada estudiante cuenta como un contacto individual (D29). La marca `representante_atipico` **no es predictor**, porque equivaldría a usar la nacionalidad (D33). En C5 no hubo casos para evaluar la equidad |
| **Cambios entre cohortes** | C1 mostró diferencias en promedio, sede y conducta | Auditoría de comparabilidad; C1 excluida con regla registrada de antemano (D14) |
| **Sesgo de confirmación del equipo** | Riesgo de probar modelos hasta que uno gane | Un único intento adicional registrado antes de verlo (D39); C5 evaluada una sola vez con el sistema congelado (D38) |

## 4. Impacto social

**Potencial positivo**
- Contacto **oportuno** con familias que podrían necesitar apoyo, antes de que pierdan el cupo.
- Mejor planificación de cupos y docentes, lo que da estabilidad a los estudiantes.
- Transparencia: la regla D2 se puede explicar a cualquier familia en una frase.

**Potencial negativo y salvaguardas**
| Riesgo | Salvaguarda |
|---|---|
| Estigmatizar a familias con dificultades económicas | La lista es confidencial, usa seudónimos y está dirigida a ofrecer ayuda |
| Contactos percibidos como presión de cobro | Protocolo de contacto con enfoque de apoyo (manual de usuario) |
| Confianza excesiva en "la IA" | La app explica que los modelos no superaron a la regla y muestra la incertidumbre (IC 95 %) |
| Que no se contacte a quien no aparece en la lista | La lista cubre alrededor del 30 % de los casos; Secretaría mantiene su atención habitual a todas las familias |

## 5. Honestidad sobre las capacidades
- **No se exageran resultados:** los modelos de aprendizaje automático no superaron a la regla D2 en la prueba final, y así se informa en el README, en la app y en el pitch.
- Las probabilidades individuales **no mejoran a la tasa histórica** (Brier 0,0648 frente a 0,0647): la app lo advierte.
- Las métricas se reportan con **intervalos de confianza** y en una cohorte nunca usada para ajustar.
- El sistema **no predice** estudiantes nuevos, reservas pendientes ni abandono durante el año.

## 6. Limitaciones éticas reconocidas
1. Las familias no fueron consultadas sobre el uso de sus datos para este análisis. La base legal es el interés legítimo institucional, con autorización de LEMAS; un despliegue permanente debería informar a las familias.
2. El número de eventos por grupo es pequeño: la equidad por beca, subnivel o nacionalidad no puede afirmarse con certeza.
3. La regla D2 refleja el pasado. Si cambian las políticas de cobro o de reservas, debe revalidarse.
4. No se midió el efecto causal del contacto: no se sabe aún si llamar a una familia cambia su decisión.

## 7. Gobernanza propuesta para LEMAS
| Rol | Responsabilidad |
|---|---|
| Custodio de datos | Guarda la clave, aprueba cada extracción, reidentifica la lista y elimina las copias |
| Admisiones / Secretaría | Usa la lista solo para contacto de apoyo y registra el resultado del contacto |
| Dirección | Revisa cada año los resultados agregados y la equidad, y decide si se mantiene el sistema |
| Equipo técnico | Revalida la regla y el modelo con cada cohorte nueva (mayo) |

## 8. Lista de verificación
- [x] Autorización institucional (01-oct-2026)
- [x] Seudonimización con clave custodiada y acta con huella SHA-256
- [x] Repositorio sin datos reales ni modelos reales
- [x] Supresión de celdas menores a 5
- [x] Variables sensibles excluidas (nacionalidad, DECE, texto libre)
- [x] Análisis de equidad por sede, beca, subnivel y cédula genérica
- [x] Decisión humana obligatoria; la app no actúa sola
- [x] Limitaciones comunicadas en la app, el README y el pitch
- [ ] Comunicación a las familias (recomendado antes de un uso permanente)

**Referencias:** LOPDP (Registro Oficial, 2021); Fairlearn (fairlearn.org); fast.ai Practical Data Ethics; Google AI Principles; Mitchell et al. (2019), *Model Cards for Model Reporting*.
