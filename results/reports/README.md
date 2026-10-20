# Reportes

**Reportes generados en esta carpeta** (desde los agregados de `results/metrics`; se regeneran con `python tools/generar_resumen.py --fuente real` o `--fuente sintetica`):

| Reporte | Contenido |
|---|---|
| [`resumen_resultados_real.md`](resumen_resultados_real.md) | Selección en C4, prueba final en C5 con IC 95 %, calibración, proyección, hiperparámetros del sistema congelado y comprobaciones de la revisión final (D59) |
| [`resumen_resultados_sintetica.md`](resumen_resultados_sintetica.md) | Lo mismo con la base sintética: sirve para comprobar el código, no describe a LEMAS |

**Reportes que se guardan junto a la documentación que los explica**, en `docs/`:

| Reporte | Contenido |
|---|---|
| [`docs/diagnostic_report.pdf`](../../docs/diagnostic_report.pdf) | Actividad de la semana 3: diagnóstico de sobreajuste y subajuste, curvas de aprendizaje y estrategias de mejora. Se regenera con `python tools/generar_reporte_diagnostico.py --fuente real` |
| [`docs/Workshop_Impacto_Social_y_Responsabilidad_LEMAS.pdf`](../../docs/Workshop_Impacto_Social_y_Responsabilidad_LEMAS.pdf) | Workshop de la semana 4: impacto social y responsabilidad |
| [`docs/Documento_Tecnico_Prediccion_Matricula_v6.docx`](../../docs/Documento_Tecnico_Prediccion_Matricula_v6.docx) | Documento técnico integral del proyecto |

Las tablas de métricas están en [`results/metrics/`](../metrics) y las figuras en [`results/figures/`](../figures). Todo es agregado: no hay datos individuales.
