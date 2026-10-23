# Cambios: calendario comparativo con recorrido temporal

23 de octubre de 2026 · rama local `sprint-2/revision-01`.

## Comportamiento implementado

En `/sprint-2`, la pestaña **Episodios** incorpora el calendario «Un mes, día a día». Se mantienen las tablas de máximos, episodios y series de contexto existentes. El calendario respeta año y contaminante principal; muestra el mes general o, cuando se elige «Todo el año», ofrece un selector de mes propio.

Las fechas reales son botones con color y abreviatura de categoría. Buena (0) se conserva como válida. El gris rayado identifica un día sin indicador suficiente; los espacios anteriores al inicio de la semana son solo alineación. El 29 de febrero de 2024 permanece seleccionable y se explica la inexistencia de una fecha equivalente en 2023, sin inventar un día ni convertirlo en ausencia de medición.

La selección sincroniza mes y día entre ambos años. Cada detalle muestra I (indicador redondeado), EXACT (base anterior al redondeo), C, lecturas N y bases horarias N_IND frente a 24 horas esperadas, y las medias meteorológicas M y sus N para ET/RH/WS. Las partículas se identifican como promedio diario de 24 h; CO, máximo diario del promedio móvil de 8 h; O₃, máximo horario diario. Los valores meteorológicos insuficientes se conservan como ausencias.

El recorrido inicia pausado. Reproducir requiere una acción explícita y avanza cada 1.4 segundos por las fechas reales, incluidos días sin datos. Se detiene al final del mes. Los pasos manuales y la selección pausan; los cambios de contaminante, año, periodo o mes reinician pausados en el día 1. Al abandonar la vista se desmonta el calendario y se limpia el temporizador; también se pausa al ocultar la pestaña del navegador. La preferencia de movimiento reducido desactiva la reproducción y conserva controles manuales. Botones nativos permiten Enter/Space y muestran foco; el contorno de selección no sustituye el color de categoría.

## Datos y conservación

Se amplía el contrato a `mir-s2-v2` con 731 registros diarios tomados de los CSV procesados. Python y TypeScript validan fechas, dimensiones, conteos, nulos y reconciliación con las distribuciones mensuales/anuales. No se implementan bandas ni indicadores normativos en JavaScript. Los dos CSV diarios se añaden a las descargas, conservando los recursos anteriores.

108 archivos registrados antes de la modificación se verifican por SHA-256, incluidos fuentes, los 24 resultados, figuras, página y evidencia del Sprint 1, PDF/Word existentes y los textos públicos revisados el 23 de octubre. Los campos anteriores de la exportación coinciden con la revisión 02; solo se cambia la versión de esquema y se añaden registros/estadísticos diarios y dos descargas. No cambian cálculos, bandas, dependencias ni datos del análisis.

La portada, ficha y metodología mantienen la limpieza pública; se conservan los avisos científicos de cobertura, validación instrumental, NO₂ exploratorio y límites causales. No se incorpora participación individual. Los PDF y Word no se editan; [complemento_dashboard.md](complemento_dashboard.md) se entrega por separado.

## Comprobaciones ejecutadas

- 86 pruebas Python aprobadas con avisos como errores: las 73 anteriores y 13 comprobaciones nuevas de fechas, valores, conteos y corrupción del calendario.
- Contrato TypeScript: datos reales aprobados y 11 mutaciones rechazadas. Se prueban además las funciones de fechas y recorrido de meses de 28, 29, 30 y 31 días.
- Tipos (`npm run lint`, que ejecuta `tsc --noEmit`) y build de producción aprobados.
- 38 comprobaciones de navegador con Playwright CLI/Edge: inicio pausado, sincronización, Buena/ausencias, febrero y 29 adicional, filtros, avance, pausa, fin del mes, desmontaje, teclado y movimiento reducido. O₃ enero 2023 tiene 31 fechas sin indicador; CO diciembre tiene Buena 31/31 en ambos años; PM₁₀ diciembre tiene Mala o peor 15/31 y 27/31.
- Cuatro páginas de producción local con navegación interna y HTTP 200. Las 35 descargas enlazadas respondieron 200 y coincidieron por bytes con sus archivos locales, incluidas siete históricas del Sprint 1.
- Seis capturas en escritorio 1440×1100 y móvil 390×844. Se revisó la legibilidad del calendario y sus detalles. El documento móvil no presenta desbordamiento horizontal. Solo se oculta el encabezado fijo durante el recorte de captura para evitar superposición.

Los registros están en `output/playwright/calendario_2026-10-23/`. La prueba local integral queda en `calendario/verificacion/`; se separa de los informes históricos. La reproducción del ZIP se informa externamente con el SHA-256 exacto del archivo, sin afirmar por adelantado su resultado dentro de este documento.

## Reproducción y alcance

Ver [REPRODUCIR_CALENDARIO.md](REPRODUCIR_CALENDARIO.md). El ZIP conserva código, fuentes, resultados, evidencia, capturas y complemento, con manifiesto interno y huella externa; no incluye dependencias ni entornos. El ensayo aislado crea una extracción sin Git, instala los locks, reproduce los 24 resultados desde originales y extractos por separado, exporta el calendario y prueba contrato, recorrido, tipos, build y HTTP.

Las verificaciones cubren los casos indicados; no acreditan exhaustividad de toda combinación del dashboard ni validación instrumental. Los patrones son descriptivos y no prueban causas ni resuelven la insuficiencia de comparación anual. No se ha ensayado una plataforma distinta de Windows. Los cambios continúan locales, sin commit, push, despliegue ni marca de entrega en Classroom.
