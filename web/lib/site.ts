/**
 * Identidad de la "agencia" del equipo: una institución académica ficticia cercana a la estación.
 * Cambien aquí el nombre y los textos; el resto del sitio los toma de este archivo.
 */
export const ACADEMIA = {
  nombre: "Academia Miravalle",
  siglas: "AM",
  unidad: "Observatorio de Calidad del Aire",
  descripcion:
    "Institución académica cercana a la estación Miravalle. Usamos los datos de SEMADET y la NOM-172-SEMARNAT-2023 para decidir cuándo y cómo realizar actividades al aire libre con nuestra comunidad.",
  comunidad: "estudiantes, docentes y personal",
  equipo: "Equipo 3",
  materia: "Análisis y Visualización de la Información",
  universidad: "Universidad de Guadalajara",
};

export type Sprint = {
  slug: string;
  numero: number;
  titulo: string;
  periodo: string | null; // AAAA-MM procesado por el pipeline
  resumen: string;
  estado: "entregado" | "en curso" | "próximo";
};

/** Registro de entregas. Cada sprint nuevo agrega su fila y su ruta app/sprint-N. */
export const SPRINTS: Sprint[] = [
  {
    slug: "sprint-1",
    numero: 1,
    titulo: "Del dato horario a la información",
    periodo: "2024-03",
    resumen:
      "Marzo 2024: preparación de datos, simulación en tiempo real, numeralia diaria e interpretación para la academia.",
    estado: "entregado",
  },
  {
    slug: "sprint-2",
    numero: 2,
    titulo: "Siguiente periodo",
    periodo: null,
    resumen: "Se amplía el rango de tiempo con el mismo pipeline (--periodo AAAA-MM).",
    estado: "próximo",
  },
];

export const ESTACION = {
  clave: "MIR",
  nombre: "Miravalle",
  coords: "20.6145 N · 103.3434 O",
  altitud: "1 622 msnm",
  red: "SEMADET · Jalisco",
};
