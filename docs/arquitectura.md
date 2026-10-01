# Arquitectura del sistema

Este documento describe cómo está construido el sistema: el flujo de datos, los componentes de código, la solución elegida, el diseño de la aplicación en dos modos y los controles de privacidad. Las decisiones citadas como **Dnn** están registradas en [`planificacion.md`](planificacion.md).

## 1. Visión general

El sistema responde a una pregunta operativa. Al **20 de febrero** (t0), entre las familias con reserva aprobada, ¿a quiénes conviene contactar primero porque podrían **no pagar la matrícula** hasta el **30 de abril** (H)?

```mermaid
flowchart LR
    A[Excel institucional<br/>una hoja por ciclo] -->|00a · seudonimización<br/>HMAC-SHA256 + clave del custodio| B[base_seud.csv<br/>sin cédulas ni nombres]
    B --> C[Limpieza y reglas del estudio<br/>src/data_processing.py]
    C --> D[Cohortes C1–C5<br/>etiqueta y_no_matricula]
    D --> E[Auditoría<br/>eventos, comparabilidad C1]
    E --> F[Modelado y selección<br/>src/modeling.py]
    F --> G[Prueba única C5<br/>IC bootstrap, equidad]
    G --> H[Solución final<br/>regla D2 + modelo calibrado]
    H --> I[Aplicación Streamlit<br/>src/inferencia.py + app/app.py]
```

## 2. Componentes de código

| Módulo | Responsabilidad |
|---|---|
| `config.yaml` | Todas las reglas del estudio: cohortes, t0 y H, filtros de elegibilidad, alias de columnas, capacidad k, privacidad y figuras. El código no tiene fechas ni umbrales escritos a mano |
| `tools/seudonimizar.py` | Seudonimización con HMAC-SHA256 (cédula del estudiante y del representante), derivación del año de ingreso, acta con huella SHA-256 y reidentificación por el custodio |
| `src/data_processing.py` | Limpieza, normalización (curso, estados de reserva, alias), representantes atípicos, predictores conocidos en t0, cohortes, etiqueta y guardas anti-fuga |
| `src/auditoria.py` | Conteo de eventos, EPV, diferencias estandarizadas, decisión sobre C1, tabla 6.3 del v5 y sensibilidad |
| `src/evaluate.py` | Consolidación por representante, k por sede y Precision/Recall/Lift@k familiar |
| `src/modeling.py` | Candidatos, optimización con Optuna, selección en C4, calibración, congelamiento, bootstrap, líneas base R/B0/B1, equidad y proyección |
| `src/inferencia.py` | Lógica de la aplicación (validación, población del ciclo, puntuación, lista, proyección y formulario), separada de Streamlit para poder probarla |
| `src/synthetic.py` | Generador de datos sintéticos con la estructura real, calibrado con totales agregados |
| `app/app.py` | Interfaz Streamlit |
| `notebooks/` | Flujo reproducible en Colab: 00a → 00b → 01 → 02 → 03 |
| `tests/` | 73 pruebas: reglas del estudio, métricas, modelado, protocolo (C5 nunca se usa al ajustar) e interfaz |

## 3. Solución elegida

### 3.1 Protocolo temporal
| Rol | Cohorte (ciclo de origen → destino) |
|---|---|
| Entrenamiento | C2 (2022→2023) + C3 (2023→2024). C1 excluida por la auditoría (D14, decisión del 01-oct) |
| Optimización interna | C2 → C3 |
| Selección y calibración | C4 (2024→2025) |
| Prueba final, una sola vez | C5 (2025→2026, matrícula 2026–2027) |

### 3.2 Candidatos evaluados
| Candidato | Tipo | Lift@k en C4 | Resultado |
|---|---|---|---|
| **D2 · señales administrativas** | Regla: pago anterior tardío → reserva extraordinaria → atrasos | **1,93** | **Elegido para priorizar (D40)** |
| D · más atrasos primero | Regla | 1,86 | Referencia |
| Logística híbrida | Regresión logística con señales de D2 + variables académicas | 1,53 | Se usa para probabilidades y proyección |
| Regresión logística regularizada | Elastic-net | 1,40 | Descartada |
| Gradient boosting | HistGradientBoosting, monotonía en atrasos | 1,06 | Descartada (sobreajuste) |

### 3.3 Arquitectura de la solución final
1. **Priorización:** regla **D2**, transparente y validada en C5 (Lift@k = 1,97 [1,24; 2,56]). Cada familia ocupa un solo cupo de contacto. El desempate dentro del mismo puntaje D2 se resuelve con la probabilidad del modelo.
2. **Probabilidad individual:** logística híbrida calibrada con Platt en C4. Está bien calibrada, pero no mejora a B1 (Brier 0,0648 frente a 0,0647), por eso la interfaz la presenta junto a la tasa histórica.
3. **Proyección por sede y subnivel:** suma de probabilidades de matrícula, comparada siempre con B1 (MAPE de 2,8 % en ambos casos).
4. **Capacidad:** k = 2 × el promedio histórico de familias con no matrícula (D32): 118 en Mucho Lote 1 y 47 en Mucho Lote 2.

## 4. Aplicación en dos modos (D42)

Diseño aprobado el 01-oct-2026: **los datos reales nunca llegan a un servidor público.**

```mermaid
flowchart TB
    subgraph Publico["Modo demo · Streamlit Community Cloud (público)"]
        S[base_sintetica.csv<br/>origen_datos = SINTETICO] --> APPD[app/app.py<br/>LEMAS_MODO no definido]
        APPD --> RD[Lista, proyección y formulario<br/>con datos ficticios]
    end
    subgraph LEMAS["Modo institucional · equipo de LEMAS (localhost)"]
        X[Excel del ciclo actual + anterior] -->|00a con la misma clave| BS[base_seud.csv]
        BS --> APPI[app/app.py<br/>LEMAS_MODO=institucional]
        M[models/sistema_real.joblib<br/>sistema congelado, opcional] --> APPI
        APPI --> L[Lista por seudónimo<br/>descarga CSV]
        L -->|tools/seudonimizar.py reidentificar<br/>solo el custodio| N[Lista con nombres<br/>uso interno de Secretaría]
    end
```

| Aspecto | Modo demo | Modo institucional |
|---|---|---|
| Dónde corre | Streamlit Community Cloud | Un computador de LEMAS (`localhost`) |
| Cómo se activa | Por defecto | Variable de entorno `LEMAS_MODO=institucional` |
| Datos aceptados | Solo sintéticos (`origen_datos = SINTETICO`) | `base_seud.csv` seudonimizado |
| Sistema de predicción | Se reentrena con la base sintética (mismo protocolo y mismos hiperparámetros) | `models/sistema_real.joblib` congelado en la Fase 2; si no está, se reentrena con la base cargada |
| Salida | Lista ficticia | Lista por seudónimo; el custodio reidentifica |

**Controles implementados en `src/inferencia.py`:**
- Rechaza cualquier archivo con columnas de identificadores directos (cédula, nombres, código interno, teléfono, correo, dirección), en **ambos** modos.
- En modo demo rechaza todo archivo que no sea sintético.
- Procesa en memoria: no escribe en disco ni envía datos a terceros. La caché de Streamlit vive solo durante la sesión.
- Muestra mensajes de error en lenguaje simple, sin detalles técnicos.

## 5. Ciclo operativo anual (modo institucional)

| Fecha | Paso | Responsable |
|---|---|---|
| Septiembre–enero | Reservas y su aprobación | Secretaría |
| Hasta el 19 de febrero | Exportar el Excel (ciclo actual + anterior) y ejecutar `00a` con la clave | Responsable de datos |
| 20 de febrero (t0) | Ejecutar la app en modo institucional y descargar la lista por sede | Admisiones |
| 20 de febrero | Reidentificar la lista con `tools/seudonimizar.py reidentificar` | Custodio |
| 20-feb a 30-abr | Contacto de apoyo (planes de pago, información, inquietudes) | Secretaría |
| Mayo | Comparar la lista con las matrículas reales y actualizar el historial | Datos + Dirección |

## 6. Reproducibilidad y calidad
- **Semilla única** (42) en datos sintéticos, Optuna, bootstrap y desempates.
- **Configuración central** en `config.yaml` y registro de decisiones D01–D43.
- **Versiones exactas** en `requirements-lock.txt` y en `app/requirements.txt`.
- **Integración continua** (GitHub Actions): ruff (PEP 8) y pytest en cada push.
- **Sistema congelado** con huella SHA-256 registrada antes de abrir C5.
- **Cuadernos listos para Colab**, que se pueden ejecutar de punta a punta con la base sintética.

## 7. Tecnologías
Python 3.11+, pandas, NumPy, scikit-learn, Optuna, SHAP, Matplotlib/Seaborn, Plotly, Streamlit, pytest, ruff y GitHub Actions.
