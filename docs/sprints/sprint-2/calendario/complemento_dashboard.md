# Complemento: calendario comparativo y recorrido temporal

El dashboard incorpora en la vista **Episodios** un calendario del mismo mes de 2023 y 2024. Cada fecha real representa la categoría de su indicador diario, con color y abreviatura. Se pueden consultar las fechas manualmente o recorrerlas en secuencia mediante reproducción, pausa y avance de un día. Las tablas de máximos, los episodios y sus series de contexto permanecen disponibles debajo del calendario.

**Pregunta de análisis:** «¿Cómo se distribuyeron los días favorables, desfavorables y sin información dentro de cada mes, y qué diferencias aparecen entre ambos años?».

La interacción permite reconocer agrupaciones temporales que un promedio mensual oculta y contrastar el mismo día del calendario sin confundir cobertura con contaminación. Buena (código 0) es una categoría válida; el gris rayado identifica fechas sin indicador suficiente. El 29 de febrero de 2024 se conserva y se explica que no tiene fecha equivalente en 2023. Esto es distinto de una fecha real cuya medición falta.

Al seleccionar un día se muestran el indicador redondeado, la base antes del redondeo, categoría, lecturas utilizables/esperadas, bases horarias suficientes y meteorología diaria disponible (temperatura externa, humedad relativa y velocidad del viento, con unidades y n). Los valores se toman de los CSV diarios calculados. Las partículas usan promedio de 24 h; CO, máximo diario del promedio móvil de 8 h; O₃, máximo horario diario. No se recalculan reglas normativas en el navegador.

El recorrido comienza pausado, respeta las fechas sin datos y termina al final del mes. Cambiar filtros o abandonar la vista lo pausa y limpia el temporizador. Los botones funcionan con teclado; con movimiento reducido se desactiva la reproducción automática y se conserva la selección manual. La fecha seleccionada se destaca con contorno sin ocultar su categoría.

Esta exploración es descriptiva: no resuelve la insuficiencia de cobertura anual ni la incertidumbre instrumental, y una coincidencia temporal no identifica una fuente emisora ni demuestra causalidad. NO₂ mantiene su tratamiento exploratorio separado.

## Capturas recomendadas para el documento existente

Las imágenes están en `output/playwright/calendario_2026-10-23/` del proyecto y se entregan también en la carpeta externa `capturas_calendario/`. Son recortes de la aplicación; el encabezado fijo se oculta únicamente durante la captura para que no tape el calendario.

1. **`calendario_diciembre_pm10_escritorio.png`**: comparación de diciembre, seleccionando el 31 en ambos años. Se ven Mala o peor 15/31 y 27/31, los colores y los valores diarios. Ilustra diferencias dentro del mes sin atribuir causas.
2. **`calendario_febrero29_escritorio.png`**: selección del 29/02/2024, con la explicación de la fecha inexistente en 2023. Ilustra la sincronización y el tratamiento del año bisiesto.
3. **`calendario_febrero29_movil.png`**: la misma selección en disposición vertical, con detalle diario y meteorología. Permite revisar legibilidad y uso en móvil.
4. **`calendario_ozono_sin_datos_escritorio.png`**: enero, con el 15 seleccionado. Contrasta las 31 fechas sin indicador de O₃ en 2023 con los días evaluables de 2024; no presenta faltantes como Buena.
5. **`calendario_diciembre_co_escritorio.png`**: los 31 días Buena de cada año y el estadístico específico de CO. Muestra que conservar una categoría no implica que las concentraciones sean idénticas.

Este complemento se entrega por separado para su incorporación editorial. No modifica los PDF ni Word existentes ni registra participación individual.
