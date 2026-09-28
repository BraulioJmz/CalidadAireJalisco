# Sprint 1 · Reporte técnico 1 · marzo 2024

**Estado:** entregado · **Ruta:** `/sprint-1` · **Tag:** `sprint-1`
**Estación:** Miravalle (MIR), SEMADET · **Periodo:** 2024-03-01 00:00 a 2024-03-31 23:00 (29-feb solo como calentamiento)
**Norma:** NOM-172-SEMARNAT-2023 (Índice AIRE Y SALUD)

## Objetivo y preguntas guía

Desarrollar un proceso reproducible para preparar, transformar, analizar y visualizar datos ambientales, y comprender
cómo una medición horaria se convierte en información útil.

1. ¿Qué ocurrió durante marzo y cómo cambia la interpretación entre la perspectiva horaria y la diaria?
2. ¿Cómo se transforma un dato ambiental desde que se genera hasta convertirse en información útil?

## Dónde se cumple cada requisito

| Requisito de la actividad | Dónde está |
|---|---|
| Preparación: tipos, unidades, faltantes, formato, atípicos, criterios de limpieza | Reporte §2.2–2.3 y §3.1; `pipeline/etl.py`, `pipeline/limpieza.py`; bitácora |
| Aplicación de la NOM-172 (indicadores, redondeo, compleción, bandas, colores, mensajes) | Reporte §3.2 (tablas 3 y 4); `pipeline/nom172.py`, `pipeline/calculos.py` |
| Simulación horaria (dato → procesamiento → indicador → categoría → información) | Reporte §4.1, Figura 3 y Tabla 7; `web/components/SimulationPlayer.tsx` |
| Numeralia diaria y representación de cada día | Reporte §4.2 (tabla 8, calendario, tabla 9); matriz día × hora en el Observatorio |
| Horario contra diario y qué se pierde al resumir | Reporte §4.3 (figuras 5–7) |
| Máximos y relación con la meteorología | Reporte §4.4 (tabla 10, figura 8) |
| Interpretación desde la agencia | Reporte §5 y el Observatorio (franjas para planear actividades) |
| Visualizaciones y justificación; referentes (SIMAJ, SINAICA, RESPIRA) | Reporte §3.4 (tablas 5 y 6) |
| Conclusiones y limitaciones | Reporte §6 |
| Código y evidencia para reproducir | Reporte §7, este repositorio y las descargas del periodo |

## Pipeline

```
BD_2024.xlsx (raíz, solo lectura)
 → pipeline/etl.py       data/processed/miravalle_2024_clean.csv
                         data/processed/2024-03/miravalle_marzo2024_clean.csv   (+24 h de calentamiento)
 → pipeline/calculos.py  data/processed/2024-03/Archivo1_Calculos_Horarios.csv
                         data/processed/2024-03/Archivo2_Calculos_Diarios.csv
 → pipeline/procesar.py  web/data/periodos/2024-03.json, Excel horario y diario, bitácora
 → pipeline/reporte.py   data/processed/2024-03/reporte_resultados_2024-03.txt  (texto para el reporte en Word)
   pipeline/mapa.py      web/data/mapa_jalisco.json, data/processed/estaciones_semadet.csv
```

Reproducir todo: `python pipeline/procesar.py --periodo 2024-03` y `python -m pytest tests`.

## Hallazgos de datos

- 744 de 744 registros horarios, sin duplicados; HOUR 0–23 coincide con DATE.
- Miravalle mide O₃, CO, PM₁₀ y PM₂.₅; NO₂ y SO₂ vacíos. Humedad relativa: 0 de 744 en toda la red SEMADET.
- 17-mar sin datos; 18-mar parcial; PM₂.₅ sin datos el 13 y del 29 al 31 (73.9 % de disponibilidad).
- Viento con resolución limitada: 0.4 a 1.2 m/s, paso 0.1; 0.4 se interpreta como calma.
- Formato: PM2.5 como texto en BD_2024 (se convierte a número); encabezado `MES ` con espacio; DIA y MES son fórmulas.
  En la hoja *Param*, las estaciones COU, SAN y SMT tienen nombre y abreviatura intercambiados.
- Bitácora de control de calidad: 66 registros (54 evento real probable, 8 revisar, 3 valor bajo plausible, 1 limitación). No se eliminó ningún valor.

## Resultados

- **Días (29 con categoría):** Mala 18, Aceptable 10, Buena 1 (7-mar, calificado solo con O₃ y CO), sin datos 2 (17 y 18).
- **Responsable diario:** PM₁₀ 25 días, O₃ 4 (6, 7, 24 y 25 de marzo).
- **Horas (708 con categoría):** Buena 407 (57 %), Aceptable 126, Mala 158, Muy Mala 17 (todas por PM₁₀, entre 08:00 y 12:59).
  Responsable por hora: PM₁₀ 402, O₃ 197, PM₂.₅ 99, CO 10.
- **Horario contra diario:** 57 % de las horas en Buena contra 3 % de los días; 17 días con horas peores que su categoría
  diaria (59 horas en total); 154 cambios de categoría horaria en el mes.
- **Franjas:** crítica de 06:00 a 12:59 (la mitad o más de los días en Mala o peor); mejor de 16:00 a 00:59.
- **Máximos:** PM₁₀ horario 297 µg/m³ (8-mar 09:00 y 27-mar 08:00); NowCast de PM₁₀ 172 µg/m³ (6-mar 11:00);
  O₃ 0.091 ppm (27-mar 14:00, única hora de O₃ en Mala); temperatura de 9 a 35 °C.
- **Simulación (26 al 28 de marzo):** 22 cambios de categoría y 25 horas en Mala o peor. 27-mar 08:00: PM₁₀ horario
  297 µg/m³, NowCast 141 µg/m³ → Muy Mala; a las 13:00 el responsable pasa a O₃; a las 18:00 regresa a Buena.

## Decisiones del equipo

- **Bandas de partículas:** columna «a partir de enero de 2024» de las tablas 4 y 5 (PM₁₀ 45/60/132/213; PM₂.₅ 15/33/79/130),
  porque corresponde a la fecha de los datos.
- **Redondeo (numeral 5.2.4):** half-up; PM a entero, O₃ a 3 decimales, CO a 2, también en los indicadores diarios.
- **NowCast:** función de referencia del curso sin cambios (24 casos en `tests/`). En marzo 2024 su redondeo coincide con
  el numeral 5.2.4 en todas las horas.
- **Contaminante responsable en empate:** el más cercano al límite superior de su banda (la NOM no define desempate).
- **Atípicos:** z robusto por hora del día (|z| > 3.5); se clasifican, no se eliminan. Sin imputación.
- **Colores:** RGB oficiales de la tabla 11; blanco para «sin información». **Mensajes:** texto oficial de la tabla 12 para
  los tres grupos de población, y descripción del riesgo de la tabla 10.
- **Periodo de simulación:** ventanas de 72 h desde las 00:00 con ≥ 90 % de cobertura, ordenadas por peor categoría,
  contaminantes responsables distintos, cambios de categoría y horas en Mala o peor.

## Limitaciones

- Un solo mes y una sola estación; los patrones deben confirmarse en los siguientes sprints.
- Relaciones con la meteorología: coincidencias temporales, no causas demostradas.
- Sin humedad relativa, precipitación ni radiación solar; anemómetro con resolución limitada.
- Días con categoría diaria incompleta por falta de compleción de partículas (PM₁₀: 6, 7, 17 y 18; PM₂.₅: 6, 7, 13, 14, 17, 18, 29, 30 y 31).

## Entregables y descargas

En `/descargas/2024-03/` (también desde el reporte y el Observatorio): datos limpios del periodo, bitácora, Archivo 1,
Archivo 2, Excel horario y diario, y el reporte de resultados en texto.

## Para el Sprint 2

- Rama `sprint-2`, `python pipeline/procesar.py --periodo AAAA-MM`, ruta `web/app/sprint-2` y fila en `SPRINTS` (`web/lib/site.ts`).
- El Observatorio mostrará el selector de periodo y la evolución entre meses en cuanto haya dos periodos.
- Pendientes: lectura robusta de columnas (alias y faltantes), soporte multi-año y parametrizar los pocos textos del
  reporte que todavía mencionan fechas de marzo.
