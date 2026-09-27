# Sprint 1 · Boletín 1 · marzo 2024

**Ruta:** `/sprint-1` · **Tag:** `sprint-1` · **Periodo:** 2024-03 (29-feb como calentamiento)

## Hallazgos de datos
- Miravalle mide O₃, CO, PM₁₀ y PM₂.₅ (NO₂ y SO₂ vacíos). Humedad relativa: 0/744 en toda la red SEMADET.
- 17-mar sin datos, 18-mar parcial; PM₂.₅ sin datos el 13 y del 29 al 31. Viento con resolución 0.4–1.2 m/s.
- El CSV de marzo del equipo coincide 100 % con BD_2024.

## Resultados
- Días: Mala 18, Aceptable 10, Buena 1, sin datos 2. PM₁₀ dominante 25 días, O₃ 4.
- Horas: 57 % Buena; 17 horas en Muy Mala (todas por PM₁₀, 08–12 h).
- Periodo simulado: 26–28 mar (22 cambios; 27-mar 08:00 Muy Mala; 14:00 O₃ en Mala, 0.091 ppm).

## Decisiones del equipo (documentadas en la metodología)
- Responsable en empate: el contaminante más cerca del límite superior de su categoría.
- Atípicos: z robusto por hora del día; se clasifican, no se eliminan.
- NowCast: función de la profesora sin cambios (pruebas en `tests/`).
