# Catálogo de figuras · revisión 02

Seis preguntas complementarias, sin agregar contaminantes con unidades distintas. SVG vectorial y PNG a 220 dpi, fondo blanco. No se elaboró aún el PDF final.

## Figura 1: 01_mensual_pm10.svg / 01_mensual_pm10.png

- **pregunta:** ¿Cómo cambió PM₁₀ en los días coincidentes de cada mes?
- **filtros:** PM10 · meses 2023 y 2024 · solo fechas pareadas
- **estadistico:** Media de bases diarias PM10 antes de redondear
- **denominador:** n de pares / días del mes de 2023
- **fuente:** data/processed/sprint-2/; contrato web exportado desde esos resultados
- **decision:** D10–D11; separar cobertura y cambio.
- **hallazgo:** Diciembre: 31/31 pares; PM10 +65.20%, sin inferencia causal.

## Figura 2: 02_diciembre_categorias.svg / 02_diciembre_categorias.png

- **pregunta:** ¿Cómo cambió la distribución diaria de partículas y CO en diciembre?
- **filtros:** PM10/PM2.5/CO · diciembre 2023 y 2024
- **estadistico:** Conteo de categorías diarias
- **denominador:** 31 días calendario por fila
- **fuente:** data/processed/sprint-2/; contrato web exportado desde esos resultados
- **decision:** D12–D14; no promediar categorías ni equiparar cambio relativo con riesgo.
- **hallazgo:** Mala o peor: PM10 15→27 y PM2.5 7→19; CO Buena 31→31.

## Figura 3: 03_cobertura.svg / 03_cobertura.png

- **pregunta:** ¿Qué meses permiten comparar las mediciones?
- **filtros:** Ambos años · 12 meses · contaminantes comunes, NO2 y ET/RH/WS
- **estadistico:** Porcentaje y conteo de horas utilizables
- **denominador:** Horas calendario de cada mes (672–744; febrero 2024=696)
- **fuente:** data/processed/sprint-2/; contrato web exportado desde esos resultados
- **decision:** D03–D04, D17; mostrar cobertura antes de interpretar.
- **hallazgo:** O3 2023 comienza en julio; RH cubre temporadas distintas; NO2 aparece en parte de 2024.

## Figura 4: 04_patron_horario.svg / 04_patron_horario.png

- **pregunta:** ¿En qué horarios fueron frecuentes las categorías desfavorables de PM₁₀?
- **filtros:** PM10 · ambos años · 12 meses × 24 horas
- **estadistico:** Proporción de categorías horarias Mala o peor del NowCast
- **denominador:** Horas evaluables por mes/hora; expected=días calendario del mes
- **fuente:** data/processed/sprint-2/; contrato web exportado desde esos resultados
- **decision:** D04 y D14; contrastar patrones sin mezclar NowCast y concentración cruda.
- **hallazgo:** Mayor frecuencia 2024 entre celdas con ≥75% cobertura: Marzo, 10:00, 27/29 = 93.10% Mala o peor (cobertura 29/31).

## Figura 5: 05_episodio_cruce.svg / 05_episodio_cruce.png

- **pregunta:** ¿Cómo se extendió el episodio de PM₁₀ entre diciembre y enero?
- **filtros:** PM10 · 29/12/2023–05/01/2024 · episodio 31/12–03/01
- **estadistico:** Base diaria antes de redondear, con dos días de contexto a cada lado
- **denominador:** 24 h/día; episodio 96/96 lecturas y 4 días
- **fuente:** data/processed/sprint-2/; contrato web exportado desde esos resultados
- **decision:** D18; fechas reales y continuidad, sin atribuciones causales.
- **hallazgo:** El episodio de cuatro días cruza el año y se conserva como un único intervalo.

## Figura 6: 06_meteorologia.svg / 06_meteorologia.png

- **pregunta:** ¿Cómo coincidieron PM₁₀ y la temperatura externa en diciembre de 2024?
- **filtros:** PM10 y ET · diciembre 2024
- **estadistico:** Pares diarios y rho de Spearman descriptivo
- **denominador:** 31/31 pares diarios
- **fuente:** data/processed/sprint-2/; contrato web exportado desde esos resultados
- **decision:** D15; ET externa, sin usar IT para afirmar inversión.
- **hallazgo:** Se describe asociación ρ=0.172; la cobertura no permite inferir causalidad.
