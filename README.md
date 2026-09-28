# Calidad del aire · Miravalle (MIR)

Proyecto de **Análisis y Visualización de la Información** (Equipo 3). Nuestra "agencia" es una institución
académica ficticia, la **Academia Miravalle**, que usa los datos de SEMADET y la **NOM-172-SEMARNAT-2023**
(Índice AIRE Y SALUD) para decidir cuándo y cómo realizar actividades al aire libre.

Cada sprint entrega un **reporte técnico** (una ruta del sitio) y el sitio completo es el **dashboard final**.

**Estado:** Sprint 1 (marzo 2024) entregado → [`docs/sprints/sprint-1.md`](docs/sprints/sprint-1.md).

```
calidad-aire-miravalle/
├─ BD_2024.xlsx         base anual de SEMADET (no se versiona; solo lectura)
├─ pipeline/
│  ├─ etl.py            BD_<AÑO>.xlsx → año limpio y recorte del periodo (con 24 h de calentamiento)
│  ├─ calculos.py       periodo limpio → Archivo1 (horario) y Archivo2 (diario), NOM-172
│  ├─ procesar.py       orquesta los pasos y arma el JSON del sitio, los Excel y el reporte en texto
│  ├─ reporte.py        numeralia en texto para el reporte en Word (reporte_resultados_AAAA-MM.txt)
│  ├─ mapa.py           mapa de Jalisco y catálogo de estaciones SEMADET (hoja Param)
│  ├─ nom172.py         NowCast de referencia, CO 8 h, bandas, redondeo y categorías
│  └─ limpieza.py       perfil, control de calidad y bitácora
├─ tests/               NowCast de la profesora, reglas de categorías y regresión de marzo
├─ data/processed/
│  ├─ miravalle_2024_clean.csv   año limpio (se versiona: permite correr sin BD_2024.xlsx)
│  ├─ estaciones_semadet.csv     catálogo de las 13 estaciones con coordenadas
│  └─ AAAA-MM/          miravalle_<mes><año>_clean.csv, Archivo1, Archivo2, Excel, bitácora y reporte .txt
├─ docs/sprints/        resumen y decisiones de cada entrega
└─ web/                 sitio Next.js (dashboard)
   ├─ app/page.tsx              Observatorio: dashboard final (todos los periodos, abre en el último)
   ├─ app/sprint-1/page.tsx     Reporte técnico 1 (marzo 2024), formato académico
   ├─ app/metodologia/          criterios y cómo crece el proyecto
   ├─ components/               simulación con recorrido guiado, mapa, calendario, gráficas, tablas
   ├─ lib/site.ts               nombre de la academia y registro de sprints
   ├─ data/periodos/*.json      salida del pipeline que lee el sitio
   └─ data/mapa_jalisco.json    geometría del mapa (INEGI) y estaciones
```

## Pipeline (Python)

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python pipeline/procesar.py --periodo 2024-03        # ETL + cálculos + JSON del sitio (usa BD_2024.xlsx si está en la raíz)
python pipeline/etl.py --periodo 2024-03             # solo el ETL
python pipeline/calculos.py --periodo 2024-03        # solo Archivo1 y Archivo2
python pipeline/reporte.py --periodo 2024-03         # solo el reporte en texto para Word
python pipeline/mapa.py                              # regenera el mapa (descarga los límites de INEGI la primera vez)
python -m pytest tests
```

`BD_2024.xlsx` va en la raíz y no se versiona (~9 MB). Si no está, el pipeline usa el año limpio ya versionado.

### Criterios NOM-172 aplicados (resumen)

| Contaminante | Indicador horario | Indicador diario | Bandas (límite superior Buena / Aceptable / Mala / Muy Mala) |
|---|---|---|---|
| PM₁₀ | NowCast 12 h (factor 0.714) | Promedio 24 h, entero | 45 / 60 / 132 / 213 µg/m³ |
| PM₂.₅ | NowCast 12 h (factor 0.694) | Promedio 24 h, entero | 15 / 33 / 79 / 130 µg/m³ |
| O₃ | Valor horario | Máximo horario, 3 decimales | 0.058 / 0.090 / 0.135 / 0.175 ppm |
| CO | Promedio móvil 8 h (≥ 6 de 8) | Máximo del promedio 8 h, 2 decimales | 5 / 9 / 12 / 16 ppm |

Partículas: columna «a partir de enero de 2024» de las tablas 4 y 5 (fecha de los datos). Suficiencia diaria: 18 de 24 h.
Redondeo half-up (numeral 5.2.4). Colores RGB de la tabla 11 y mensajes de la tabla 12 para tres grupos de población.

## Sitio (Next.js)

```bash
cd web
npm install
npm run dev          # http://localhost:3000
npm run build        # verificación antes de subir
```

### Vercel
Importar el repositorio en vercel.com y en **Settings → Build & Deployment → Root Directory** poner `web`.
Framework: Next.js (se detecta solo). Cada rama y cada pull request obtiene su propio enlace de vista previa;
`main` es producción.

## Flujo de trabajo por sprint

| Paso | Comando / acción |
|---|---|
| 1. Rama del sprint | `git switch -c sprint-2` |
| 2. Nuevo periodo | `python pipeline/procesar.py --periodo 2024-04` |
| 3. Nueva ruta | copiar `web/app/sprint-1` a `web/app/sprint-2` y agregar la fila en `web/lib/site.ts` |
| 4. Revisión | pull request → enlace de preview en Vercel |
| 5. Entrega | merge a `main` y `git tag sprint-2 && git push --tags` |

Las entregas pasadas no se tocan: su ruta y su tag quedan como evidencia de lo entregado.
