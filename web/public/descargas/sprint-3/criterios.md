# Histórico 2015–2024: criterios anteriores a interpretar comparaciones

Se conserva C05 como evidencia congelada. Esta etapa no ajusta modelos ni utiliza sus errores para modificar decisiones predictivas. El registro `conservacion_antes.json` firma originales, inventario, resultados, configuración, modelos y predicciones anteriores. Solo se autoriza refactorizar las cuatro rutas/componentes web enumerados en ese registro y añadir recursos nuevos.

## Poblaciones y suficiencia

- Concentración mensual: media de **horas crudas utilizables**, con n y horas esperadas del mes. Se considera suficiente descriptivamente con ≥75 % de horas. Media anual: ≥75 % de horas **y ≥75 % en cada trimestre**. No se ajusta una tendencia representativa a años insuficientes. Son criterios del proyecto; no prueban representatividad ni son límites de exposición de una norma.
- Perfiles estacionales y horarios: medias de observaciones crudas coincidentes en la población seleccionada, n y denominadores visibles. El agregado de diez años mezcla años con cobertura distinta y se etiqueta descriptivo. Se conservan picos y huecos.
- Comparación de dos años: medias de bases diarias **antes del redondeo** en fechas con el mismo mes/día y datos en ambos años. Se requiere ≥75 % de pares para destacar un mes; para el año, además ≥75 % en cada trimestre. El denominador es la intersección real de calendarios: 29 de febrero solo se parea si ambos años lo tienen. Un porcentaje no se calcula sobre referencia cero. NO2 2024 y NO/NOX son exploratorios, sin conclusión comparativa representativa.
- Categorías diarias: distribución de conteos, nunca media de códigos. Se conserva el denominador esperado y los días sin indicador. La categoría 0 (Buena) es válida. NO y NOX se describen como concentraciones, sin categoría normativa.
- Episodio: ≥2 días consecutivos con categoría diaria Mala o peor; un día sin indicador interrumpe la secuencia. Se conservan límites reales al cruzar meses y años. Máximos horarios: tres por año/contaminante separados ≥24 horas. Atípico estadístico: |z robusto|>3.5 respecto a misma hora, mes y año, escala max(1.4826 MAD, piso), reutilizando los pisos del Sprint 2. Son señales para inspección, no evidencia de incendio, falla o causalidad; no se excluyen.
- Meteorología: medias diarias ET, RH y WS con ≥18 horas; WD circular ponderada por WS con ≥18 pares no calmos y resultante no degenerada. Spearman se calcula por mes/año con ≥15 pares diarios coincidentes y ambas series no constantes. Los pares y sus fechas se exportan. No hay p-valores ni atribución causal. IT no sustituye ET; WD no se correlaciona linealmente.

## Referencia retrospectiva y reglas normativas

Se reutiliza `pipeline/normativa.py` y las **bandas de referencia de 2024**, como en Sprint 2, para todos los años. No es reconstrucción de avisos oficiales históricos ni evaluación oficial de cumplimiento. Las bases diarias son media de partículas, máximo móvil de 8 horas de CO y máximo horario de O3/NO2/SO2. Los mínimos normativos de ventanas se distinguen del requisito adicional del proyecto de 18 lecturas diarias para máximos de gases. Los archivos horarios no permiten verificar el mínimo de minutos dentro de cada hora. Referencia: [NOM, tabla 3 y §5.2](https://sidof.segob.gob.mx/notas/docFuente/5715154).

La continuidad de los cálculos usa los libros 2015–2024. Se omiten las primeras 11 horas de PM y 7 de CO de 2015 por falta de diciembre de 2014. Los años siguientes sí pueden usar el contexto previo disponible. Esto puede producir diferencias de arranque respecto a la revisión del Sprint 2, que no tenía diciembre de 2022; sus resultados originales no se sobrescriben ni se sustituyen en su ruta histórica.

Se conserva la exclusión oficial de SO2 2023 por falta de calibración (INECC p. 222, evidencia del Sprint 2). NO2/NO/NOX 2024 no figuran en el catálogo MIR: procedencia y calibración no acreditadas. Los controles básicos son los del inventario: finitud, concentraciones no negativas, RH 0–100, WD 0–360, WS no negativa y otros rangos mínimos documentados. No se inventa homogeneidad instrumental entre años.

## Dashboard y trazabilidad

La portada recibe solo metadatos, hallazgos y métricas compactas. Histórico, pares de periodos, calendario mensual, meteorología y predicciones se cargan en JSON del mismo origen al consultar cada vista. Los detalles horarios se fragmentan por mes; no se carga toda la década al abrir. El navegador no recalcula normativa ni entrena. No hay peticiones entre dominios que requieran CORS.

Predicción consume exclusivamente los CSV congelados de evaluación 2024. Los filtros de **origen** de los pronósticos y **fecha objetivo** de las métricas se etiquetan por separado. No se clasifica directamente PM10 predicho; 114 µg/m³ es un umbral diagnóstico, no una banda normativa. Las métricas conservan R² negativos, n y la población evaluada del 70.9 %. Se mantienen las advertencias de subestimación en altas y exposición descriptiva previa de 2024.
