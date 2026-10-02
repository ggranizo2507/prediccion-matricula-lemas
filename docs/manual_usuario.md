# Manual de usuario

Guía para **Secretaría, Admisiones y Dirección** de LEMAS, y para cualquier persona que quiera probar la versión de demostración. No se necesitan conocimientos de programación para usar la aplicación.

## 1. ¿Qué hace la aplicación?
Al **20 de febrero** de cada año, entre los estudiantes con **reserva aprobada**, indica:
1. **A qué familias contactar primero**, por sede, porque podrían no pagar la matrícula hasta el 30 de abril.
2. **Cuántas matrículas se esperan** por sede y subnivel.
3. La **probabilidad estimada** de no matrícula de un estudiante cualquiera (formulario).

> La lista es un **apoyo**. Secretaría decide a quién llamar y cómo. La aplicación no contacta a nadie ni decide sobre cupos, becas o servicios.

## 2. Dos formas de usarla

| | **Demostración (pública)** | **Institucional (LEMAS)** |
|---|---|---|
| Dónde | En el navegador, con el enlace del README | En un computador de LEMAS (doble clic en `iniciar_lemas.bat`) |
| Datos | Sintéticos (ficticios), ya incluidos | El Excel de LEMAS y la clave del custodio |
| Nombres | Nunca | Solo en la pestaña **Lista con nombres**, para personal autorizado |
| Para qué | Conocer la herramienta, el video y la evaluación académica | Uso real cada 20 de febrero |

**Importante:** nunca suba datos reales a la versión pública. La aplicación los rechaza, pero el archivo alcanza a viajar por internet. El Excel y la clave solo se usan en el modo institucional.

## 3. Uso paso a paso (demostración)

1. **Abra la aplicación:** [continuidad-matricula-lemas.streamlit.app](https://continuidad-matricula-lemas.streamlit.app/) (también enlazada en el README). Si estuvo inactiva, Streamlit puede tardar unos segundos en despertarla. Arriba verá un aviso azul: *Modo demostración*.
2. **Cargue datos.** En la barra lateral pulse **▶️ Prueba con ejemplo**. Aparecerá *Datos: Ejemplo sintético*.
3. **Revise los parámetros** en la barra lateral:
   - **Ciclo de origen:** el ciclo cuyas reservas se van a priorizar. Viene elegido el más reciente. Si elige uno anterior, la app avisa que el resultado es **retrospectivo**, porque esos ciclos se usaron para entrenar el sistema.
   - **Familias a contactar (k):** **no cambia al elegir otro ciclo**, porque representa la capacidad de contacto de cada sede y se calcula una sola vez con los ciclos de entrenamiento. Indica cuántas familias puede atender cada sede. El valor sugerido es el aprobado: el doble del promedio histórico de familias que no se matricularon. Puede cambiarlo según el personal disponible.
4. Vaya a la pestaña **📋 Lista de contactos** y pulse **Generar lista**.
   - Las tarjetas muestran elegibles, familias, familias a contactar y cobertura.
   - La tabla muestra, por sede y en orden, cada **familia (seudónimo)**, sus estudiantes, la probabilidad y el **motivo** (por ejemplo, "pagó tarde la matrícula anterior; 4 pensiones pagadas tarde").
   - Pulse **⬇️ Descargar lista (CSV)** para guardarla.
5. Pestaña **📈 Proyección:** matrículas esperadas por sede y subnivel, según el modelo y según la tasa histórica (B1).
6. Pestaña **🧑‍🎓 Evaluar un estudiante:** complete el formulario (sede, subnivel, pago anterior, pensiones pagadas tarde, tipo de reserva, promedio y conducta) y pulse **Estimar**. Obtendrá la prioridad D2 (alta, media o baja), la probabilidad y su comparación con la tasa histórica.
7. Pestaña **ℹ️ Acerca de:** cómo se validó el sistema, sus resultados y sus limitaciones.

## 4. Cómo interpretar los resultados

| Elemento | Significado |
|---|---|
| **Orden de la lista (regla D2)** | Primero quien **pagó tarde la matrícula anterior**, luego quien hizo **reserva extraordinaria** y luego quien tuvo **más pensiones pagadas tarde**. Con datos reales, esta regla encontró casi el **doble** de familias que no se matricularon que una selección al azar |
| **Prob. no matrícula** | Probabilidad calibrada. En promedio coincide con la realidad, pero para una persona concreta **no es más precisa que la tasa histórica**. Úsela como referencia, no como diagnóstico |
| **Prioridad en el formulario** | *Alta:* pagó tarde la matrícula anterior. *Media:* reserva extraordinaria o 3 o más pensiones tarde. *Baja:* sin esas señales |
| **Cobertura** | Porcentaje de familias elegibles que entra en la lista. Con k aprobado es alrededor del 15 % y alcanza cerca del 30 % de los casos de no matrícula |

**Recomendación de equidad:** la regla detecta menos casos entre familias **becadas**. Revise también a las becadas con atrasos aunque no estén en la lista.

## 5. Procedimiento anual en LEMAS (modo institucional)

No se necesita Colab ni escribir comandos. Todo ocurre en un computador de LEMAS.

**Responsables:** responsable de datos (paso 1), Admisiones junto con el custodio (pasos 2–7).

### 5.1 Preparación del equipo (una sola vez)
1. Instale **Python 3.11 o superior** desde python.org y marque la opción *Add python.exe to PATH*.
2. Descargue el repositorio (botón **Code → Download ZIP** en GitHub) y descomprímalo en una carpeta del equipo.
3. Haga doble clic en **`iniciar_lemas.bat`**. La primera vez instala lo necesario (requiere internet y tarda unos minutos). En macOS o Linux use `bash iniciar_lemas.sh`.

### 5.2 Uso cada 20 de febrero
1. **Hasta el 19 de febrero:** exporte el Excel institucional de siempre, con una hoja por ciclo y los encabezados estándar (ver `data/README.md`). Debe incluir al menos los ciclos 2022 a 2025 y el ciclo actual.
2. Haga doble clic en **`iniciar_lemas.bat`**. Se abre el navegador en `http://localhost:8501` con un aviso amarillo de **Modo institucional**. Deje abierta la ventana negra mientras trabaja.
3. En la barra lateral suba dos archivos:
   - **Excel de LEMAS (.xlsx)**.
   - **Clave del custodio (.key)**: el archivo `clave_lemas.key`, **el mismo de siempre**.
4. La aplicación seudonimiza el Excel en el equipo. Abra el recuadro **🔐 Excel seudonimizado en este equipo** y revise:
   - que el número de hojas y de filas sea el esperado;
   - que la **huella de la clave** sea la misma de años anteriores (anótela la primera vez). Si cambió, se usó otra clave;
   - si lo necesita, descargue `base_seud.csv` y el acta de extracción.
5. Elija el ciclo, ajuste k si cambió el personal y pulse **Generar lista** (pestaña *Lista de contactos*).
   - Si en la carpeta `models/` está `sistema_real.joblib` (el sistema validado en la Fase 2, generado por el cuaderno 03), la app lo usa. Si no, entrena uno nuevo con el Excel cargado.
6. Abra la pestaña **🪪 Lista con nombres**, marque **Soy personal autorizado y deseo ver los nombres** y descargue la lista. Muestra el representante, su cédula, sus estudiantes con el curso y el motivo.
   - La columna **Observación** avisa cuando la cédula del representante es compartida (cédula genérica): en ese caso confirme el contacto con los datos del estudiante.
7. Al terminar pulse **🧹 Borrar datos de la sesión**, cierre el navegador y la ventana negra. Guarde la lista con nombres solo en una carpeta autorizada y elimínela al terminar la campaña.

### 5.3 La clave
- LEMAS usa **una sola clave**. Con una clave distinta los seudónimos cambian y las listas anteriores no se pueden cruzar ni identificar.
- La guarda el custodio de datos y la entrega solo para cada uso. La aplicación no la guarda.
- La opción **¿LEMAS aún no tiene clave?** sirve únicamente la primera vez: crea una clave nueva para descargar. Si ya existe una clave, no la use.
- Nunca envíe la clave por correo ni la suba a internet.

### 5.4 Práctica sin datos reales
Para capacitar al personal, genere un Excel y una clave **ficticios**:
```bash
python tools/generar_excel_ejemplo.py --salida ejemplo_lemas
```
Crea `ejemplo_institucional.xlsx` y `clave_ejemplo.key`, con personas inventadas («Estudiante 0001», «Representante 0001»). Úselos en el modo institucional para ensayar todo el procedimiento.

### 5.5 Alternativa con Colab (uso académico)
El cuaderno `00a_seudonimizacion` produce el mismo `base_seud.csv` con la misma clave. La aplicación también acepta ese archivo (**…o suba base_seud.csv**), pero con él no hay lista con nombres, porque el archivo no los contiene. En ese caso el custodio puede usar `python tools/seudonimizar.py reidentificar`.

**Nunca:** suba el Excel, `base_seud.csv` o la lista con nombres a la versión pública, a GitHub, al correo o a chats; ni comparta la clave.

## 6. Protocolo sugerido para el contacto
- Presentarse como apoyo: "Queremos saber si necesitan información o facilidades para la matrícula".
- Ofrecer opciones (fechas, planes de pago y canales de atención); no hablar de deudas ni de la lista.
- Registrar el resultado del contacto (contactado, sin respuesta, confirmó o no continuará) para evaluar el proceso en mayo.

## 7. Mensajes de error frecuentes

| Mensaje | Qué hacer |
|---|---|
| "La versión pública solo acepta datos sintéticos" | Está en la versión de demostración. Use **Prueba con ejemplo**, o use el modo institucional dentro de LEMAS |
| "El archivo contiene columnas con identificadores directos" | Subió un CSV con cédulas o nombres. En LEMAS suba el **Excel junto con la clave** en el modo institucional; nunca lo suba a la versión pública |
| "El archivo de clave no es válido" | Use el archivo `clave_lemas.key` del custodio, sin abrirlo ni modificarlo |
| "No se pudo leer el Excel" | Verifique que sea `.xlsx`, sin contraseña y que no esté abierto en Excel |
| "Al Excel le faltan columnas obligatorias" | Revise los encabezados `CI`, `cedulap` y `Codigo` (`data/README.md`) |
| "Por seguridad no se continúa: … aún hay columnas con nombres o cédulas" | El Excel tiene una columna extra con datos personales. Elimínela y vuelva a subirlo |
| "Modo institucional abierto desde otro equipo" | Abra la aplicación en el mismo computador, con `iniciar_lemas.bat` |
| "Se necesitan los dos archivos: el Excel y la clave" | Suba el archivo que falta |
| "Faltan columnas obligatorias" | Revise que los encabezados sean los estándar (`data/README.md`) |
| "La base no tiene suficientes ciclos para entrenar" | Incluya en el Excel las hojas de los ciclos 2022 a 2025, o coloque `models/sistema_real.joblib` |
| "Ese ciclo no tiene estudiantes con reserva aprobada" | Elija otro ciclo: el actual aún no tiene reservas aprobadas o no está en el archivo |
| "El archivo no tiene la estructura esperada" | Verifique que sea un CSV generado por `00a`, con fechas en formato día/mes/año o año-mes-día |

## 8. Preguntas frecuentes
- **¿Por qué no se usa el modelo de IA para ordenar la lista?** Porque en la prueba final la regla D2 fue mejor (Lift 1,97 frente a 0,98). El análisis con IA sirvió para descubrir y validar esa regla.
- **¿Puedo cambiar k?** Sí. Un k mayor encuentra más casos pero con menor proporción de aciertos.
- **¿La app guarda los datos?** No. Procesa en memoria y no escribe en disco. Solo quedan los archivos que usted descargue.
- **¿Necesito Colab?** No. En el modo institucional la app convierte el Excel directamente.
- **¿Qué pasa si se pierde la clave?** Las listas ya descargadas con nombres siguen sirviendo. Para trabajar de nuevo puede crear otra clave, pero los seudónimos cambiarán y no coincidirán con los archivos anteriores.
- **¿Pueden ver la app desde otro computador?** No. El arranque solo permite abrirla en el mismo equipo.
- **¿Sirve para estudiantes nuevos?** No. Solo para estudiantes antiguos con reserva aprobada.
