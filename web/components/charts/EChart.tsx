"use client";
import { useEffect, useRef } from "react";
import * as echarts from "echarts/core";
import { BarChart, CustomChart, LineChart } from "echarts/charts";
import {
  AxisPointerComponent, GridComponent, LegendComponent, MarkAreaComponent, MarkLineComponent,
  TitleComponent, TooltipComponent,
} from "echarts/components";
import { CanvasRenderer } from "echarts/renderers";

echarts.use([BarChart, LineChart, CustomChart, GridComponent, TooltipComponent, LegendComponent, TitleComponent,
  MarkAreaComponent, MarkLineComponent, AxisPointerComponent, CanvasRenderer]);

type Props = {
  option: echarts.EChartsCoreOption | null;
  height: number | string;
  className?: string;
  ariaLabel: string;
  replace?: boolean;
  onReady?: (chart: echarts.ECharts) => void;
};

export function EChart({ option, height, className, ariaLabel, replace = false, onReady }: Props) {
  const ref = useRef<HTMLDivElement>(null);
  const chart = useRef<echarts.ECharts | null>(null);

  useEffect(() => {
    if (!ref.current) return;
    const c = echarts.init(ref.current, undefined, { renderer: "canvas" });
    chart.current = c;
    onReady?.(c);
    const ro = new ResizeObserver(() => c.resize());
    ro.observe(ref.current);
    return () => { ro.disconnect(); c.dispose(); chart.current = null; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (chart.current && option) chart.current.setOption(option, { notMerge: replace, lazyUpdate: true });
  }, [option, replace]);

  useEffect(() => { chart.current?.resize(); }, [height]);

  return <div ref={ref} role="img" aria-label={ariaLabel} className={className} style={{ height, width: "100%" }} />;
}
