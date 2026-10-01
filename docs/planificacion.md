# Planificación del proyecto

> **Estado:** en construcción. La versión completa se redacta en la Fase 3 e incluirá problema y objetivos, relevancia, alcance, cronograma planificado frente a real, recursos y riesgos. Esta versión contiene el **registro de decisiones** y las **inconsistencias pendientes** entre los documentos del proyecto, que se actualizan a medida que avanza el trabajo.

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
| D30 | 30-sep-2026 | Referencias obligatorias en C4: azar (R), más atrasos primero (D), señales administrativas (D2) y regresión logística (B1). Se agrega un IC 95 % por bootstrap a la decisión sobre C1, como dato informativo | Equipo |
| D31 | 30-sep-2026 | Base sintética calibrada con `perfil_lemas.json` (sedes, beca, promedio, conducta, atrasos; ~1500 estudiantes por año; tasa ≈ 8,5 %). Los parámetros agregados están en `data/synthetic/parametros_calibracion.json` | Fase 1 |
| D32 | 01-oct-2026 | k por sede = **2 ×** el promedio histórico de representantes con no matrícula (`capacidad.multiplicador_k`), porque la capacidad de contacto supera con holgura el promedio. Se prioriza el recall | Equipo |
| D33 | 01-oct-2026 | El representante con 39 estudiantes es una **cédula genérica** que se usa para familias extranjeras sin cédula ecuatoriana. Se confirma el tratamiento D29. `representante_atipico` **no** es predictor, porque equivaldría a usar la nacionalidad | Equipo |
| D34 | 01-oct-2026 | La conversión de conducta 2022 a letras es correcta (18 % de B ese año); la variable se mantiene sin ajustes | Equipo |
| D35 | 01-oct-2026 | Se confirma que la columna `Fecha` de 2022–2025 es la fecha en que el padre hace la reserva (= `Fecha Reserva`) | Equipo |

La decisión de C1 con datos reales se guarda en `results/metrics/decision_c1_real.json`, generado por el notebook 02, y se transcribe aquí.

## Estado de las inconsistencias entre documentos (revisión del 28-sep-2026)

| # | Documento | Inconsistencia | Estado |
|---|---|---|---|
| I1 | v5 y Ficha | Convención de la etiqueta (1 = matrícula en documentos; 1 = no matrícula en el código) | Resuelta en el v5 (nota en 1.6.1). La Ficha ya fue entregada |
| I2 | Checklist | Interpretación con 29/31 y 38/40 | Resuelta: 25/31, nivel amarillo |
| I3 | v5, sección 3 | Puntaje 38/40 | Resuelta: 25/31 |
| I4 | v5 | C1 fija y sin conteo de eventos | Resuelta: 5.3.3, 5.3.4, 6.2 y 6.3 |
| I5 | v5 y Checklist | Cronograma de 6 semanas frente al plan de 3 semanas | Se mantiene a propósito; aquí se documentará el cronograma planificado frente al real |
| I6 | v5, Checklist y Canvas | "Colab solo con autorización escrita" y autorización pendiente, aunque ya se trabaja con la extracción seudonimizada | **Pendiente:** registrar la autorización del custodio o limitarse a datos sintéticos |
| I7 | Proyecto | Canvas ausente | Resuelta: el Canvas volvió a subirse |
| I8 | Canvas | Declara "cumple con todos los criterios SMART" junto a 25/31 | Pendiente |
| I9 | v5 y Canvas | Algunas secciones aún citan t0, H y k como pendientes | Pendiente (menor) |
| I10 | v5, sección 6.3 | La tabla del v5 debe actualizarse con las cifras reales cuando se vuelva a ejecutar el cuaderno 02 tras D27–D29 | Pendiente |
