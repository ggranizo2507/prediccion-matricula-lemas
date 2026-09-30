# Predicción de matrícula y continuidad estudiantil

![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![License](https://img.shields.io/badge/licencia-MIT-green)
![Tests](https://img.shields.io/badge/tests-pytest-orange)
![Estado](https://img.shields.io/badge/estado-en%20desarrollo-yellow)

Sistema de aprendizaje automático que estima, al **20 de febrero** de cada año, qué estudiantes con reserva aprobada tienen mayor riesgo de **no concretar su matrícula** antes del **30 de abril**. Entrega a Secretaría y Admisiones de la Unidad Educativa LEMAS una lista priorizada de familias para contactar, ajustada a su capacidad real de atención, y una proyección de matrícula por sede y nivel.

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
- **Modelos:** regresión logística (referencia interpretable), Random Forest y HistGradientBoosting, comparados contra líneas base simples (incluida la regla "más atrasos primero").
- **Preprocesamiento:** limpieza, derivación de variables conocidas en t0 y guardas automáticas anti-fuga (`src/data_processing.py`).
- **Auditoría de datos:** conteo de eventos de no matrícula por cohorte y comparabilidad de C1. Se entrena con y sin C1, se evalúa en C4 y C1 se incluye solo si no degrada la priorización (`src/auditoria.py`).
- **Optimización:** Optuna con validación por ventanas temporales crecientes y seguimiento en MLflow. Ver [`docs/optimizacion.md`](docs/optimizacion.md).
- **Métricas:** Precision@k y Lift@k por sede (métrica principal, con k igual a la capacidad de contacto), Recall@k, PR-AUC, ROC-AUC, Brier, matriz de confusión e intervalos bootstrap por familia.

## Resultados
*En construcción (Fase 2).* Aquí se publicarán las métricas de la prueba final C5, solo en forma agregada.

## Instalación y uso

### Opción A · Google Colab (recomendada para el equipo)
Cada notebook trae una celda **0 · Preparar el entorno**. Esa celda clona el repositorio (o pide subir el `.zip`) e instala solo lo que falte.

| Notebook | Qué hace | Abrir |
|---|---|---|
| `00a_seudonimizacion` | Excel de LEMAS → `base_seud.csv` seudonimizado (solo personal autorizado) | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ggranizo2507/prediccion-matricula-lemas/blob/main/notebooks/00a_seudonimizacion.ipynb) |
| `00b_perfil_datos` | Perfil agregado para calibrar el sintético | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ggranizo2507/prediccion-matricula-lemas/blob/main/notebooks/00b_perfil_datos.ipynb) |
| `01_exploracion` | EDA con 8 figuras a 300 DPI, conteo de eventos por estudiante y representante, y comparabilidad de C1 (SMD) | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ggranizo2507/prediccion-matricula-lemas/blob/main/notebooks/01_exploracion.ipynb) |
| `02_preprocesamiento` | Partición temporal, anti-fuga, transformaciones y decisión de incluir C1 (evaluada en C4) | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ggranizo2507/prediccion-matricula-lemas/blob/main/notebooks/02_preprocesamiento.ipynb) |

En los notebooks 01 y 02, el parámetro `FUENTE` elige entre `sintetica` (cualquier persona) y `real` (solo en el entorno autorizado de LEMAS).

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
*En construcción (Fase 3).* Aplicación Streamlit con evaluación individual, priorización por lote, proyección por sede y nivel, y una sección "Acerca del modelo".

## Estructura del proyecto
| Carpeta | Contenido |
|---|---|
| `data/` | `raw/` y `processed/` (vacías en el repositorio público) y `synthetic/` con la base artificial |
| `notebooks/` | 00a seudonimización, 00b perfil, 01 EDA, 02 preprocesamiento, 03 modelado, 04 optimización, 05 evaluación (listos para Colab) |
| `src/` | Código modular: procesamiento (`data_processing`), auditoría, evaluación (Precision@k familiar y k por sede), generador sintético y utilidades |
| `tools/` | Seudonimización y perfil agregado (se ejecutan solo en LEMAS) |
| `models/` | Modelos entrenados con datos sintéticos |
| `app/` | Aplicación Streamlit |
| `tests/` | Pruebas unitarias |
| `results/` | Figuras, métricas y reportes agregados |
| `docs/` | Planificación (con registro de decisiones), datos, arquitectura, optimización, ética y manual de usuario |
| `config.yaml` | Todas las reglas del estudio: cohortes, t0, H, filtros y capacidad |

## Consideraciones éticas
El sistema **prioriza contactos de apoyo; no decide admisiones, reservas ni becas**. La variable de atrasos en pensiones funciona como proxy socioeconómico: se mide la equidad del modelo según beca y sede, y la lista no debe usarse para presionar a las familias. Análisis completo en [`docs/consideraciones_eticas.md`](docs/consideraciones_eticas.md).

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
