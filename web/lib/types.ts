export type Mensaje = { general: string; menores_gestantes: string; sensibles: string };

export type Valor = string | number | boolean | null;

export type HourRec = {
  t: string;
  Cat_global: string;
  Responsable: string;
  Cambio_categoria: boolean;
  [k: string]: Valor;
};

export type DayRec = {
  FECHA: string;
  dia_semana: string;
  Cat_global: string;
  Responsable: string;
  evento: string | null;
  evento_sigla: string | null;
  [k: string]: Valor;
};

export type Variable = {
  variable: string; nombre: string; unidad: string; tipo: string;
  validos: number; faltantes: number; disponibilidad: number;
  min: number | null; mediana: number | null; max: number | null; dias_con_datos: number;
};

export type Bitacora = {
  fecha_hora: string; variable: string; valor: number | null; regla: string;
  clasificacion: string; accion: string; detalle: string;
};

export type PeriodoSim = {
  inicio: string; fin: string; cambios: number; horas_mala_o_peor: number; peor: string;
  contaminantes_responsables: number; criterio: string;
  ranking: { inicio: string; cambios: number; peor: string; horas_mala: number; contaminantes: number }[];
};

export type Maximo = {
  variable: string; tipo: "max" | "min"; valor: number; fecha_hora: string; otras_horas: string[];
  categoria: string | null; cat_global: string;
};

export type Numeralia = {
  dias_mes: number;
  dias_con_categoria: number;
  dias_sin_datos: string[];
  dias_por_categoria: Record<string, number>;
  dias_por_responsable: Record<string, number>;
  horas_con_categoria: number;
  horas_por_categoria: Record<string, number>;
  horas_por_responsable: Record<string, number>;
  suficiencia: Record<string, number>;
  dias_mas_desfavorables: { fecha: string; categoria: string; responsable: string; indicador: number; unidad: string; horas_mala_o_peor: number }[];
  horario_vs_diario: { dias_con_horas_peores: number; horas_peores_total: number; dias_peor_horaria_distinta: number; dias_responsable_distinto: number; cambios_categoria_total: number };
  maximos?: Maximo[];
};

export type PeriodoData = {
  periodo: { clave: string; nombre: string; inicio: string; fin: string; calentamiento: string };
  estacion: { clave: string; nombre: string; contaminantes: string[]; meteorologia: string[] };
  bandas: Record<string, number[]>;
  unidades: Record<string, string>;
  categorias: string[];
  riesgo: Record<string, string>;
  indicador_horario: Record<string, string>;
  indicador_diario: Record<string, string>;
  /** Tabla 12 de la NOM: mensajes para tres grupos poblacionales. */
  mensajes: Record<string, Mensaje>;
  /** Tabla 10 de la NOM: descripción del riesgo para la población en general y la sensible. */
  descripcion_riesgo?: Record<string, { general: string; sensible: string }>;
  perfil: {
    registros: number; registros_esperados: number; timestamps_faltantes: string[]; duplicados: number;
    hora_convencion: string; hora_consistente: boolean; variables: Variable[];
    faltantes_por_dia: Record<string, number[]>; formato: string[];
  };
  bitacora: Bitacora[];
  horario: HourRec[];
  diario: DayRec[];
  numeralia: Numeralia;
  periodo_simulacion: PeriodoSim;
  perfil_diurno: Record<string, (number | null)[]>;
  categorias_por_hora: Record<string, number[]>;
  metodologia: { Elemento: string; Criterio: string }[];
};

export type IndicePeriodo = {
  periodo: string; nombre: string; inicio: string; fin: string;
  dias_con_categoria: number; categoria_predominante: string;
};

/** Paquete de datos que reciben los componentes interactivos. */
export type SimPayload = Pick<PeriodoData,
  "horario" | "diario" | "periodo_simulacion" | "mensajes" | "descripcion_riesgo" | "riesgo" | "unidades" | "bandas" | "indicador_horario">;
