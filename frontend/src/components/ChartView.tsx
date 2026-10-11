import { useEffect, useRef } from "react";
import * as echarts from "echarts";
import { Download, Maximize2 } from "lucide-react";

interface Props {
  option: Record<string, unknown>;
}

export default function ChartView({ option }: Props) {
  const ref = useRef<HTMLDivElement>(null);
  const chartRef = useRef<echarts.ECharts | null>(null);

  useEffect(() => {
    if (!ref.current) return;
    const chart = echarts.init(ref.current, undefined, { renderer: "canvas" });
    chartRef.current = chart;
    chart.setOption(option);
    const onResize = () => chart.resize();
    window.addEventListener("resize", onResize);
    return () => {
      window.removeEventListener("resize", onResize);
      chart.dispose();
    };
  }, [option]);

  const enlarg = () => {
    const url = chartRef.current?.getDataURL({ pixelRatio: 2, backgroundColor: "#0B1220" });
    if (!url) return;
    const ov = document.createElement("div");
    ov.className = "lb-overlay";
    const img = document.createElement("img");
    img.src = url;
    ov.appendChild(img);
    ov.addEventListener("click", () => ov.remove());
    document.body.appendChild(ov);
  };

  const download = () => {
    const url = chartRef.current?.getDataURL({ pixelRatio: 2, backgroundColor: "#0B1220" });
    if (!url) return;
    const a = document.createElement("a");
    a.href = url;
    a.download = "chatbi-chart.png";
    a.click();
  };

  return (
    <div className="relative mt-3 rounded-xl border border-white/5 bg-ink-900/40 p-2">
      <div className="absolute right-3 top-3 z-10 flex gap-2">
        <button
          onClick={download}
          title="导出图片"
          className="rounded-lg bg-white/5 p-1.5 text-txt-mid transition hover:bg-white/10 hover:text-txt-hi"
        >
          <Download size={15} />
        </button>
        <button
          onClick={enlarg}
          title="放大"
          className="rounded-lg bg-white/5 p-1.5 text-txt-mid transition hover:bg-white/10 hover:text-txt-hi"
        >
          <Maximize2 size={15} />
        </button>
      </div>
      <div ref={ref} className="h-[320px] w-full" />
    </div>
  );
}
