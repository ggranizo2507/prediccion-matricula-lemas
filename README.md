# Predicción de matrícula y continuidad estudiantil

![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![License](https://img.shields.io/badge/licencia-MIT-green)
![Tests](https://img.shields.io/badge/tests-pytest-orange)
![Estado](https://img.shields.io/badge/estado-fase%203-blue)
![Streamlit](https://img.shields.io/badge/app-Streamlit-FF4B4B)

Sistema de IA que identifica, al **20 de febrero** de cada año, a las familias con reserva aprobada que podrían **no concretar la matrícula** antes del **30 de abril**. Entrega a Secretaría y Admisiones de la Unidad Educativa LEMAS una lista priorizada de contactos ajustada a su capacidad real y una proyección de matrícula por sede y subnivel. En la prueba final con datos reales, la priorización encontró **casi el doble** de familias que no se matricularon que una selección al azar (Lift@k = 1,97, IC 95 % [1,24; 2,56]).

🔗 **Aplicación (demo con datos sintéticos):** [continuidad-matricula-lemas.streamlit.app](https://continuidad-matricula-lemas.streamlit.app/)

[![Abrir en Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://continuidad-matricula-lemas.streamlit.app/)

> Proyecto integrador · Maestría en Inteligencia Artificial · Universidad de Especialidades Espíritu Santo (UEES), 2026.

## Tabla de contenidos
1. [Descripción del problema](#descripción-del-problema)
2. [Dataset](#dataset)
3. [Metodología](#metodología)
4. [Resultados](#resultados)
5. [Instalación y uso](#instalación-y-uso)
6. [Interfaz de usuario](#interfaz-de-usuario)
7. [Estructura del proyecto](#estructura-del-proyecto)
8. [Consideraciones éticas](#consideraciones-éticas)
9. [Autores y contribuciones](#autores-y-contribuciones)
10. [Licencia](#licencia)
11. [Agradecimientos y referencias](#agradecimientos-y-referencias)
12. [Videos](#videos)

## Descripción del problema
Cada año, entre septiembre y noviembre, las familias de LEMAS reservan un cupo para el ciclo siguiente. No todas las reservas aprobadas terminan en matrícula pagada. Cuando una familia no continúa, la institución se entera tarde, sin tiempo para ofrecer apoyo ni para planificar cupos, docentes y paralelos.

**Qué resuelve.** El modelo ordena a los estudiantes elegibles por su riesgo de no matricularse y consolida el resultado por representante. Así, las 10 personas de Secretaría y Admisiones de las dos sedes concentran su tiempo en las familias que más lo necesitan.

**Por qué importa.** Contactar a tiempo permite ofrecer planes de pago, información de becas o atención a inquietudes, y proyectar la matrícula con anticipación.

**Usuarios objetivo.** Secretaría, Admisiones y Dirección de LEMAS.

## Dataset
| Aspecto | Detalle |
|---|---|
| Fuente | Registros institucionales de LEMAS, ciclos 2021–2022 a 2026–2027 |
| Unidad | Estudiante antiguo con reserva aprobada para el ciclo siguiente |
| Cohortes | C1–C3 entrenamiento (C1 condicionada a la auditoría de comparabilidad), C4 selección, C5 prueba final evaluada una sola vez |
| Variables | Sede, subnivel, curso, años de permanencia, promedio, conducta, beca, pensiones pagadas tarde, tipo de reserva, hermanos en LEMAS, puntualidad de la matrícula anterior |
| Etiqueta | 1 = no pagó matrícula entre el 20-feb y el 30-abr del año de destino |

**Privacidad.** Los datos reales contienen información de menores y **no se publican**. Se seudonimizan con HMAC-SHA256 y clave custodiada por LEMAS (`tools/seudonimizar.py`), y se procesan solo en el entorno autorizado. Este repositorio incluye un **dataset sintético** (`data/synthetic/`) con la misma estructura, calibrado únicamente con totales agregados. Sirve para ejecutar el código, **no** para sacar conclusiones sobre LEMAS. Detalle en [`data/README.md`](data/README.md).

## Metodología
- **Enfoque:** clasificación binaria supervisada con validación temporal por cohortes.
- **Candidatos:** regresión logística elastic-net, gradient boosting (HistGradientBoosting con monotonía en atrasos) y una logística híbrida, comparados contra reglas sin IA (D: más atrasos primero; D2: señales administrativas) y las líneas base del v5 (A, R, B0, B1).
- **Preprocesamiento:** limpieza, derivación de variables conocidas en t0 y guardas automáticas anti-fuga (`src/data_processing.py`).
- **Auditoría de datos:** conteo de eventos de no matrícula por cohorte y comparabilidad de C1. Se entrena con y sin C1, se evalúa en C4 y C1 se incluye solo si no degrada la priorización (`src/auditoria.py`).
- **Optimización:** Optuna (TPE, 60 trials por modelo) con validación interna temporal C2 → C3; selección en C4; calibración de Platt; sistema congelado (SHA-256) y prueba única en C5. Ver [`docs/optimizacion.md`](docs/optimizacion.md).
- **Métricas:** Precision@k y Lift@k por sede (métrica principal, con k igual a la capacidad de contacto), Recall@k, PR-AUC, ROC-AUC, Brier, matriz de confusión e intervalos bootstrap por familia.

## Resultados
Prueba final en **C5** (matrícula 2026–2027), evaluada **una sola vez** con el sistema congelado. k = 118 familias en Mucho Lote 1 y 47 en Mucho Lote 2 (≈ 15 % de 1.093 familias). Solo cifras agregadas.

| Sistema | Precision@k | Lift@k [IC 95 %] | Recall@k |
|---|---|---|---|
| **D2 · señales administrativas** (solución elegida) | **0,133** | **1,97 [1,24; 2,56]** | **0,30** |
| D · más atrasos primero | 0,115 | 1,70 [1,03; 2,30] | 0,26 |
| Logística híbrida (mejor modelo de ML en C4) | 0,067 | 0,98 [0,47; 1,52] | 0,15 |
| A · selección al azar | 0,073 | 1,08 | 0,16 |

- **Hallazgo principal:** contactando al 15 % de las familias se llega al **30 %** de las que no se matriculan. La regla D2 (pago anterior tardío → reserva extraordinaria → pensiones pagadas tarde) surgió del análisis de datos y se confirmó fuera de muestra.
- **Los modelos de aprendizaje automático no superaron a la regla** con 193 eventos de entrenamiento: el gradient boosting se sobreajustó y los modelos lineales se quedaron cortos. Es un resultado válido y está documentado.
- **Calibración y proyección:** la logística híbrida calibrada iguala a la tasa histórica (Brier 0,0648 frente a 0,0647; MAPE 2,8 % en ambos).
- **Equidad:** menor detección en familias becadas (recall 0,18 frente a 0,32), que se advierte en la app.

Detalle en [`docs/analisis_datos.md`](docs/analisis_datos.md) y [`docs/modelado.md`](docs/modelado.md).

## Instalación y uso

### Opción A · Google Colab (recomendada para el equipo)
Cada notebook trae una celda **0 · Preparar el entorno**. Esa celda clona el repositorio (o pide subir el `.zip`) e instala solo lo que falte.

| Notebook | Qué hace | Abrir |
|---|---|---|
| `00a_seudonimizacion` | Excel de LEMAS → `base_seud.csv` seudonimizado (solo personal autorizado) | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ggranizo2507/prediccion-matricula-lemas/blob/main/notebooks/00a_seudonimizacion.ipynb) |
| `00b_perfil_datos` | Perfil agregado para calibrar el sintético | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ggranizo2507/prediccion-matricula-lemas/blob/main/notebooks/00b_perfil_datos.ipynb) |
| `01_exploracion` | EDA con 8 figuras a 300 DPI, conteo de eventos por estudiante y representante, y comparabilidad de C1 (SMD) | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ggranizo2507/prediccion-matricula-lemas/blob/main/notebooks/01_exploracion.ipynb) |
| `02_preprocesamiento` | Partición temporal, anti-fuga, transformaciones y decisión de incluir C1 (evaluada en C4) | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ggranizo2507/prediccion-matricula-lemas/blob/main/notebooks/02_preprocesamiento.ipynb) |
| `03_modelado` | Optuna (regresión logística y gradient boosting), selección en C4 frente a las reglas D/D2, calibración, SHAP, congelamiento y prueba final única en C5 con IC bootstrap, equidad y proyección | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ggranizo2507/prediccion-matricula-lemas/blob/main/notebooks/03_modelado.ipynb) |
| `04_optimizacion` | Análisis de la búsqueda con Optuna (180 trials), efecto de hiperparámetros, paso de C3 a C4 y diagnóstico de ajuste. Lee resultados guardados; no reentrena | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ggranizo2507/prediccion-matricula-lemas/blob/main/notebooks/04_optimizacion.ipynb) |
| `05_evaluacion` | Resultados de la prueba única en C5: IC 95 %, Brier frente a R/B0/B1, criterios del Canvas, explicabilidad, equidad y proyección. Lee resultados guardados | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ggranizo2507/prediccion-matricula-lemas/blob/main/notebooks/05_evaluacion.ipynb) |

En los notebooks 01, 02 y 03, el parámetro `FUENTE` elige entre `sintetica` (cualquier persona) y `real` (solo en el entorno autorizado de LEMAS). Los notebooks 04 y 05 leen los **agregados reales ya publicados** en `results/` (autorizados por LEMAS), así que cualquier persona puede ejecutarlos.

### Opción B · Entorno local
```bash
git clone https://github.com/ggranizo2507/prediccion-matricula-lemas.git
cd prediccion-matricula-lemas
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt                     # versiones exactas: requirements-lock.txt

python -m src.synthetic                              # regenera el dataset sintético
python -m src.data_processing                        # construye la tabla de modelado
pytest -q                                            # ejecuta las pruebas
```

## Interfaz de usuario
Aplicación **Streamlit** en español (`app/app.py`), con **dos modos** (decisiones D42 y D45):

| Modo | Dónde | Datos |
|---|---|---|
| **Demo** (por defecto) | Streamlit Community Cloud | Solo **sintéticos**; rechaza cualquier otro archivo |
| **Institucional** | Computador de LEMAS, solo `localhost` (doble clic en `iniciar_lemas.bat`) | El **Excel de LEMAS + la clave del custodio**: se seudonimiza en el propio equipo. También acepta `base_seud.csv`. Nada se guarda |

**Funciones:** botón *Prueba con ejemplo*; carga validada de CSV (rechaza cédulas o nombres); lista de contactos por sede con k editable, motivo de cada prioridad y descarga CSV; proyección por sede y subnivel frente a B1; formulario para evaluar a un estudiante; sección *Acerca de* con métricas, limitaciones y privacidad.

**Solo en modo institucional (D45):** carga del Excel institucional y de la clave, seudonimización en memoria con verificación automática, descarga de `base_seud.csv` y del acta, pestaña **Lista con nombres** para personal autorizado y botón **Borrar datos de la sesión**. Así el personal de LEMAS no necesita Colab ni línea de comandos. La versión pública no tiene ninguna de estas funciones.

```bash
pip install -r app/requirements.txt
streamlit run app/app.py                          # demo
# Solo dentro de LEMAS: doble clic en iniciar_lemas.bat (Windows) o:
bash iniciar_lemas.sh                             # macOS / Linux
python tools/generar_excel_ejemplo.py             # Excel y clave FICTICIOS para practicar
```
Guía completa en [`docs/manual_usuario.md`](docs/manual_usuario.md) y diseño en [`docs/arquitectura.md`](docs/arquitectura.md).

## Estructura del proyecto
| Carpeta | Contenido |
|---|---|
| `data/` | `raw/` y `processed/` (vacías en el repositorio público) y `synthetic/` con la base artificial |
| `notebooks/` | 00a seudonimización, 00b perfil, 01 EDA, 02 preprocesamiento, 03 modelado (entrena, optimiza, calibra y evalúa una vez en C5), 04 optimización y 05 evaluación (análisis de resultados guardados), listos para Colab |
| `src/` | Código modular: `data_processing`, `auditoria`, `evaluate` (métricas por familia), `modeling` (entrenamiento, Optuna, calibración, evaluación), `inferencia` (lógica de la app), `synthetic` y `utils` |
| `tools/` | Seudonimización y perfil agregado (se ejecutan solo en LEMAS) |
| `models/` | Sistema entrenado con datos sintéticos (los reales nunca se publican) |
| `app/` | Aplicación Streamlit, `requirements.txt` propio y recursos |
| `tests/` | 102 pruebas: datos, métricas, modelado, interfaz y modo institucional |
| `results/` | Figuras (300 DPI) y métricas **agregadas**, sintéticas y reales autorizadas; sin datos individuales |
| `docs/` | Planificación (con registro de decisiones), datos, arquitectura, optimización, ética y manual de usuario |
| `config.yaml` | Todas las reglas del estudio: cohortes, t0, H, filtros y capacidad |

### Documentación
| Documento | Contenido |
|---|---|
| [`docs/planificacion.md`](docs/planificacion.md) | Problema, objetivos, alcance, cronograma planificado frente a real, riesgos y registro de decisiones D01–D45 |
| [`docs/analisis_datos.md`](docs/analisis_datos.md) | Análisis exploratorio, calidad de datos, auditoría de cohortes y referencias |
| [`docs/arquitectura.md`](docs/arquitectura.md) | Flujo de datos, componentes, solución elegida y aplicación en dos modos |
| [`docs/optimizacion.md`](docs/optimizacion.md) | Optuna, espacios de búsqueda, resultados y diagnóstico de ajuste |
| [`docs/modelado.md`](docs/modelado.md) | Selección en C4, prueba final en C5, calibración, explicabilidad y equidad |
| [`docs/consideraciones_eticas.md`](docs/consideraciones_eticas.md) | Privacidad, sesgos, impacto social, mitigaciones y limitaciones |
| [`docs/manual_usuario.md`](docs/manual_usuario.md) | Uso de la app y procedimiento anual en LEMAS |
| [`docs/guion_pitch.md`](docs/guion_pitch.md) | Guion cronometrado del pitch (5 min) y plan de grabación |
| [`docs/banco_preguntas.md`](docs/banco_preguntas.md) | 28 preguntas probables de la defensa con sus respuestas |
| [`data/README.md`](data/README.md) · [`models/README.md`](models/README.md) | Diccionario de datos y modelos |

## Consideraciones éticas
El sistema **prioriza contactos de apoyo; no decide admisiones, reservas ni becas**, y la decisión final es siempre humana.
- **Privacidad:** seudonimización HMAC-SHA256 con clave custodiada, celdas menores a 5 suprimidas, app pública solo con datos sintéticos y repositorio sin datos reales.
- **Sesgos:** los atrasos son un proxy socioeconómico; la detección es menor en familias becadas; la cédula genérica de familias extranjeras no se usa como predictor.
- **Honestidad:** se informa que los modelos de ML no superaron a la regla y se reporta la incertidumbre.

Análisis completo en [`docs/consideraciones_eticas.md`](docs/consideraciones_eticas.md).

## Autores y contribuciones
| Integrante | Rol |
|---|---|
| Guillermo Leonidas Granizo Veintimilla | Product Owner, dominio institucional, datos reales y validación con usuarios |
| José Farid Ulloa Manzur | Scrum Master, repositorio, modelado, optimización y aplicación |

## Licencia
Código bajo licencia [MIT](LICENSE). Los datos reales de LEMAS están excluidos.

## Agradecimientos y referencias
A la Unidad Educativa LEMAS por autorizar el uso seudonimizado de sus registros. Las referencias se listan en [`docs/planificacion.md`](docs/planificacion.md).

## Videos
*Se agregan en la Fase 4.*
- Video pitch (5 min): —
- Video de respuestas: —
