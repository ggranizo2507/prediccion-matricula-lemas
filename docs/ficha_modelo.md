# Ficha del modelo

Resumen de una página del sistema de priorización, con el formato de las fichas de modelo (*model cards*) de Mitchell et al. (2019). Sirve para que cualquier persona sepa para qué es, qué tan bien funciona, con quién funciona peor y cuándo no debe usarse. El detalle está en [modelado.md](modelado.md) y en [consideraciones_eticas.md](consideraciones_eticas.md).

## 1. Datos del sistema

| | |
|---|---|
| Nombre | Priorización de contactos para la continuidad de matrícula · Unidad Educativa LEMAS |
| Versión | 1.0 (sistema congelado el 01-oct-2026; huella SHA-256 `ab864636…1d69d7`, completa en `results/metrics/resultados_finales_real.json`) |
| Autores | Guillermo Granizo y José Ulloa · Maestría en Inteligencia Artificial, UEES |
| Tipo | **Regla de puntaje D2** para ordenar familias, más una regresión logística calibrada que entrega probabilidades y la proyección. El modelo no interviene en el orden |
| Regla D2 | 100 puntos por pago tardío de la matrícula anterior + 20 por reserva extraordinaria + 1 por cada pensión atrasada |
| Modelo de apoyo | Logística híbrida (señales de D2 y variables académicas), calibrada con el método de Platt. scikit-learn 1.6 o superior |
| Licencia y código | Repositorio público del proyecto; ver `LICENSE` |
| Contacto | A través del repositorio de GitHub |

## 2. Uso previsto

- **Para qué:** ordenar, el 20 de febrero de cada año, a qué familias con reserva aprobada conviene llamar primero para ofrecer apoyo antes del 30 de abril, y proyectar la matrícula por sede y subnivel.
- **Quién lo usa:** Secretaría y Admisiones de LEMAS, con el custodio de datos. Dirección revisa los resultados.
- **Cómo:** la lista es un apoyo. Una persona decide a quién llamar y qué ofrecer.
- **Seguimiento (D51):** la aplicación también lista, a una fecha de corte posterior, a las familias que siguen sin pagar. Ese listado no aplica k ni usa el modelo: entran todas las pendientes, y la regla solo da el orden de presentación. No se ha validado como estrategia.

**Usos fuera de alcance**
- Decidir o condicionar cupos, reservas, becas o servicios.
- Cobranza o presión sobre las familias.
- Estudiantes nuevos, reservas pendientes o abandono durante el año lectivo.
- Otros colegios u otros procesos sin volver a validar con sus propios datos.
- Evaluar el desempeño del personal.

## 3. Factores

- **Grupos evaluados:** sede (Mucho Lote 1 y 2), beca, subnivel y representantes con cédula genérica.
- **Variables que usa la regla:** puntualidad del pago de la matrícula anterior, tipo de reserva y pensiones atrasadas.
- **Variables que nunca se usan:** nacionalidad, datos de salud, motivos del DECE, texto libre, nombres y cédulas.

## 4. Métricas

- **Lift@k por familia** (principal): cuántas veces más casos encuentra la lista que una selección al azar del mismo tamaño.
- **Precision@k y Recall@k** por familia, con k igual a la capacidad de contacto de cada sede (118 y 47).
- **Brier** para las probabilidades y **MAPE** para la proyección por sede y subnivel.
- Intervalos de confianza del 95 % con 2.000 réplicas bootstrap por representante.

## 5. Datos

| | |
|---|---|
| Origen | Registros administrativos de LEMAS, con autorización institucional. 9.031 registros de seis ciclos, 2.733 estudiantes y 2.017 familias |
| Evento | No tener la matrícula pagada al 30 de abril, entre estudiantes con reserva aprobada al 20 de febrero. Ocurre en el 6 a 11 % de los casos según el ciclo |
| Entrenamiento | Cohortes C2 y C3 (2.541 estudiantes, 193 eventos). C1 se excluyó por no ser comparable |
| Selección y calibración | Cohorte C4 (1.374 estudiantes, 122 eventos por estudiante) |
| Prueba | Cohorte C5, evaluada una sola vez con el sistema congelado. Las métricas de la lista se calculan por representante: 1.093 representantes, 74 eventos |
| Preparación | Seudonimización HMAC-SHA256 antes de cualquier análisis; variables conocidas al 20 de febrero; guardas automáticas contra fuga de información |
| Publicación | Solo datos sintéticos y resultados agregados. Las celdas con menos de 5 casos no se muestran |

## 6. Resultados en la prueba final (C5)

| Sistema | Precision@k | Lift@k [IC 95 %] | Recall@k |
|---|---|---|---|
| **Regla D2** | **0,133** | **1,97** [1,24; 2,56] | **0,30** |
| Regla D (más atrasos primero) | 0,115 | 1,70 [1,03; 2,30] | 0,26 |
| Logística híbrida calibrada | 0,067 | 0,98 [0,47; 1,52] | 0,15 |
| Selección al azar | 0,073 | 1,08 | 0,16 |

Llamando al 15 % de las familias se llega al 30 % de las que no pagan la matrícula en plazo. Los empates dentro de un mismo puntaje se resuelven al azar con semilla fija, igual en la prueba y en la aplicación. **Los modelos de aprendizaje automático no superaron a la regla.** Las probabilidades individuales empatan con la tasa histórica (Brier 0,0648 frente a 0,0647) y la proyección tiene un MAPE de 2,8 %, igual que la tasa histórica.

### Resultados por grupo (regla D2, C5)

| Grupo | Familias | Eventos | Precision@k | Recall@k |
|---|---|---|---|---|
| Mucho Lote 1 | 640 | 44 | 0,12 | 0,32 |
| Mucho Lote 2 | 453 | 30 | 0,17 | 0,27 |
| Sin beca | 930 | 63 | 0,14 | 0,32 |
| Con beca | 163 | 11 | 0,12 | 0,18 |
| Educación General Básica | 743 | 55 | 0,12 | 0,27 |
| Inicial | 115 | oculto | — | — |
| Preparatoria | 113 | 12 | 0,38 | 0,42 |
| Bachillerato | 122 | <5 | — | — |

La celda de Inicial se oculta para que la de Bachillerato no pueda deducirse por diferencia.

## 7. Consideraciones éticas

- Trata datos de menores de edad, que la ley ecuatoriana considera de categoría especial, y de sus representantes.
- Las señales de pago reflejan la situación económica de la familia: la lista solo puede usarse para ofrecer apoyo.
- Detecta menos casos entre familias becadas (0,18 frente a 0,32 de Recall@k), con solo 11 eventos.
- La decisión es siempre de una persona y cada familia de la lista lleva su motivo.
- Los datos con nombres y la clave no salen de LEMAS. La base seudonimizada se analizó en Google Colab con autorización de la institución. La aplicación pública solo acepta archivos marcados como sintéticos.

## 8. Advertencias y recomendaciones

- La lista no alcanza a cerca del 70 % de las familias que no pagan la matrícula en plazo. Tenía más cupos (165) que casos (74), así que es un límite de señal y no de capacidad.
- La regla ordena mejor que el azar solo al inicio de la campaña. Desde la cuarta semana no supera a elegir al azar entre las familias que siguen sin pagar ([alcance_lista.md](alcance_lista.md)).
- El Lift depende de la cohorte (1,38 en C2, 1,49 en C3, 1,93 en C4 y 1,97 en C5) y del sorteo entre familias empatadas (en C4, de 1,53 a 1,99; media 1,75).
- En C2 a C4, el 86 % de los casos son familias que no registran ningún pago; el 5 % paga todo después del 30 de abril y el 9 % paga por unos estudiantes y no por otros. La regla encuentra al 24 % de las primeras y al 43 % del resto: detecta mejor el retraso que la salida.
- La regla refleja las políticas de cobro y de reservas vigentes entre 2022 y 2026. Si cambian, hay que revalidarla antes de usarla.
- Con unos 200 eventos de entrenamiento los resultados por grupo son inciertos.
- No se ha medido si la llamada cambia la decisión de la familia.
- Revalidar cada mayo con la cohorte que cierra. Si el Lift@k baja de 1,20, revisar la regla; si no supera al azar, suspender su uso.
- Antes de un uso operativo, LEMAS debe informar a las familias, confirmar la base legal para datos de menores y completar los pendientes de cumplimiento descritos en [consideraciones_eticas.md](consideraciones_eticas.md).
