# NOM-172-SEMARNAT-2023: Guía de referencia para el proyecto (Estación Miravalle)

**Fuente oficial:** Diario Oficial de la Federación, publicada el 25 de enero de 2024. Entra en vigor 180 días naturales después de su publicación (≈ 23 de julio de 2024). Sustituye a la NOM-172-SEMARNAT-2019.
**Enlace:** https://sidof.segob.gob.mx/notas/docFuente/5715154

> Esta norma es la base normativa obligatoria para todo lo que muestre el dashboard: qué contaminantes reportar, cómo calcular la concentración representativa de cada uno, cómo clasificarla en una categoría de calidad del aire, qué color asignarle y qué mensaje de riesgo mostrar. Todo el trabajo del equipo (cálculos, tablas, semáforos, mensajes) debe poder justificarse con un numeral de esta norma.

---

## 1. Objetivo y alcance

Establece los lineamientos para **obtener y comunicar, de forma horaria y diaria**, el **Índice AIRE Y SALUD** (el nombre oficial que sustituye a "ICA"/"índice de calidad del aire"), con el fin de informar de forma clara, oportuna y continua:
- el estado de la calidad del aire,
- los probables daños a la salud, y
- las medidas para reducir la exposición.

Es de observancia **obligatoria** para gobiernos estatales y municipales que operan sistemas de monitoreo (SEMADET/Jalisco es uno de estos, y de hecho participó en la elaboración de esta NOM).

## 2. Contaminantes que cubre ("contaminantes criterio")

La norma cubre 6 contaminantes (excluye plomo, que sí es "criterio" en general pero queda fuera de esta NOM):

| Contaminante | Unidad de reporte | Cifras decimales |
|---|---|---|
| PM10 (partículas ≤10 µm) | µg/m³ | 0 |
| PM2.5 (partículas ≤2.5 µm) | µg/m³ | 0 |
| Ozono (O3) | ppm | 3 |
| Dióxido de nitrógeno (NO2) | ppm | 3 |
| Dióxido de azufre (SO2) | ppm | 3 |
| Monóxido de carbono (CO) | ppm | 2 |

Si la estación Miravalle no mide los 6, el índice y las tablas solo se calculan para los contaminantes que sí monitorea.

## 3. Definiciones clave (numeral 4)

- **Banda del índice AIRE Y SALUD**: intervalo de concentración que califica el nivel de contaminación y su riesgo a la salud.
- **Concentración base**: el estadístico (promedio horario, móvil de 8h, móvil ponderado de 12h, o de 24h) a partir del cual se asigna la banda.
- **Compleción de datos**: cantidad mínima de datos requerida para que un cálculo sea válido (ver sección 5).
- **Personas sensibles**: menores de 12 años, mayores de 60 años, personas gestantes, y personas con enfermedades cardiovasculares o respiratorias (EPOC, asma) — la norma pide mensajes diferenciados para este grupo.
- **Estación de monitoreo automático**: la caseta con analizadores/sensores que mide en tiempo real (esto describe exactamente lo que es Miravalle dentro del sistema SEMADET).

## 4. Cómo se calcula la "concentración base" de cada contaminante (numeral 5.2)

Este es el corazón técnico de la norma — define qué estadístico usar según el contaminante y si el reporte es horario o diario.

| Contaminante | Concentración base — reporte **horario** | Concentración base — reporte **diario** |
|---|---|---|
| PM10 / PM2.5 | Promedio móvil ponderado de 12 horas (NowCast) | Promedio de 24 horas |
| CO | Promedio móvil de 8 horas | Máximo de los promedios móviles de 8h del día |
| NO2, O3, SO2 | Promedio horario (de 1 hora) | Máximo de los promedios horarios del día |

**¿Por qué PM10/PM2.5 usan un cálculo distinto?** Porque la evidencia de salud para partículas está basada en promedios de 24h, pero eso no permite avisar a la población con oportunidad durante el día. Por eso se usa el "NowCast" (promedio móvil ponderado de 12h), un método desarrollado por la EPA de EE.UU., que aproxima el promedio de 24h pero reacciona más rápido a cambios abruptos.

### 4.1 Fórmula del promedio móvil ponderado de 12h (NowCast) — para PM10 y PM2.5

Pasos (numeral 5.2.5.3 y Anexo A):

1. **Rango** = Cmax − Cmin de las concentraciones horarias de las últimas 12 horas.
2. **Factor de ponderación (w)**: se calcula como `1 − (Rango / Cmax)`.
   - Si `w ≤ 0.5` → se fija W = 0.5.
   - Si `w > 0.5` → se usa W = w, redondeado a 2 decimales.
3. Cada concentración horaria `Ci` se multiplica por `W` elevado a la potencia de cuántas horas atrás fue medida (la hora más reciente es i=1, con exponente 0; la más antigua es i=12, con exponente 11).
4. Se suman esos productos y se dividen entre la suma de los pesos `W^(i-1)` usados, y el resultado se multiplica por un **factor de ajuste** propio de la NOM (distinto para PM10 y PM2.5, detallado en el Anexo A).
5. Se redondea según la regla de PM (ver sección 5 abajo).

**Requisito mínimo de datos**: se necesitan al menos 2 de las 3 horas más recientes; si falta 1 de esas 3, el cálculo continúa; si faltan 2 o más de esas 3, no se calcula el subíndice para esa hora.

Para el dashboard esto significa: si van a mostrar un valor "horario" de PM10/PM2.5, **no es el dato crudo de esa hora**, es este promedio ponderado — hay que implementarlo así para que sea correcto conforme a la norma (el Anexo A trae dos ejemplos numéricos completos, útiles para probar su código).

### 4.2 Reglas de redondeo (numeral 5.2.4)

| Contaminante | Regla |
|---|---|
| O3, NO2, SO2 | Redondear a 3 decimales (ppm); si la 4ª cifra decimal es ≥5, sube la 3ª |
| PM10, PM2.5 | Redondear a entero (µg/m³); si el primer decimal es ≥5, sube el entero |
| CO | Redondear a 2 decimales (ppm); si la 3ª cifra decimal es ≥5, sube la 2ª |

### 4.3 Criterios de completitud de datos (numeral 5.2.5)

| Estadístico | Mínimo de datos requerido |
|---|---|
| Promedio horario | ≥75% de los registros de esa hora (≥45 min de 60) |
| Promedio móvil de 8h (CO) | ≥75% de las horas, es decir mínimo 6 de 8 horas |
| Promedio móvil ponderado de 12h (PM) | ≥2 de las 3 horas más recientes |
| Promedio de 24h | ≥75% de las horas, es decir mínimo 18 de 24 horas |

**Importante para el proyecto**: cuando limpien/agrupen los datos de Miravalle (pandas, Power BI, etc.), estos son los umbrales que deben usar para decidir si un promedio diario/horario es "válido" o si debe marcarse como dato insuficiente, en vez de simplemente promediar lo que haya sin verificar cobertura mínima.

## 5. Clasificación en bandas del Índice AIRE Y SALUD (numeral 5.3, tablas 4–9)

Cinco bandas para todos los contaminantes: **Buena, Aceptable, Mala, Muy Mala, Extremadamente Mala**, con niveles de riesgo asociados: Bajo, Moderado, Alto, Muy Alto, Extremadamente Alto.

### PM10 (µg/m³, promedio móvil ponderado de 12h)

⚠️ La norma establece una entrada en vigor **gradual** para PM10 y PM2.5 con 3 escalones. Como hoy (2026) ya se aplica la columna "a partir de enero de 2026", **esos son los umbrales vigentes que deben usar en el dashboard**:

| Calidad | Riesgo | Al entrar en vigor | Desde enero 2024 | **Desde enero 2026 (vigente hoy)** |
|---|---|---|---|---|
| Buena | Bajo | <45 | <45 | **<45** |
| Aceptable | Moderado | 45–70 | 45–60 | **45–50** |
| Mala | Alto | 70–132 | 60–132 | **50–132** |
| Muy Mala | Muy Alto | 132–213 | 132–213 | **132–213** |
| Extremadamente Mala | Extremadamente Alto | >213 | >213 | **>213** |

### PM2.5 (µg/m³, promedio móvil ponderado de 12h)

| Calidad | Riesgo | Al entrar en vigor | Desde enero 2024 | **Desde enero 2026 (vigente hoy)** |
|---|---|---|---|---|
| Buena | Bajo | <15 | <15 | **<15** |
| Aceptable | Moderado | 15–41 | 15–33 | **15–25** |
| Mala | Alto | 41–79 | 33–79 | **25–79** |
| Muy Mala | Muy Alto | 79–130 | 79–130 | **79–130** |
| Extremadamente Mala | Extremadamente Alto | >130 | >130 | **>130** |

### Ozono O3 (ppm, promedio de 1 hora)

| Calidad | Riesgo | Intervalo |
|---|---|---|
| Buena | Bajo | <0.058 |
| Aceptable | Moderado | 0.058–0.090 |
| Mala | Alto | 0.090–0.135 |
| Muy Mala | Muy Alto | 0.135–0.175 |
| Extremadamente Mala | Extremadamente Alto | >0.175 |

### NO2 (ppm, promedio de 1 hora)

| Calidad | Riesgo | Intervalo |
|---|---|---|
| Buena | Bajo | <0.053 |
| Aceptable | Moderado | 0.053–0.106 |
| Mala | Alto | 0.106–0.160 |
| Muy Mala | Muy Alto | 0.160–0.213 |
| Extremadamente Mala | Extremadamente Alto | >0.213 |

### SO2 (ppm, promedio de 1 hora)

| Calidad | Riesgo | Intervalo |
|---|---|---|
| Buena | Bajo | <0.035 |
| Aceptable | Moderado | 0.035–0.075 |
| Mala | Alto | 0.075–0.185 |
| Muy Mala | Muy Alto | 0.185–0.304 |
| Extremadamente Mala | Extremadamente Alto | >0.304 |

### CO (ppm, promedio móvil de 8 horas)

| Calidad | Riesgo | Intervalo |
|---|---|---|
| Buena | Bajo | <5.00 |
| Aceptable | Moderado | 5.00–9.00 |
| Mala | Alto | 9.00–12.00 |
| Muy Mala | Muy Alto | 12.00–16.00 |
| Extremadamente Mala | Extremadamente Alto | >16.00 |

## 6. Colores oficiales del semáforo (numeral 5.4.3, tablas 10–11)

Para que su dashboard sea fiel a la norma, usen exactamente estos colores (no colores genéricos de semáforo):

| Categoría | Color | RGB | Hex aproximado |
|---|---|---|---|
| Buena | Verde | (0, 228, 0) | #00E400 |
| Aceptable | Amarillo | (255, 255, 0) | #FFFF00 |
| Mala | Naranja | (255, 126, 0) | #FF7E00 |
| Muy Mala | Rojo | (255, 0, 0) | #FF0000 |
| Extremadamente Mala | Morado | (143, 63, 151) | #8F3F97 |
| Fuera de operación / Mantenimiento | Blanco | (255, 255, 255) | #FFFFFF |

Nota: la norma indica que estos valores son sobre escala 0–255 (RGB para pantalla) y también da equivalentes CMYK para impresos, por si necesitan la versión para reportes en PDF.

## 7. Mensajes de riesgo y recomendaciones (numeral 5.4.4, tabla 12)

La norma exige diferenciar el mensaje por **tres grupos poblacionales**: población general, menores de 12 años/gestantes, y personas con enfermedad cardiovascular/respiratoria o mayores de 60. En resumen, la lógica de mensajes por banda es:

- **Buena**: disfrutar actividades al aire libre sin restricción, para todos los grupos.
- **Aceptable**: población general y niños/gestantes pueden actividad normal; personas sensibles (mayores/enfermedad crónica) deben reducir actividad física vigorosa y consultar a su médico si hay síntomas.
- **Mala**: se pide a personas sensibles y a niños/gestantes reducir actividad vigorosa al aire libre; población general puede seguir pero con más descansos si hay síntomas.
- **Muy Mala**: personas sensibles y niños/gestantes deben evitar casi toda actividad al aire libre y preferir espacios interiores libres de humo de tabaco.
- **Extremadamente Mala**: se recomienda permanecer en interiores y reprogramar actividades al aire libre, con atención médica si hay síntomas.

Para el dashboard, esto se traduce en un pequeño bloque de texto/ícono que cambie según la banda vigente, idealmente separado por audiencia (general / sensible).

## 8. Reglas de difusión que aplican a un dashboard (numeral 5.1 y 5.4)

- Se calcula y difunde **por estación de monitoreo** (Miravalle debe tratarse como su propia unidad de análisis, no mezclarse con otras estaciones).
- Reporte horario con un retraso máximo de 15 minutos respecto al cierre de cada hora (esto aplica al sistema oficial en vivo; para su proyecto académico con datos históricos no aplica literal, pero pueden mencionarlo como referencia de "tiempo real" del sistema original).
- El reporte diario toma en cuenta las 24 horas del día anterior.
- Si una estación está fuera de servicio, el índice debe sustituirse por la leyenda **"Fuera de operación"** o **"Mantenimiento"**, no por un valor inventado o vacío — sugerido para el manejo de datos faltantes en su ETL/dashboard.
- Cuando se reporta el estado "de una zona" (agregando estaciones), debe mostrarse el valor que indique **el mayor deterioro** entre las estaciones — es decir, nunca promediar bandas de distintas estaciones para "suavizar" el resultado.

## 9. Por qué estos umbrales son así (Anexo B, para el marco teórico/justificación del proyecto)

Los límites de cada banda no son arbitrarios: se basan en **funciones concentración-respuesta (FCR)** de estudios epidemiológicos (meta-análisis usados por la OMS 2021) que relacionan el incremento de concentración de cada contaminante con el incremento en riesgo relativo de mortalidad. Cada contaminante tiene su propio estudio de referencia y su propio valor de concentración base de comparación (por ejemplo, PM2.5 usa como referencia el valor guía de largo plazo de la OMS de 5 µg/m³). Esto explica por qué los intervalos no son simétricos ni comparables directamente entre contaminantes — es un dato útil si su equipo necesita justificar metodológicamente por qué no se puede promediar o normalizar los 6 contaminantes en una sola escala sin ponderar por riesgo.

## 10. Aplicación práctica sugerida para su equipo (enfoque institución académica, estación Miravalle)

1. **Sprint 1 (un mes de datos)**: implementar el cálculo de concentración base horaria para los contaminantes que mida Miravalle, aplicar redondeo y criterios de completitud, y clasificar cada hora en su banda con el color oficial — esto ya cumple el núcleo del numeral 5.2 y 5.3.
2. **Sprints posteriores (rango anual)**: agregar el reporte diario (máximo/promedio de 24h según contaminante), calcular frecuencia de días por categoría en el periodo, y evaluar cumplimiento como estación de referencia (comparar contra los límites de "Aceptable" que igualan las NOM de salud SSA1).
3. Dado el enfoque de "institución académica", tiene sentido enmarcar el dashboard como una herramienta de **monitoreo epidemiológico/ambiental para investigación y alerta a la comunidad universitaria** (p. ej. recomendaciones de actividad al aire libre en campus, correlación con estudios de salud), usando el lenguaje y mensajes de riesgo tal cual los define la tabla 12.

## 11. Otras normas referenciadas (por si el proyecto pide profundizar)

- **NOM-034/036/037/038-SEMARNAT-1993**: métodos de medición y calibración de CO, O3, NO2 y SO2 respectivamente (relevante si el proyecto pide describir cómo se mide, no solo cómo se calcula el índice).
- **NOM-020/021/022/023/025-SSA1**: normas de salud que definen los límites de exposición por contaminante — los límites superiores de la banda "Aceptable" de la NOM-172 están alineados a estas.
- **NOM-156-SEMARNAT-2012**: establecimiento y operación de sistemas de monitoreo de calidad del aire (útil si quieren describir cómo opera técnicamente una estación como Miravalle).

---

**Fuente primaria completa (texto oficial):** https://sidof.segob.gob.mx/notas/docFuente/5715154
**Copia técnica (INECC/SINAICA, con las imágenes de las fórmulas):** https://sinaica.inecc.gob.mx/archivo/noms/NOM-172-SEMARNAT-2023-Indice-AIRE-y-SALUD.pdf
