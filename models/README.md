# Modelos

| Archivo | Descripción | ¿Se publica? |
|---|---|---|
| `sistema_sintetica.joblib` / `.json` | Sistema completo generado por el cuaderno `03_modelado` con **datos sintéticos**: modelo, calibración, k por sede, hiperparámetros y métricas de C4. El `.json` guarda los metadatos y la huella SHA-256 | Sí |
| `sistema_real.joblib` / `.json` | El mismo sistema entrenado con **datos reales** de LEMAS (Fase 2, congelado antes de evaluar C5) | **No** (`.gitignore` bloquea `models/*_real*`) |

**Uso en la aplicación:**
- **Modo demo:** la app reentrena el sistema con la base sintética al iniciar. Usa el mismo protocolo (C2+C3, calibración en C4) y los hiperparámetros elegidos por Optuna. Así no depende de archivos binarios ni de versiones de librerías.
- **Modo institucional:** si `models/sistema_real.joblib` existe en el computador de LEMAS, la app lo usa. Si no, reentrena con la base cargada.

Un modelo entrenado con datos reales puede memorizar casos individuales; por eso nunca se publica. La priorización final usa la **regla D2**, que no requiere modelo. El modelo calibrado aporta las probabilidades y la proyección.

## Cómo cargar el sistema sintético

```python
import joblib
from src.data_processing import construir_matriz_x

sistema = joblib.load("models/sistema_sintetica.joblib")   # diccionario
probabilidades = sistema["calibrado"].predict_proba(construir_matriz_x(datos))[:, 1]
```

`datos` es una tabla con la estructura de `construir_dataset` (ver `data/README.md`). El archivo es un *pickle* de joblib: cárguelo solo si confía en su origen, y con las versiones de `requirements.txt` (scikit-learn 1.8.0), con las que se serializó.

**Campos del `.json`:** `fuente`, `fecha`, `tipo` y `nombre` del modelo, `hiperparametros`, `cohortes_entrenamiento`, `incluir_C1`, `k_por_sede`, `priorizacion` (el sistema que ordena la lista), `modelo_supera_reglas`, `metricas_C4`, `tasa_historica_no_matricula` y `sha256` (huella del `.joblib`, para comprobar que no cambió).

> Con la base sintética el modelo supera a las reglas (`modelo_supera_reglas = true`); con los datos reales no. Es una de las diferencias entre la base sintética y LEMAS que se explican en el README (sección *Instalación y uso*).

