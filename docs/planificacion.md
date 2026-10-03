# Planificación del proyecto

Documento vivo del proyecto: problema, objetivos, alcance, cronograma, recursos, riesgos, **registro de decisiones** (D01–D43) e inconsistencias entre documentos. El detalle académico completo está en el documento integral v5.

## 1. Problema y relevancia
No todas las reservas aprobadas en LEMAS terminan en matrícula pagada (entre 6 % y 11 % por cohorte). La institución se entera tarde, sin tiempo para ofrecer apoyo ni para planificar cupos, paralelos y personal. El proyecto entrega, al 20 de febrero, una **lista priorizada de familias** para contactar entre el 20 de febrero y el 30 de abril, y una **proyección de matrícula** por sede y subnivel.

## 2. Objetivo SMART
Desarrollar en 6 semanas (14-sep a 25-oct-2026) un sistema que, validado temporalmente con cinco cohortes, priorice familias con una **Precision@k familiar mayor que la tasa base** y **Lift@k ≥ 1,20** (IC 95 % bootstrap), respetando la capacidad de contacto de cada sede.
**Resultado (C5):** D2 obtuvo Lift@k = 1,97 [1,24; 2,56] y Precision@k = 0,133, frente a una tasa base familiar de 0,068. ✅

## 3. Alcance
- **Incluye:** estudiantes antiguos con reserva aprobada antes de t0, excepto 3.º de bachillerato; priorización por representante; proyección; app; documentación y ética.
- **Excluye:** estudiantes nuevos, reservas pendientes o rechazadas, predicción de abandono durante el año, despliegue productivo integrado y contacto automático.

## 4. Cronograma planificado frente a real

| Fase | Contenido | Planificado | Real |
|---|---|---|---|
| Fase 1 | Datos, seudonimización, EDA y auditoría de cohortes | 25-sep a 03-oct | 25-sep a 01-oct ✅ |
| Fase 2 | Modelado, optimización y evaluación final | 04-oct a 10-oct | 01-oct ✅ (adelantada) |
| Fase 3 | App Streamlit, ética y documentación | 11-oct a 15-oct | Desde 01-oct (en curso) |
| Fase 4 | Pulido final, pitch y video de respuestas | 16-oct a 18-oct | — |

El documento v5 y el Checklist mantienen el cronograma original de 6 semanas (I5); el plan comprimido de 3 semanas se aprobó al inicio del trabajo.

## 5. Recursos
- **Equipo:** Guillermo Granizo (Product Owner, dominio y datos reales) y José Ulloa (Scrum Master, repositorio, código y app).
- **Técnicos:** Google Colab (autorizado), GitHub con integración continua y Streamlit Community Cloud. Costo incremental: USD 0.

## 6. Riesgos y estado

| Riesgo | Mitigación | Estado |
|---|---|---|
| Acceso a datos y autorización | Seudonimización y autorización institucional | Cerrado (01-oct) |
| Fuga temporal | Corte t0, guardas anti-fuga y C5 intacta hasta el final | Cerrado |
| Pocos eventos y sobreajuste | Modelos regularizados, diagnóstico y reglas de referencia | Materializado: los modelos de ML no superaron a D2 (documentado) |
| Comparabilidad de C1 | Auditoría con regla registrada de antemano | Cerrado: C1 excluida |
| Sesgos | Análisis de equidad y uso solo para apoyo | Abierto: menor recall en becadas (monitorear) |
| Exposición de datos en la app | Dos modos; la app pública solo acepta sintéticos | Cerrado (D42) |

## Registro de decisiones

| # | Fecha | Decisión | Origen |
|---|---|---|---|
| D01 | 25-sep-2026 | Cohortes C1–C5: ciclo de origen 2021–2022 a 2025–2026; t0 = 20 de febrero y H = 30 de abril del año de destino | Equipo |
| D02 | 25-sep-2026 | Etiqueta del modelo: `y_no_matricula = 1` cuando no hay pago de matrícula del ciclo de destino entre t0 y H (equivale a `1 − matricula_efectiva` del v5) | Plan aprobado |
| D03 | 25-sep-2026 | Matrículas después del 30 de abril: se reportan aparte como tardías y cuentan como no matrícula en plazo | Plan aprobado |
| D04 | 25-sep-2026 | Seudonimización con HMAC-SHA256 y clave custodiada por LEMAS; se eliminan nombres y cédulas | Equipo |
| D05 | 25-sep-2026 | Unidad de contacto: representante (`cedulap`). Hermanos con distinto representante cuentan como contactos distintos | Equipo |
| D06 | 25-sep-2026 | k por sede = promedio de representantes con no matrícula en las cohortes de entrenamiento; se contrasta con el personal: Mucho Lote 1 (5 secretarias + 1 de Admisiones) y Mucho Lote 2 (3 secretarias + 1 de Admisiones) | Equipo |
| D07 | 25-sep-2026 | Predictores: sede, subnivel, curso, años de permanencia (desde el año de ingreso del código), promedio, conducta, beca, pensiones pagadas tarde, tipo de reserva, hermanos en LEMAS y puntualidad de la matrícula anterior | Equipo |
| D08 | 25-sep-2026 | Elegibles: Reserva = SI; RColegio ∈ {Aprobar, Aprobar extraordinaria}; reserva antes de t0; curso distinto de 3.º BGU. "En proceso" se reporta aparte | Equipo |
| D09 | 25-sep-2026 | Sin fecha de aprobación de la reserva: análisis de sensibilidad solo con "Aprobar" | Equipo |
| D10 | 25-sep-2026 | Conducta en letras A–E en todos los años (2021–2022 convertidos con la regla institucional), codificada A = 5 … E = 1 | Equipo |
| D11 | 25-sep-2026 | La fecha de reserva no es predictor; se usa `Tiempo` (ordinaria o extraordinaria) | Equipo |
| D12 | 25-sep-2026 | Repositorio público con datos sintéticos; la app pública usa un modelo entrenado con datos sintéticos; interfaz en Streamlit; licencia MIT (datos excluidos) | Plan aprobado |
| D13 | 25-sep-2026 | Todo el código se entrega listo para Google Colab | Equipo |
| D14 | 26-sep-2026 | **C1 condicional:** se entrena con C1–C3 y con C2–C3, ambas se evalúan en C4, y C1 entra solo si no reduce la Precision@k familiar más que la tolerancia configurada | Ficha técnica |
| D15 | 26-sep-2026 | **Auditoría obligatoria de Sprint 1:** conteo de eventos de no matrícula por estudiante y por representante en cada cohorte, con mínimo de eventos y regla EPV | Checklist SMART |
| D16 | 27-sep-2026 | Figuras del proyecto a 300 DPI | Actividad semana 3 |
| D17 | 28-sep-2026 | La comparabilidad descriptiva de C1 (diferencias estandarizadas) se calcula frente a C2–C4; la decisión de incluir C1 usa solo C4 como validación | v5_final, 5.3.4 |
| D18 | 28-sep-2026 | Umbrales de auditoría: al menos 30 eventos de no matrícula por cohorte, EPV ≥ 10 en el entrenamiento y tolerancia de 0,02 en Precision@k familiar para incluir C1 | v5_final, 5.3.4 y 6.3 |
| D19 | 28-sep-2026 | El notebook 02 genera la tabla "Reporte obligatorio por cohorte" de la sección 6.3 del v5 y el análisis de sensibilidad solo con "Aprobar" | v5_final, 5.3.1 y 6.3 |
| D20 | 30-sep-2026 | La llave del estudiante es la cédula (seudonimizada); el código interno solo aporta el año de ingreso y luego se elimina | Equipo (el código cambia con reingreso o cambio de sede) |
| D21 | 30-sep-2026 | `beca` vacía = sin beca (0) | Equipo |
| D22 | 30-sep-2026 | `RColegio` se normaliza a aprobada, aprobada_extraordinaria, pendiente y sin_reserva. Los matriculados sin reserva aprobada (autorización del director) quedan fuera de la población y se reportan aparte | Equipo |
| D23 | 30-sep-2026 | "Nuevo" = no estaba en la hoja del año anterior (no se usa el prefijo del código) | Equipo |
| D24 | 30-sep-2026 | Se eliminan `Orden`, `saldo`, `deuda` y `statusp`; la columna de pago se llama `fecha_pago` | Equipo |
| D25 | 30-sep-2026 | Datos disponibles de 2021–2022 a 2026–2027: fechas de pago, notas y becas de todos los años; `# meses caído` se calcula desde el registro mensual de pagos (recomendado: mayo a enero) | Equipo |
| D26 | 30-sep-2026 | Encabezados distintos entre hojas: `anoaa` (2022–2026) se lee como `anoa` y `Fecha` (2022–2025) como `Fecha Reserva` (`alias_columnas` en `config.yaml`). La hoja 2026 solo aporta `fecha_pago`, porque es únicamente destino de C5 | Perfil de datos reales |
| D27 | 30-sep-2026 | El curso se normaliza entre años: se quita "EGB" y "Primer/Segundo/Tercer Curso" pasa a "… de bachillerato" | Perfil de datos reales (88 textos de Nivel) |
| D28 | 30-sep-2026 | El curso terminal (3.º de bachillerato) se detecta en el nivel o en el curso normalizado, para cubrir el formato "Tercer Curso" | Perfil de datos reales |
| D29 | 30-sep-2026 | Un representante con más de 6 estudiantes en el año se trata como atípico: cada estudiante es su propio contacto y no cuenta como hermano | Figura 4 (un representante con 39 estudiantes) |
| D30 | 30-sep-2026 | Referencias obligatorias en C4: azar (A), más atrasos primero (D), señales administrativas (D2) y regresión logística base (RL). Se usan los nombres del v5: R, B0 y B1 no ordenan familias y se evalúan con Brier y error de proyección en la Fase 2. Se agrega un IC 95 % por bootstrap a la decisión sobre C1, como dato informativo | Equipo |
| D31 | 30-sep-2026 | Base sintética calibrada con `perfil_lemas.json` (sedes, beca, promedio, conducta, atrasos; ~1500 estudiantes por año; tasa ≈ 8,5 %). Los parámetros agregados están en `data/synthetic/parametros_calibracion.json` | Fase 1 |
| D32 | 01-oct-2026 | k por sede = **2 ×** el promedio histórico de representantes con no matrícula (`capacidad.multiplicador_k`), porque la capacidad de contacto supera con holgura el promedio. Se prioriza el recall | Equipo |
| D33 | 01-oct-2026 | El representante con 39 estudiantes es una **cédula genérica** que se usa para familias extranjeras sin cédula ecuatoriana. Se confirma el tratamiento D29. `representante_atipico` **no** es predictor, porque equivaldría a usar la nacionalidad | Equipo |
| D34 | 01-oct-2026 | La conversión de conducta 2022 a letras es correcta (18 % de B ese año); la variable se mantiene sin ajustes | Equipo |
| D35 | 01-oct-2026 | Se confirma que la columna `Fecha` de 2022–2025 es la fecha en que el padre hace la reserva (= `Fecha Reserva`) | Equipo |
| D36 | 01-oct-2026 | Fase 2: dos modelos obligatorios (regresión logística elastic-net y gradient boosting con monotonía creciente en atrasos), optimizados con Optuna (TPE, semilla 42) maximizando la PR-AUC en la validación interna temporal (C2 → C3) | Plan aprobado |
| D37 | 01-oct-2026 | La selección en C4 se hace por Lift@k (desempate: PR-AUC) frente a la mejor regla (D o D2). Si el modelo no la supera, se recomienda la regla para priorizar y el modelo se usa solo para probabilidades y proyección | Equipo |
| D38 | 01-oct-2026 | Calibración de Platt en C4 sobre el modelo congelado; huella SHA-256 registrada antes de abrir C5; C5 se evalúa una sola vez (`EVALUAR_C5`) | v5, 6.2 |
| D39 | 01-oct-2026 | **Un único intento adicional, registrado antes de verlo en C4:** logística híbrida con las señales de D2 (pago anterior tardío, reserva extraordinaria y atrasos por tramos 0 / 1-2 / 3-5 / 6+) más es_nuevo, conducta "no A", subnivel y promedio; Optuna solo ajusta C y el balanceo (C2 → C3). Si en C4 no supera a la mejor regla, la priorización final es D2 y no se prueban más variantes | Equipo (resultado C4: RL 1,40 y árboles 1,06 frente a D2 1,93) |
| D40 | 01-oct-2026 | **Resultado de D39 en C4 (datos reales):** la logística híbrida obtiene Lift@k = 1,53, frente a 1,93 de D2. **La priorización final es la regla D2.** La logística híbrida, calibrada en C4, se conserva solo para probabilidades y proyección. No se prueban más variantes. La regresión logística (1,40) y el gradient boosting (1,06) se reprodujeron idénticos | Notebook 03 |
| D41 | 01-oct-2026 | **Prueba final en C5 (única):** D2 obtiene Lift@k = 1,97 [1,24; 2,56], Precision@k = 0,133 y Recall@k = 0,30; la logística híbrida obtiene 0,98 [0,47; 1,52]. Brier del modelo calibrado = 0,0648, frente a 0,0647 de B1. MAPE de 2,8 % (igual que B1). La solución final es la regla D2 para priorizar, con probabilidades y proyección del modelo calibrado presentadas junto a B1 | Notebook 03 · ver `docs/modelado.md` |
| D42 | 01-oct-2026 | **Aplicación en dos modos:** *demo* pública (Streamlit Community Cloud) que solo acepta datos sintéticos, e *institucional* (`LEMAS_MODO=institucional`), que corre solo en un equipo de LEMAS con `base_seud.csv` y procesa en memoria. Ambos modos rechazan archivos con identificadores directos. La reidentificación de la lista la hace únicamente el custodio | Equipo (aprobado por el PO) |
| D43 | 01-oct-2026 | La app prioriza con D2 (desempate: probabilidad del modelo), muestra la probabilidad calibrada junto a la tasa histórica y la proyección junto a B1. En modo demo el sistema se reentrena con la base sintética usando los hiperparámetros reales (C = 9, balanceado) | Fase 3 |
| D44 | 01-oct-2026 | App demo publicada en Streamlit Community Cloud: https://continuidad-matricula-lemas.streamlit.app/ (rama `main`, `app/app.py`, sin `LEMAS_MODO`) | Equipo |
| D45 | 01-oct-2026 | **Modo institucional sin Colab:** la aplicación, solo en modo institucional y en el mismo equipo (`localhost`), recibe el Excel de LEMAS y la clave del custodio, seudonimiza en memoria con la misma técnica del cuaderno 00a y verifica que no queden identificadores. Incluye la pestaña **Lista con nombres** para personal autorizado. La clave **se sube en cada uso** (no se guarda en el equipo) y solo se ofrece crear una clave nueva si LEMAS confirma que no tiene. La versión pública no cambia: no tiene ninguna de estas funciones. Arranque con `iniciar_lemas.bat` | Equipo (para que el personal de LEMAS no dependa de Colab ni de la línea de comandos) |
| D46 | 02-oct-2026 | **Diagnóstico de sobreajuste y subajuste (actividad de la semana 3):** cuaderno `overfitting_analysis.ipynb` y reporte `diagnostic_report.pdf`. Reglas prácticas (no pruebas estadísticas): sobreajuste si la brecha relativa de PR-AUC supera 30 %; subajuste si, sin esa brecha, la PR-AUC de validación no llega a 1,5 veces el azar; una estrategia mejora o empeora solo si la PR-AUC cambia al menos 0,005. Se fijaron antes de ejecutar el cuaderno con datos reales, pero cuando ya se conocían las PR-AUC de entrenamiento y de C4 de la Fase 2. Se entrena con las cohortes de la Fase 2 y se valida con C4; **C5 no interviene**. La parada temprana se elige en la validación interna y solo puede recortar. Seis estrategias con antes/después y dos modelos de control. No cambia la decisión final (D40) | Actividad de la semana 3 |

La decisión de C1 con datos reales se guarda en `results/metrics/decision_c1_real.json`, generado por el notebook 02, y se transcribe aquí.

**Decisión C1 (01-oct-2026, datos reales):** C1 **se excluye**. Precision@k en C4 = 0,112 con C1 frente a 0,139 sin C1 (Δ = −0,027 > 0,02). IC 95 % bootstrap de Δ = [−0,061; +0,012]. Configuración final: entrenamiento C2+C3, selección C4, prueba C5. k = 118 (Mucho Lote 1) y 47 (Mucho Lote 2). Referencia a superar en la Fase 2: D2 (Lift@k = 1,93 en C4).

## Estado de las inconsistencias entre documentos (revisión del 28-sep-2026)

| # | Documento | Inconsistencia | Estado |
|---|---|---|---|
| I1 | v5 y Ficha | Convención de la etiqueta (1 = matrícula en documentos; 1 = no matrícula en el código) | Resuelta en el v5 (nota en 1.6.1). La Ficha ya fue entregada |
| I2 | Checklist | Interpretación con 29/31 y 38/40 | Resuelta: 25/31, nivel amarillo |
| I3 | v5, sección 3 | Puntaje 38/40 | Resuelta: 25/31 |
| I4 | v5 | C1 fija y sin conteo de eventos | Resuelta: 5.3.3, 5.3.4, 6.2 y 6.3 |
| I5 | v5 y Checklist | Cronograma de 6 semanas frente al plan de 3 semanas | Se mantiene a propósito; aquí se documentará el cronograma planificado frente al real |
| I6 | v5, Checklist y Canvas | "Colab solo con autorización escrita" y autorización pendiente | **Resuelta (01-oct-2026):** LEMAS autorizó el tratamiento y el uso de Colab. Falta actualizar el texto en los documentos (Canvas, Checklist H1/H6 y v5 5.6, 5.7, 8.3, 8.4 y 15) |
| I7 | Proyecto | Canvas ausente | Resuelta: el Canvas volvió a subirse |
| I8 | Canvas | Declara "cumple con todos los criterios SMART" junto a 25/31 | Pendiente |
| I9 | v5 y Canvas | Algunas secciones aún citan t0, H y k como pendientes | Pendiente (menor) |
| I10 | v5, sección 6.3 | Actualizar la tabla del v5 con las cifras reales de `docs/analisis_datos.md` (sección 3) y la decisión de C1 | Pendiente: lo hace el equipo en el documento |
