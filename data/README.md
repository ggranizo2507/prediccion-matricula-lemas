# Datos

## Carpetas
| Carpeta | Contenido | ¿Se publica? |
|---|---|---|
| `raw/` | Base seudonimizada de LEMAS (`base_seud.csv`) | **No** (bloqueada por `.gitignore`) |
| `processed/` | Tablas de modelado derivadas de la base real | **No** |
| `synthetic/` | `base_sintetica.csv`: base artificial con la misma estructura | Sí |

## Estructura de origen
LEMAS entrega un Excel con **una hoja por ciclo lectivo** y una fila por estudiante matriculado en ese ciclo. Cada fila reúne:
- el pago que confirmó ese ciclo;
- el desempeño del ciclo (notas y atrasos en pensiones);
- la reserva para el ciclo siguiente.

## Flujo de preparación (dentro de LEMAS)
1. `tools/seudonimizar.py` (o el notebook `00a`) une las hojas y deriva `anio_ingreso` de los dos primeros dígitos del código interno. Luego reemplaza la **cédula del estudiante** por `id_seudonimo` y la cédula del representante por `id_familia_seudonimo` (HMAC-SHA256 con clave custodiada). Por último, elimina el código, los nombres, las cédulas y las columnas internas (`Orden`, `saldo`, `deuda`, `statusp`) y genera un acta con la huella SHA-256 del archivo.
   - Se enlaza por cédula porque el código interno puede cambiar si el estudiante reingresa o se cambia de sede. Enlazar por código haría aparecer como "no matriculado" a quien sí se matriculó.
2. `notebooks/00b_perfil_datos.ipynb` produce `perfil_lemas.json`, que contiene solo agregados y suprime las celdas con menos de 5 casos.
3. `src/synthetic.py --perfil perfil_lemas.json` calibra la base sintética con esos totales.

## Diccionario (base seudonimizada)
| Columna | Descripción | Uso |
|---|---|---|
| `hoja` | Ciclo lectivo de origen de la fila | Trazabilidad |
| `anoa` | Año de inicio del ciclo al que pertenece la fila (2021 = ciclo 2021–2022) | Cohorte |
| `anos` | Año de inicio del ciclo siguiente (2022 = ciclo 2022–2023) | Referencia |
| `Sede` | Mucho Lote 1 / Mucho Lote 2 | Predictor; k por sede |
| `Nivel` | Curso + paralelo + subnivel (p. ej. "Inicial 1 A - Inicial") | Se separa en curso y subnivel; excluye 3.º BGU |
| `Paralelo` | Letra del paralelo | Solo para separar `Nivel` |
| `P.Académico` | Promedio final del año (0–10) | Predictor |
| `P.Conducta` | Comportamiento del año en letras A–E. 2021 y 2022 se convierten a letras con la regla institucional antes de la extracción | Predictor ordinal (A = 5 … E = 1) |
| `fecha_pago` | Fecha del pago de la matrícula del ciclo `anoa`. Los antiguos pagan desde el 20 de febrero; los nuevos, antes | Etiqueta (en la hoja siguiente) y puntualidad del pago anterior (en la hoja de origen) |
| `Reserva` | SI / NO / NO HIZO: la familia desea continuar | Filtro |
| `RColegio` | Respuesta del colegio a la reserva. El texto varía por año y se normaliza a: aprobada, aprobada_extraordinaria, pendiente (en revisión o en proceso), sin_reserva (NO HIZO o vacío) | Filtro (no predictor) |
| `Fecha Reserva` | Fecha y hora del formulario de reserva | Auditoría: se excluyen las reservas posteriores a t0 |
| `Tiempo` | ORDINARIA / EXTRAORDINARIA | Predictor |
| `beca` | "SI" si tiene beca en `anoa`; vacío = sin beca (0) | Predictor y atributo de equidad |
| `# meses caído` | Pensiones del ciclo pagadas después de la fecha tope de su mes, calculadas desde el registro de pagos (recomendado: solo mayo a enero) | Predictor |
| `anio_ingreso` | Año de ingreso (2 primeros dígitos del código) | Años de permanencia |
| `id_seudonimo` | Seudónimo de la cédula del estudiante | Enlace entre ciclos |
| `id_familia_seudonimo` | Seudónimo del representante | Unidad de contacto; hermanos |

## Reglas del estudio
- **t0 = 20 de febrero** y **H = 30 de abril** del año de destino (`config.yaml`).
- **Elegibles:** reserva aprobada (ordinaria o extraordinaria), hecha antes de t0; curso distinto de 3.º de Bachillerato.
- **Estudiante nuevo en `anoa`:** no aparece en la hoja del año anterior. En la primera hoja (2021) se usa el pago de matrícula antes del 20 de febrero o un código del mismo año.
- **Etiqueta `y_no_matricula`:** 1 si el estudiante no aparece en la hoja siguiente con pago entre t0 y H. Equivale a `1 − matricula_efectiva` del documento v5.
- **C1 condicional:** se usa en el entrenamiento solo si supera la auditoría (eventos suficientes y sin pérdida de Precision@k en C4 frente a entrenar con C2–C3).
- **Casos que se reportan aparte:** sin reserva, reservas pendientes, pagos antes de t0 (ya confirmados al corte), pagos después de H (matrícula tardía) y **matriculados sin reserva aprobada** (por ejemplo, con autorización del director). Estos últimos quedan fuera de la población del modelo.

## Limitaciones conocidas
- No hay fecha de aprobación de la reserva. Se usa el estado actual, y las aprobaciones excepcionales posteriores a enero pueden quedar incluidas. Por eso se hace un análisis de sensibilidad solo con "Aprobar".
- `# meses caído` puede incluir la pensión de febrero, cuyo vencimiento es posterior a t0.
- La aprobación de reservas depende también de factores institucionales que no están en los datos.
- La unidad de contacto es el representante: dos hermanos con distinto representante cuentan como dos contactos.

## Base sintética
`base_sintetica.csv` tiene la columna `origen_datos = SINTETICO`. Para que la auditoría de comparabilidad tenga algo que detectar, C1 lleva un aumento artificial de atrasos en pensiones (`sintetico.desplazamiento_c1`). Sus relaciones entre variables son supuestos del generador; **las métricas obtenidas con ella no describen a LEMAS**.
