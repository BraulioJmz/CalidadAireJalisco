# Sprint 3: inventario y diagnóstico de Miravalle 2015–2024

Etapa inicial realizada el 8 de noviembre de 2026 en la rama local `sprint-3/historico-prediccion`, desde `main` actualizado en `527af8a4781df65ede43b746dffdddb330915740`. No se entrenaron modelos, cambiaron vistas, recalcularon índices, hicieron commits, subieron ramas ni generaron paquetes.

## Fuentes y conservación

Se descargaron únicamente 2015–2022 desde `https://aire.jalisco.gob.mx/reportes/BD_AAAA.xlsx`. Los ocho libros están en `data/source/sprint-3/originales/`. Se comprobaron HTTP 200, formato XLSX y CRC del contenido OpenXML. Cada original conserva sus bytes.

Los originales de 2023 y 2024 se reutilizan en `data/source/sprint-2/originales/`, sin duplicarlos ni descargarlos otra vez. Se verificaron contra los SHA-256 del Sprint 2. La procedencia acreditada de 2024 sigue siendo un archivo suministrado para la asignatura, no una descarga realizada en esta etapa. Su URL solicitada por patrón se registra por separado. No se inventó una fecha de descarga para los dos archivos preexistentes.

`config/fuentes_sprint3.json` contiene la ruta, URL, URL final, inicio y fin de descarga en UTC, tamaño, SHA-256 y cabeceras HTTP de cada descarga. Para los originales preexistentes conserva procedencia y hash, con fecha de descarga no acreditada indicada explícitamente. `conservacion_inicial.json` registra los hashes de los 263 archivos versionados al comenzar; todos siguen intactos, incluidos PDF, Word, fuentes, resultados y evidencia del Sprint 1 y Sprint 2.

## Pipeline revisado y límites de reutilización

- Sprint 1: `pipeline/etl.py`, `limpieza.py`, `calculos.py`, `nom172.py`, `procesar.py` y `docs/sprints/sprint-1.md`. Trabaja por mes, incluye calentamiento y escribe resultados del periodo. Su ETL exige un conjunto fijo con DIA/MES y su limpieza tiene límites físicos adicionales; no se ejecutó sobre los años históricos.
- Sprint 2: `pipeline/anual.py`, `normativa.py`, `preparar_sprint2.py`, `exportar_sprint2_web.py`, `config/fuentes_sprint2.json` y las decisiones metodológicas. Contiene comparación retrospectiva, control de calidad y procedencia de 2023–2024. `source_extract` escribe en la carpeta del Sprint 2, por lo que no se llamó para esta etapa.
- Sprint 3: los nuevos scripts leen cada libro en flujo, identifican su hoja y encabezados, inspeccionan Param, filtran MIR y escriben exclusivamente en las carpetas nuevas de diagnóstico. No aplican la normativa retrospectiva al histórico ni convierten concentraciones en categorías.

## Estructura, tiempo y unidades

Los diez libros tienen hojas `Data` y `Param`. MIR aparece como `MIR`, con el nombre Miravalle en el catálogo. Cada año tiene todas sus fechas horarias: 8,760 filas o 8,784 en 2016, 2020 y 2024. En conjunto son **87,672 horas**. No se encontraron fechas inválidas, fuera de año, desalineadas, duplicados por fecha ni filas MIR idénticas repetidas. HOUR coincide con DATE y los auxiliares de día/mes, donde existen, también coinciden. Esto verifica la rejilla, no la presencia de mediciones.

En 2015–2022 hay 20 encabezados, sin DIA ni MES; las dimensiones de las hojas no siempre están declaradas. Param conserva un catálogo de códigos de invalidación y las unidades están en posiciones distintas a las recientes. En 2023–2024 hay 22 encabezados: `dia `/`mes ` en 2023 y `DIA`/`MES ` en 2024, incluyendo espacios. Las fórmulas auxiliares se leen por su resultado almacenado, sin recalcularlas; no faltan cachés de las fórmulas MIR encontradas. Los encabezados y tipos originales y todos los metadatos no vacíos se conservan en `libro_AAAA.json`.

Las unidades declaradas son estables entre los libros: PM10 y PM2.5 en µg/m³; O3, NO, NO2, NOX, SO2 y CO en ppm; ET/IT en °C; RH en %; WS en m/s; WD en grados; PP en mm; ATM en mmHg; RS en W/m² y UVI en mW/m² según la fuente. IT es temperatura interna de la caseta, no temperatura ambiental. La unidad nominal no acredita una calibración o equipo idéntico entre años. DATE no aporta zona u offset: se conserva la hora local codificada y no se inventa conversión UTC ni ajuste de horario estacional. Las fechas UTC del manifiesto corresponden a la adquisición, no a las mediciones.

## Cobertura por variable

Porcentaje de **horas únicas con número finito en el original**, sobre todas las horas esperadas de cada año. Un 0 % significa ninguna medición numérica, no concentración cero. Se conservan los ceros reales. Esta tabla no acredita calidad instrumental ni suficiencia normativa.

| Año | PM10 | PM2.5 | O3 | CO | NO2 | SO2 | NO | NOX |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 2015 | 73.6 | 0.0 | 97.3 | 97.3 | 97.3 | 83.3 | 0.0 | 0.0 |
| 2016 | 23.9 | 0.0 | 74.0 | 79.8 | 73.5 | 61.3 | 0.0 | 0.0 |
| 2017 | 87.3 | 0.0 | 96.1 | 90.9 | 97.5 | 60.8 | 0.0 | 0.0 |
| 2018 | 92.1 | 22.2 | 88.0 | 79.1 | 91.6 | 91.0 | 0.0 | 0.0 |
| 2019 | 93.8 | 20.4 | 74.9 | 82.2 | 87.4 | 86.8 | 0.0 | 0.0 |
| 2020 | 90.9 | 47.1 | 69.9 | 90.8 | 41.1 | 90.1 | 0.0 | 0.0 |
| 2021 | 57.6 | 25.7 | 61.4 | 84.7 | 29.0 | 67.9 | 0.0 | 0.0 |
| 2022 | 85.1 | 83.7 | 87.8 | 32.9 | 0.0 | 11.7 | 0.0 | 0.0 |
| 2023 | 91.1 | 89.8 | 37.5 | 84.1 | 0.0 | 94.5* | 0.0 | 0.0 |
| 2024 | 91.7 | 78.3 | 90.8 | 92.4 | 36.2† | 0.0 | 35.4† | 36.1† |

*SO2 2023 está presente en el original, pero excluido del conjunto utilizable por la evidencia oficial conservada en el Sprint 2: INECC, Informe Nacional 2023, p. 222, falta de calibración. Sus 8,281 números se preservan; la cobertura básica utilizable es 0 %.*

†NO/NO2/NOX de 2024 tienen lecturas, pero no están declarados en el catálogo MIR de ese libro. No acreditan por sí solos procedencia o calibración. NO2 sigue siendo exploratorio y no se propone como objetivo.

| Año | ET | RH | WS | WD | IT | PP | ATM | RS | UVI |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2015 | 98.6 | 98.6 | 98.6 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| 2016 | 96.1 | 96.1 | 96.1 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| 2017 | 97.6 | 97.6 | 97.6 | 0.3 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| 2018 | 0.0 | 0.0 | 93.7 | 93.7 | 93.7 | 0.0 | 45.8 | 0.0 | 0.0 |
| 2019 | 99.4 | 99.5 | 99.5 | 99.5 | 99.5 | 89.8 | 0.0 | 27.6 | 0.0 |
| 2020 | 49.3 | 49.4 | 49.3 | 49.3 | 97.4 | 0.0 | 0.0 | 0.0 | 0.0 |
| 2021 | 92.1 | 92.7 | 92.5 | 92.4 | 97.3 | 0.0 | 0.0 | 0.0 | 0.0 |
| 2022 | 62.2 | 62.2 | 62.0 | 37.6 | 97.8 | 0.0 | 33.1 | 0.0 | 0.0 |
| 2023 | 83.6 | 42.7 | 90.8 | 65.1 | 96.2 | 0.0 | 92.1 | 0.0 | 0.0 |
| 2024 | 84.8 | 47.6 | 78.0 | 70.2 | 84.6 | 0.1† | 84.8 | 0.0 | 0.0 |

†PP de 2024 contiene seis mediciones y no figura en el catálogo MIR: no es una serie de lluvia anual ni permite interpretar vacíos como ausencia de precipitación. ATM 2018 tiene números en 45.8 % de las horas, pero solo 37.7 % supera el control básico ATM > 0; el original se conserva.

`cobertura_anual.csv` contiene las 170 combinaciones año/variable con conteos numéricos, vacíos, textos, ceros, negativos, plausibilidad, unidades, catálogo, máximos, mínimos y continuidad. `cobertura_mensual.csv` conserva las 2,040 combinaciones por mes. La cobertura básica descuenta concentraciones negativas/no finitas, rangos meteorológicos mínimos explícitos y SO2 2023; no demuestra calibración. No se impone un techo estadístico a las concentraciones ni se eliminan extremos por ser altos.

## Discontinuidades y periodos aprovechables

- PM10: interrupción desde 2015-10-12 01:00 hasta fin de año; solo febrero de 2016 supera 75 % de horas, y hay múltiples huecos largos en el resto de 2016. En 2021 hay un vacío continuo de **2,448 horas**, del 7 de agosto al 16 de noviembre. Son limitaciones explícitas, no datos que deban rellenarse.
- PM10 en 2017–2020 y 2022–2024: entre 85.1 % y 93.8 % anual, con al menos diez meses por año por encima de 75 %. En 2023 el mes bajo es octubre; en 2024, julio. Esto identifica ventanas candidatas, no declara esos años completos ni representativos.
- PM2.5: sin mediciones en 2015–2017; primera medición numérica encontrada el 1 de junio de 2018. Cobertura baja y fragmentada hasta 2021; mejora en 2022–2024.
- CO: mayor cobertura total que PM10, pero solo 32.9 % en 2022 y un vacío continuo de 5,831 horas ese año.
- O3: 37.5 % en 2023, con una larga interrupción al inicio del año; enero carece de mediciones. No se debe desplazar ni conectar ese vacío con el bloque disponible posterior.
- Meteorología: no hay ET/RH en 2018; en 2020 rondan 49 %, y RH en 2023–2024 apenas 43–48 %. WD prácticamente no existe antes de 2018. PP, RS, ATM y UVI no forman un conjunto uniforme de covariables para toda la década. WD requiere tratamiento circular y no una media lineal de grados.
- El código `IO` aparece en cuatro registros de WD de 2020, y Param lo define como «Inválido por operador». Se conserva como texto no numérico y se cuenta separadamente de los vacíos; no se transforma en cero. El catálogo de banderas no equivale a que todas esas banderas aparezcan en los datos.

Los intervalos disponibles y no utilizables de al menos 24 horas consecutivas están en `intervalos_24h.csv`, con fechas y longitudes exactas por año y variable. No se conectan intervalos a través de huecos. El descriptor mensual de 75 % es exploratorio, no una nueva regla normativa ni garantía de representatividad.

## Objetivo recomendado: concentración horaria de PM10 en µg/m³

Propongo **PM10 a +1, +2 y +3 horas** como primer objetivo, por su equilibrio entre disponibilidad reciente, historia aprovechable y relevancia en los episodios ya documentados. Dispone de **69,000 horas numéricas básicas**, el **78.7 %** de las 87,672 esperadas. Tiene **53,608 ventanas** con las 24 horas pasadas observadas (incluido t) y las tres horas futuras también observadas; **11,764** tienen su origen en 2023–2024. Las ventanas se solapan y no son observaciones independientes. Las unidades y el catálogo nominal son consistentes, pero no se asume homogeneidad instrumental validada.

| Candidato | Cobertura básica 2015–2024 | Ventanas completas 24+3 | Ventanas con origen 2023–2024 | Consideración |
|---|---:|---:|---:|---|
| PM10 | 78.7 % | 53,608 | 11,764 | Objetivo recomendado: cobertura reciente >91 % y episodios desfavorables relevantes. |
| CO | 81.4 % | 62,609 | 12,494 | Alternativa sólida si se prioriza cantidad de datos; grave interrupción en 2022. |
| O3 | 77.8 % | 53,805 | 7,834 | La interrupción de 2023 debilita la continuidad reciente. |
| PM2.5 | 36.7 % | 17,611 | 9,181 | Historia temprana ausente y fragmentación hasta 2021. |

La elección de PM10 no se basa en que tenga el máximo de cobertura total: CO lo supera. Se pondera también la cobertura reciente y el hallazgo ya conservado del Sprint 2 de 15/31 frente a 27/31 días PM10 en Mala o peor en diciembre de 2023 y 2024. No se atribuyen causas a esos episodios. NO2 no es adecuado como primer objetivo por su discontinuidad y la incertidumbre de procedencia; SO2 tiene exclusión oficial reciente y ausencia en 2024.

| Año | Pares t/t+1 | Pares t/t+2 | Pares t/t+3 | Ventanas completas 24+3 de PM10 |
|---|---:|---:|---:|---:|
| 2015 | 6,403 | 6,381 | 6,366 | 5,535 |
| 2016 | 2,055 | 2,025 | 1,995 | 1,232 |
| 2017 | 7,580 | 7,569 | 7,557 | 6,492 |
| 2018 | 8,052 | 8,045 | 8,036 | 7,681 |
| 2019 | 8,170 | 8,145 | 8,126 | 7,135 |
| 2020 | 7,867 | 7,824 | 7,792 | 5,765 |
| 2021 | 4,985 | 4,961 | 4,943 | 3,769 |
| 2022 | 7,257 | 7,197 | 7,157 | 4,235 |
| 2023 | 7,834 | 7,762 | 7,728 | 5,539 |
| 2024 | 7,963 | 7,937 | 7,911 | 6,225 |

Los pares solo exigen observar t y t+h; no garantizan contexto completo. La última columna exige las 27 horas consecutivas y es la referencia conservadora para una propuesta sin imputación. El conteo usa fechas reales y permite cruzar de año si están las mediciones; no usa posiciones compactadas que salten un vacío. Una ventana de 24 horas es una propuesta inicial de contexto, no una decisión final de modelo. No se generaron matrices de entrenamiento.

## Propuesta de siguiente etapa, todavía no ejecutada

1. Acordar un protocolo para PM10 horario crudo, sin sustituirlo por NowCast, promedio diario, máximo o categoría. Construir después las etiquetas por fecha exacta para cada horizonte y una máscara explícita de disponibilidad.
2. Comenzar con rezagos causales y calendario; comparar después ET/WS únicamente donde existan, sin usar IT como temperatura exterior ni meteorología futura que no estaría disponible al emitir la predicción. Registrar la pérdida de muestra y su distribución por estación del año.
3. Definir evaluación temporal progresiva, por ejemplo desarrollo hasta 2022, validación temporal en 2023 y evaluación retrospectiva en 2024. Este último año ya se exploró en el Sprint 2: no debe presentarse como prueba ciega intacta. Las ventanas con objetivos que crucen una frontera de partición deben excluirse del ajuste anterior; toda transformación se ajustará solo con entrenamiento.
4. Antes de modelos más complejos, contrastar persistencia y referencia de la misma hora del día anterior, con MAE/RMSE, número de predicciones por horizonte, mes y disponibilidad. No usar particiones aleatorias ni tratar ventanas solapadas como réplicas independientes. Revisar estabilidad temporal y procedencia instrumental antes de atribuir utilidad operacional.

## Archivos y reproducción

Desde la raíz del repositorio, con Python 3.12 y las dependencias numéricas ya disponibles del Sprint 2:

```powershell
.\.venv\Scripts\python.exe -X utf8 pipeline/descargar_historico_sprint3.py
.\.venv\Scripts\python.exe -X utf8 pipeline/inventario_sprint3.py
.\.venv\Scripts\python.exe -X utf8 pipeline/verificar_inventario_sprint3.py
.\.venv\Scripts\python.exe -X utf8 -W error -m pytest tests -q
```

El descargador reutiliza los originales registrados si conservan su hash. Si un original cambió o hay un archivo sin registro en el destino, falla antes de sobrescribirlo. Solo los años faltantes se solicitan a la red. El inventario se ejecutó con el runtime Python 3.12.14 disponible en Codex, pandas 3.0.1 y openpyxl 3.1.5; las pruebas del repositorio se ejecutaron también con su entorno existente de pandas 2.2.3. No se añadieron dependencias.

Salidas en `data/processed/sprint-3/`: inventario general, diez JSON de libro con metadatos, cobertura anual y mensual, intervalos y disponibilidad de horizontes. El manifiesto de adquisición está en `config/`; el registro inicial y la verificación de conservación, en esta carpeta. No se publican estos archivos en la interfaz.

Verificación realizada: **96 pruebas Python aprobadas** (86 previas y 10 nuevas), y **1,272 comprobaciones de integridad y conciliación**, incluyendo SHA-256/CRC de los diez originales, 34 cotejos numéricos con los extractos del Sprint 2, coherencia mensual/anual y conservación de los 263 archivos previos. La comprobación de software no acredita calibración, ausencia de sesgo por faltantes ni capacidad predictiva: aún no se entrenó ni evaluó ningún modelo.
