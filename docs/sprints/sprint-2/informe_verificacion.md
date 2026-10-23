# Informe de controles del pipeline · Sprint 2, revisión 02

**Estado: APROBADO**. Fecha local: 22 de octubre de 2026. Equipo 3, Academia Miravalle, MIR.

Repositorio clonado en carpeta hermana del paquete. Commit inicial `67a385204b87dfe8260974510d2cf305714b264c`, rama inicial main, sin cambios locales. Rama de trabajo `sprint-2/revision-01`; implementación sin commit ni push.

Se mantienen los cálculos de revisión 01 y se corrige la completitud del ZIP. La revisión 02 añade /sprint-2, exportación web, figuras y comprobación limpia. Los controles web se registran por separado en revision02/verificacion/. Se preserva la evidencia del Sprint 1.

Pruebas del proyecto: **73 ejecutadas, 0 fallos, 0 errores, 0 omitidas**. Incluyen las 9 existentes del Sprint 1. La suite y el pipeline revisado se ejecutan con avisos tratados como errores.

## Controles

| Control | Resultado |
|---|---|
| original_2023 | Correcto |
| extracto_2023 | Correcto |
| original_2024 | Correcto |
| extracto_2024 | Correcto |
| evidencia_NOM_172_SEMARNAT_2023_DOF.pdf | Correcto |
| evidencia_Informe_Nacional_Calidad_Aire_2023.pdf | Correcto |
| evidencia_Sprint1_entregado.pdf | Correcto |
| evidencia_Protocolo_manejo_datos_calidad_aire.pdf | Correcto |
| preservacion_sprint1 | Correcto |
| pruebas_proyecto | Correcto |
| control_independiente_ventanas | Correcto |
| contraste_referencia_docente | Correcto |
| reproduccion_excel_extractos | Correcto |

Comandos, detalles y firma de entradas: verificacion.json. Salida de pruebas: pruebas.txt y pruebas.xml. Versiones: entorno.json y requirements-sprint2-lock.txt.

## Resultados y denominadores

17,544 horas; 731 días; 9,847 señalamientos/exclusiones. Los 8,281 números de SO2 2023 se conservan en las fuentes y se excluyen de indicadores. No faltan filas de las rejillas de origen; sí faltan mediciones.

| Indicador | Pares anuales / 365 | Cobertura | Trimestres (%) | Cambio anual representativo |
|---|---:|---:|---|---|
| PM10 | 291 | 79.73% | 82.22 / 82.42 / 73.91 / 80.43 | No |
| PM2.5 | 250 | 68.49% | 74.44 / 81.32 / 33.70 / 84.78 | No |
| O3 | 114 | 31.23% | 0.00 / 0.00 / 59.78 / 64.13 | No |
| CO | 285 | 78.08% | 90.00 / 79.12 / 59.78 / 83.70 | No |
| GLOBAL | 62 | 16.99% | 0.00 / 0.00 / 22.83 / 44.57 | No |

No se infiere una mejora o deterioro del año completo a partir de estas medias incompletas.

| Diciembre | Pares / 31 | Media 2023 | Media 2024 | Cambio | Destacable por cobertura |
|---|---:|---:|---:|---:|---|
| PM10 | 31 | 60.952203 | 100.690738 | +65.20% | Sí |
| PM2.5 | 31 | 27.829667 | 41.063050 | +47.55% | Sí |
| O3 | 15 | 0.048667 | 0.060733 | +24.79% | No |
| CO | 31 | 1.202206 | 2.335489 | +94.27% | Sí |

PM: media de promedios diarios de 24h (µg/m³). CO: media de máximos diarios de promedios móviles de 8h (ppm). O3: media de máximos horarios diarios (ppm). Se usan bases anteriores al redondeo final; no son el mismo estadístico. O3 y global de diciembre tienen 15/31 pares, por debajo del 75%.

## Contraste con el prototipo y correcciones

Se conserva el cálculo de categorías del prototipo. La revisión valida encabezados/fecha/HOUR, preserva procedencia y fila, evita agregados ordinales del global, añade dispersión y fechas de máximos, separa tipos de concentración y exporta pares y episodios.

EXACT_CO ahora conserva máximos de medias móviles sin redondear: cambia ligeramente su media pareada (diciembre +94.27% frente a +94.31% del prototipo). El indicador final y las categorías se contrastan columna por columna en comparacion_prototipo.csv. Los CSV fuente tienen hashes diferentes por incluir trazabilidad y columnas originales adicionales.

JSON conserva precisión completa. Spearman usa pares estabilizados a 12 decimales para no crear órdenes espurios por ruido flotante; los pares exportados reproducen sus rangos. El prototipo tenía seis decimales en JSON y sus estadísticas de GLOBAL promediaban ordinales; se corrigen. Los 18 registros de gases, los 15 pares meteorológicos y los umbrales de cobertura de comparación son reglas adicionales del proyecto.

La ejecución inicial del prototipo sin UTF-8 falló al leer JSON en Windows; con -X utf8 sus 24 pruebas pasan. Sus logs conservan FutureWarning de pandas y RuntimeWarning de series vacías. En desarrollo, un control de rangos detectó pérdida de precisión JSON; fue corregida antes de la verificación final. No se ocultan avisos con filtros globales.

El control independiente detectó CO 2024-03-23 22:00: media exacta 0.485, esperado 0.49; la versión flotante producía 0.48. Se corrige usando Decimal en la aritmética de promedios de CO/PM y de ponderación NowCast; se añadió una prueba específica. Las discrepancias reales se conservan en comparacion_prototipo.csv. Ver historial_incidencias.md.

Se contrastan también los 24 casos de la referencia docente conservada del Sprint 1 contra el método de esta revisión en contraste_casos_docentes.csv. Las diferencias por orden de redondeo se documentan; no se modifican los resultados de referencia ni se exige coincidencia artificial.

Meteorología: 360 combinaciones mensuales contaminante/variable; rho solo con n≥15 y series variables, sin p-valores. Episodios consecutivos exportados: 86. Ver pares_meteorologicos.csv, dias_relevantes.csv y episodios.csv.

## Límites y pendientes académicos

- No se verifican promedios subhorarios ni calibración instrumental.
- Ningún contaminante común cumple representación anual por trimestre.
- NO2 complementario: lecturas Data sin enumeración en catálogo MIR de Param.
- Los controles web, build y ZIP limpio se registran por separado en el informe revisión 02.
- No se atribuyen causas de episodios ni aportaciones individuales.
- O3 2023 solo desde 24/07 18:00; NO2 2024 desde 16/08; RH representa temporadas distintas. Comparar las ventanas coincidentes no elimina el sesgo por ausencia.
- La fecha se interpreta como hora civil codificada, sin inventar UTC o cambios de horario; se conserva 29/02 en descriptivos y se omite solo del pareamiento.
- No se revisa ni se entrega el PDF final en esta fase. La participación del equipo, correcciones de clase y aprobación docente siguen requiriendo evidencia real.

Decisiones, fundamentos, efectos y límites: decisiones_metodologicas.md. Reproducción: REPRODUCIR.md. Cambios y estado Git: cambios_codigo.json. Fuentes y hashes: config/fuentes_sprint2.json y fuentes_hashes.json. El ZIP incluye manifiesto interno y huella externa.
