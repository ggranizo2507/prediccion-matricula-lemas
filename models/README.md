# Modelos

| Archivo | Descripción | ¿Se publica? |
|---|---|---|
| `sistema_sintetica.joblib` / `.json` | Sistema completo generado por el cuaderno `03_modelado` con **datos sintéticos**: modelo, calibración, k por sede, hiperparámetros y métricas de C4. El `.json` guarda los metadatos y la huella SHA-256 | Sí |
| `sistema_real.joblib` / `.json` | El mismo sistema entrenado con **datos reales** de LEMAS (Fase 2, congelado antes de evaluar C5) | **No** (`.gitignore` bloquea `models/*_real*`) |

**Uso en la aplicación:**
- **Modo demo:** la app reentrena el sistema con la base sintética al iniciar. Usa el mismo protocolo (C2+C3, calibración en C4) y los hiperparámetros elegidos por Optuna. Así no depende de archivos binarios ni de versiones de librerías.
- **Modo institucional:** si `models/sistema_real.joblib` existe en el computador de LEMAS, la app lo usa. Si no, reentrena con la base cargada.

Un modelo entrenado con datos reales puede memorizar casos individuales; por eso nunca se publica. La priorización final usa la **regla D2**, que no requiere modelo. El modelo calibrado aporta las probabilidades y la proyección.
