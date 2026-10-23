# Encargo para Codex local · revisión 02

Trabaja en el repositorio local `CalidadAireJalisco`, sobre los cambios actuales de la rama `sprint-2/revision-01`. No clones otro proyecto, no descartes cambios y no sobrescribas evidencia del Sprint 1. La tarea está autorizada: implementa, verifica y entrega el ZIP; no te limites a proponer un plan. No hagas push ni despliegues en esta fase.

Lee primero la auditoría adjunta y `docs/sprints/sprint-2/decisiones_metodologicas.md`. Identifica cualquier contradicción con el código antes de trasladar un resultado al tablero. Conserva el diseño y los componentes útiles del sitio actual.

## A. Reparar la entrega técnica

1. Confirma la omisión de `data/source/sprint-2/originales/BD_2024.xlsx` en el ZIP revisión 01. Localiza el original ya utilizado y verifica SHA-256 `fe8e30b34cb64cfa3bfdaa52bcafb935c942b8e59de6132916497cf28a738e9c`.
2. Corrige la selección de archivos para que los insumos obligatorios formen parte tanto de la firma de entradas como del empaquetado, independientemente de `.gitignore`. Usa una lista explícita y verificable de archivos requeridos o mecanismo equivalente. No basta con validar únicamente lo que ya quedó seleccionado.
3. Si falta un archivo requerido, falla con un mensaje claro antes de emitir un ZIP aprobado. No inventes fuentes ni descargues una versión distinta para cubrir la omisión.
4. Añade una prueba de regresión significativa: archivo requerido existente pero ignorado por Git se incluye; archivo requerido ausente impide la entrega. Evita pruebas que solo copien la implementación.
5. Actualiza REPRODUCIR e informe para distinguir pruebas locales, reproducción desde extractos y reproducción desde originales. Verifica desde una extracción limpia, sin Git y sin resolver rutas hacia la carpeta de trabajo o hacia el paquete anterior.

## B. Implementar el Sprint 2 en la aplicación existente

Agrega una ruta estable `/sprint-2` y sus enlaces en navegación y página principal. Conserva `/sprint-1` y sus evidencias. La portada debe permitir acceder claramente al análisis 2024 vs. 2023; evita que el único periodo accesible siga siendo marzo de 2024. No marques el Sprint 2 como entrega final ni publicado si falta el PDF.

Consume los archivos calculados del pipeline como única fuente de resultados. Agrega un exportador reproducible que genere los recursos necesarios para la web sin ejecutar Python desde el navegador. No copies a mano porcentajes en componentes ni recalcules normativa con una segunda implementación JavaScript. Valida el contrato de datos, unidades, nulos y dimensiones en el límite de lectura/exportación. No publiques hojas originales completas en el navegador si basta con sus agregados y enlaces de evidencia.

### Encabezado e indicadores

- Contexto visible: estación Miravalle MIR, Academia Miravalle, mediciones 2023–2024, análisis retrospectivo con bandas de referencia 2024.
- Selección de contaminante principal PM10, PM2.5, O3 y CO; año/ambos y mes/todo el año según la vista. No conviertas NO2 en una comparación anual disponible para 2023; ubícalo como complemento exploratorio.
- Indicadores: días evaluables/esperados, proporción de días Mala o peor con denominador, magnitud diaria seleccionada y cambio pareado cuando alcance el criterio del proyecto. Muestra unidades y nombre del estadístico.
- Para el año completo, mostrar cobertura y «Comparación anual con cobertura insuficiente según el criterio del proyecto»; las medias descriptivas pueden quedar en detalle. No dar un titular de mejora/deterioro anual ni ocultar los datos existentes.
- El cambio diciembre CO debe aparecer junto con 1.202206 → 2.335489 ppm y el hecho de que los 31 días permanecieron en Buena en cada año. Explica que se comparan medias de máximos diarios móviles de 8 h.
- Nunca usar cero, Buena, una flecha favorable ni una línea continua para representar un dato ausente. Si la base de un porcentaje de cambio es cero, mostrar «no calculable» y la diferencia absoluta.

### Vistas que responden al encargo

Selecciona un conjunto compacto. La tabla fija el propósito; no exige seis gráficas visibles simultáneamente. Usa pestañas o detalle cuando ayude a la lectura.

| Vista | Pregunta que responde | Implementación y justificación |
|---|---|---|
| Concentraciones mensuales y comparación pareada | ¿Qué cambió cada mes y cuáles tienen mejores/peores condiciones evaluadas? | Comparar 2023 y 2024 en la misma unidad por contaminante. Distinguir resumen de todos los días válidos y comparación de fechas pareadas; rotular qué población se muestra. Mostrar n, cambios absolutos/relativos y meses insuficientes. No conectar huecos ni clasificar meses con cobertura insuficiente como los mejores. |
| Categorías y contaminantes determinantes | ¿Cambió la distribución del riesgo y qué contaminantes determinaron la peor categoría? | Barras por año/mes con colores NOM y sin datos en gris, sobre todos los días calendario. Añadir conteos exactos y detalle de denominantes con empates. Distinguir cuatro comunes y máximo disponible, sin promediar ordinales. Las frecuencias de determinantes pueden sumar más que los días por los empates. |
| Cobertura | ¿Qué tan comparable es cada periodo? | Matriz mes × variable, ambos años, horas utilizables/esperadas. Mostrar que no faltan filas de la rejilla, pero sí mediciones. Distinguir suficiencia de ventanas y criterio mensual/anual del proyecto. |
| Patrón horario | ¿En qué horas se concentraron categorías desfavorables? | Matriz mes × hora por año y contaminante: horas Mala o peor/horas evaluables. Tooltip con numerador, denominador, cobertura y métrica horaria. Diferenciar NowCast de PM, móvil 8 h CO y base horaria de otros gases. Mostrar insuficiencia sin aparentar ausencia de contaminación. |
| Periodos y eventos relevantes | ¿Qué episodios, días y horas merecen revisión? | Tabla de máximos diarios/horarios y episodios, con selección y serie temporal de contexto. Usar los criterios exportados: máximos separados, episodios de ≥2 días Mala o peor. Distinguir lectura cruda e indicador. Si un episodio cruza de año, mantener sus fechas reales y rotular el cruce al filtrar; no duplicar su duración. Un atípico no demuestra una causa. |
| Meteorología | ¿Cómo coincidieron concentración y temperatura, humedad o viento? | Dispersión con pares del mismo mes/año, ET/RH/WS, unidades, rho de Spearman, n y cobertura. Usar exactamente los puntos exportados. Mensaje para <15 pares o serie constante. No mostrar causalidad ni correlacionar WD linealmente. La selección inicial debe tener datos y el usuario puede explorar periodos insuficientes con su explicación. |

No añadas gráficas ornamentales o redundantes. Una tabla breve puede resolver mejor un detalle que otra visualización. Cada figura debe tener pregunta/título, unidad, denominador, fuente y nota de alcance. No construyas comparaciones de concentración sumando contaminantes con unidades distintas.

### Perspectiva de la agencia

Incorpora un bloque breve de hallazgos verificables y uso académico: priorizar revisión de diciembre, inspección de horarios con mayor frecuencia desfavorable y necesidades de mejor cobertura. Distingue «observado», «posible interpretación» y «dato adicional necesario». No atribuyas incendios, inversión térmica, tráfico o cambios de instrumentación sin evidencia. El determinante de la categoría no identifica una fuente emisora.

### Legibilidad y acceso a evidencia

Mantén estilo visual del sitio, adaptación a móvil, contraste suficiente, leyendas que no dependan solo del color y títulos/unidades legibles. Evita paneles de depuración en el flujo principal. Ofrece metodología y descargas CSV/figuras como evidencia, con rutas existentes y sin enlaces al disco C: del autor. Muestra el estado de cobertura en contexto, sin llenar la pantalla de avisos repetidos.

## C. Material para el reporte

Exporta las figuras seleccionadas con datos reales en SVG o PNG de resolución suficiente y fondo legible. Si una visualización web es difícil de exportar fielmente, genera su equivalente estático desde los mismos datos procesados, sin cambiar población ni estadístico.

Entrega `catalogo_figuras.md` con: archivo, pregunta, filtros/periodo, variable, estadístico, denominador, fuente, decisión que justifica la selección y hallazgo que la figura respalda. Si no aporta un hallazgo útil, descártala. Incluye una tabla de hallazgos con referencias a CSV, columnas, fechas, n y cálculos. No redactes reflexiones personales ni cumplimiento de integrantes como si fueran hechos.

## D. Validación proporcionada al cambio

1. Ejecuta las pruebas del pipeline y las regresiones nuevas pertinentes, con avisos como errores. Las 54 pruebas anteriores deben seguir pasando; informa el total real nuevo.
2. Reproduce los 24 resultados. Categorías, fechas, textos y ausencias coinciden exactamente; magnitudes continuas con tolerancia justificada. No exigir hashes idénticos a floats trigonométricos entre Windows/Linux. No cambies bandas ni reglas para hacer coincidir una prueba errónea.
3. Ejecuta instalación reproducible con lock, el comando de tipos/lint del proyecto y build de producción. No cambies versiones de dependencias por comodidad; si un cambio resulta necesario, justifica y conserva el lock coherente.
4. Revisa en navegador escritorio y móvil: cambio de contaminante/periodo, cobertura insuficiente, nulos, NO2 sin 2023, meteorología insuficiente, episodios, leyendas, navegación Sprint 1/2 y descargas. Registra lo efectivamente comprobado. Capturas solo de la aplicación, sin datos privados del equipo.
5. Comprueba automáticamente valores clave de la exportación web contra el pipeline, incluidos los denominadores y diciembre: PM10 +65.20 %, PM2.5 +47.55 %, CO +94.27 %; CO Buena 31/31 en cada año. El control debe detectar diferencias de datos, no limitarse a buscar literales en HTML.
6. Genera un ZIP revisión 02 y extráelo en una carpeta temporal limpia. Verifica presencia/hash de ambos Excel, fuentes y recursos web; reproduce desde los originales y comprueba la aplicación con las instrucciones incluidas. No uses dependencias, archivos o rutas de la carpeta fuente para cubrir omisiones. Las dependencias pueden instalarse de los locks; no incluir node_modules ni el entorno virtual en el ZIP.

## E. Entrega de retorno

- `sprint2_revision_02.zip`, con manifiesto y huella externa, sin credenciales ni cachés.
- Informe breve: cambios, decisiones y por qué, pruebas ejecutadas, estado de verificación desde ZIP limpio y límites pendientes.
- Figuras exportables, catálogo y tabla trazable de hallazgos.
- Capturas del tablero en escritorio/móvil cuando se haya revisado visualmente.
- Comandos de reproducción y arranque, rutas de salida y estado Git real. Mantén el trabajo local; no afirmes commit/push/deploy que no se realizaron.

Esta fase termina con una propuesta de dashboard funcional y evidencia revisable. El PDF del equipo se integrará después con las figuras verificadas, la interpretación y la bitácora real del líder.
