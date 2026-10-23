# Auditoría de Sprint 2 · revisión 01

Fecha: 22 de octubre de 2026. Equipo 3 · Academia Miravalle · estación MIR.

**Dictamen de esta revisión: los resultados numéricos revisados son utilizables para desarrollar el análisis. El ZIP necesita una corrección antes de considerarse una entrega técnica autosuficiente. La aplicación y el PDF siguen pendientes.** Esto no acredita calibración instrumental, representatividad estadística ni aprobación docente.

## 1. Comprobaciones realizadas aquí

Se trabajó con los bytes del ZIP recibido y las fuentes suministradas, sin modificar el repositorio Windows ni publicar cambios.

| Comprobación | Resultado |
|---|---|
| ZIP y manifiesto | CRC correcto; los 131 archivos enumerados coinciden en tamaño y SHA-256. El manifiesto es una entrada adicional. |
| Pruebas | 54 pruebas pasan nuevamente con `-W error`; cero fallos. |
| Pipeline desde extractos | Ejecución completa con avisos tratados como errores; 24 archivos reproducidos. |
| Comparación de salidas | CSV: mismos registros, columnas, textos y ausencias; valores numéricos dentro de 1e-10. Los dos JSON coinciden íntegramente como estructuras. |
| Fuentes Excel | Se regeneraron los extractos desde los dos Excel: las 8,760 filas MIR de 2023 y 8,784 de 2024, con sus 24 columnas, coinciden celda por celda con los extractos recibidos. Para 2024 se usó el original que ya estaba disponible en esta conversación. |
| Preservación del Sprint 1 | 68/68 archivos coinciden con el registro de preservación. También coinciden con el clon previo al normalizar finales de línea de Windows/Linux. |
| Diciembre | Recálculo de medias PM y máximos móviles CO desde las lecturas fuente usando aritmética decimal; se confirman los tres cambios publicados. |
| Distribuciones | Se reconcilian 182 filas anuales/mensuales: categorías, días válidos, faltantes y denominadores. GLOBAL no contiene medias de códigos ordinales. |
| Meteorología | 360 combinaciones declaradas; los 190 coeficientes no nulos se recalcularon desde los puntos exportados y coinciden. Esto comprueba reproducibilidad, no causalidad. |
| Límites de categorías | La inspección visual de las páginas 10–11 del PDF oficial confirma el signo ≤ en los límites superiores de Buena. |

SHA-256 del ZIP recibido:

`4742e07e92c95601003afd8158eed7f3df11bbca62ca69ab2619d16d62eb06bc`

Los CSV recibidos usan finales de línea de Windows. Tras normalizarlos, 22/24 archivos coinciden también como texto. Las únicas diferencias restantes aparecen en `M_WD` y `RESULTANTE_WD` de los dos archivos diarios: máximo absoluto 8.53e-14, compatible con aritmética trigonométrica entre plataformas. No cambian concentraciones, categorías ni resultados del reporte.

El informe recibido declara 17 controles aprobados. Aquí se contrastaron las comprobaciones de la tabla; **no se volvió a ejecutar el verificador completo desde el ZIP limpio**, porque falta el original 2024 que ese programa exige. Las 54 pruebas y la reproducción desde los extractos sí se ejecutaron aquí.

## 2. Corrección necesaria: falta un insumo obligatorio

El ZIP no contiene:

`CalidadAireJalisco/data/source/sprint-2/originales/BD_2024.xlsx`

Sin embargo, `config/fuentes_sprint2.json` y `REPRODUCIR.md` declaran ambos originales. El verificador intenta leer el archivo directamente; la reproducción completa desde originales, tal como está documentada, no puede ejecutarse únicamente con lo que trae el ZIP.

La causa se encuentra en la combinación de:

- `.gitignore`, que contiene la regla `BD_2024.xlsx`.
- `project_files()`, que en un repositorio Git usa `git ls-files --cached --others --exclude-standard`.
- El empaquetador, que verifica la integridad de los archivos seleccionados, pero no exige que estén todos los insumos obligatorios.

El manifiesto comprueba integridad del contenido enumerado; no demuestra que el paquete esté completo. La corrección debe hacer que firma y empaquetador incluyan explícitamente los insumos requeridos, aun si Git los ignora, y comprobar el ZIP extraído sin acudir al directorio original. No hace falta forzar la incorporación del Excel a Git para incluirlo en una entrega ZIP.

Hash esperado del original 2024, confirmado contra el archivo suministrado:

`fe8e30b34cb64cfa3bfdaa52bcafb935c942b8e59de6132916497cf28a738e9c`

Esta omisión no invalida los resultados reproducidos desde los extractos; sí impide describir el ZIP actual como autosuficiente desde los dos Excel originales.

## 3. Hallazgos que ya pueden entrar al documento

### Diciembre: concentración y categorías

Las comparaciones siguientes utilizan 31 pares diarios por contaminante: mismo mes y día en ambos años.

| Magnitud | Media 2023 | Media 2024 | Cambio |
|---|---:|---:|---:|
| PM10: media de promedios diarios de 24 h, µg/m³ | 60.952203 | 100.690738 | +65.20 % |
| PM2.5: media de promedios diarios de 24 h, µg/m³ | 27.829667 | 41.063050 | +47.55 % |
| CO: media de máximos diarios de promedios móviles de 8 h, ppm | 1.202206 | 2.335489 | +94.27 % |

| Categoría diaria Mala o peor | Diciembre 2023 | Diciembre 2024 | Diferencia |
|---|---:|---:|---:|
| PM10 | 15/31 = 48.39 % | 27/31 = 87.10 % | +38.71 puntos porcentuales |
| PM2.5 | 7/31 = 22.58 % | 19/31 = 61.29 % | +38.71 puntos porcentuales |
| CO | 0/31 = 0 % | 0/31 = 0 % | 0 puntos porcentuales |

Los 31 días de CO permanecen en Buena en ambos diciembres. El máximo diario de CO en diciembre 2024 es 4.03925 ppm antes del redondeo final. Por eso, +94.27 % describe el aumento de una magnitud concreta y no significa que el riesgo sanitario se haya duplicado.

La conclusión admisible es que **diciembre de 2024 presentó mayores indicadores de partículas y más días con categorías desfavorables que diciembre de 2023 en las fechas evaluadas**. No se demuestra la causa ni un deterioro equivalente de todo el año.

### Comparación anual: alcance de la cobertura

| Indicador | Pares / 365 | Cobertura | Menor cobertura trimestral |
|---|---:|---:|---:|
| PM10 | 291 | 79.73 % | 73.91 % |
| PM2.5 | 250 | 68.49 % | 33.70 % |
| O3 | 114 | 31.23 % | 0.00 % |
| CO | 285 | 78.08 % | 59.78 % |
| Resumen común de cuatro contaminantes | 62 | 16.99 % | 0.00 % |

Ninguno cumple simultáneamente 75 % anual y 75 % en cada trimestre. **Ese umbral es una decisión del proyecto para comunicar las comparaciones**, distinta de la suficiencia normativa de ventanas horarias o diarias. No es una prueba estadística de representatividad. Las medias anuales disponibles se pueden presentar descriptivamente, con n y sus límites, sin usarlas como titular de una mejora o deterioro anual.

O3 y GLOBAL en diciembre tienen solamente 15/31 pares: sus cambios no deben recibir el mismo énfasis que los tres resultados con 31/31.

## 4. Decisiones que deben explicarse en el reporte y tablero

- Se aplican bandas de referencia 2024 a ambos años para mantener una escala común. Es una comparación retrospectiva; no reconstruye los avisos oficiales emitidos en 2023.
- El redondeo decimal se efectúa en el orden documentado, después del ajuste aplicable. El ejemplo CO de 0.485 → 0.49 justifica la corrección numérica; el nuevo +94.27 % sustituye al +94.31 % del prototipo.
- Los indicadores diarios se distinguen por su magnitud: promedio de PM, máximo móvil CO o máximo horario de otros gases. No se comparan como si todos fueran medias de concentración ambiental.
- Se conservan ausencias y extremos; las banderas no prueban incendios, errores de sensor o fuentes de emisión.
- Se excluye SO2 2023 conforme a la evidencia oficial citada, conservando los valores originales. NO2 permanece como complemento exploratorio por la discrepancia de catálogo.
- El resumen común exige PM10, PM2.5, O3 y CO disponibles; el máximo entre contaminantes disponibles tiene composición variable. La interfaz debe distinguir ambos y no llamar al primero un índice oficial completo.
- Las categorías se resumen con conteos, porcentajes y puntos porcentuales. No se promedian sus códigos.
- La meteorología se analiza en fechas coincidentes y por mes; rho y n describen asociación. La ausencia de datos, especialmente RH, limita las comparaciones entre temporadas.

## 5. Estado real de los entregables

| Entregable del encargo | Estado tras revisión 01 |
|---|---|
| Preparación reproducible y comparación numérica | Base revisada; corregir autosuficiencia del ZIP. |
| Dashboard comparativo | Pendiente: la aplicación recibida conserva el Sprint 1. |
| Figuras con preguntas e interpretación | Pendientes de selección y exportación final. |
| Reporte anual integrado en PDF | Pendiente de redactar, incorporar figuras y verificar formato. |
| Reporte del líder | Requiere actividades, cumplimiento y observaciones reales de los integrantes. |
| Correcciones de clase | Requieren observaciones reales; no se deben inventar. |
| Repositorio y entrega Classroom | Repositorio conocido; cambios locales sin commit según informe recibido. No se ha publicado ni subido una entrega. |
