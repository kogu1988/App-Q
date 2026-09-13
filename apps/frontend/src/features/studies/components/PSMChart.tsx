import type { StudyDetail } from "../types";

/** Van Westendorp PSM (fiyat hassasiyeti) grafiği. Çıktı R1 öncesiyle birebir aynıdır. */
export function PSMChart({ data }: { data: NonNullable<StudyDetail["van_westendorp"]> }) {
  const W = 600, H = 260, PAD = { left: 56, right: 24, top: 16, bottom: 40 };
  const innerW = W - PAD.left - PAD.right;
  const innerH = H - PAD.top - PAD.bottom;

  // Tüm fiyat değerlerini birleştir ve X eksenini belirle
  const allVals = [
    ...data.too_cheap_values,
    ...data.cheap_values,
    ...data.expensive_values,
    ...data.too_expensive_values,
  ];
  const xMin = Math.min(...allVals) * 0.8;
  const xMax = Math.max(...allVals) * 1.15;

  const xScale = (v: number) => PAD.left + ((v - xMin) / (xMax - xMin)) * innerW;

  // Kümülatif dağılım (CDF) hesapla
  function buildCDF(values: number[]): Array<[number, number]> {
    if (!values.length) return [];
    const sorted = [...values].sort((a, b) => a - b);
    const pts: Array<[number, number]> = [];
    // Eksen genişliğinde eşit aralıklı örnek nokta
    const steps = 60;
    for (let i = 0; i <= steps; i++) {
      const x = xMin + (i / steps) * (xMax - xMin);
      const pct = sorted.filter(v => v <= x).length / sorted.length;
      pts.push([x, pct]);
    }
    return pts;
  }

  const cdfTooExpensive = buildCDF(data.too_expensive_values); // Azalan (1 - ...)
  const cdfCheap        = buildCDF(data.cheap_values);
  const cdfExpensive    = buildCDF(data.expensive_values);
  const cdfTooCheap     = buildCDF(data.too_cheap_values);     // Azalan

  function toPolyline(pts: Array<[number, number]>, invert = false): string {
    return pts
      .map(([x, y]) => `${xScale(x).toFixed(1)},${(PAD.top + innerH * (1 - (invert ? 1 - y : y))).toFixed(1)}`)
      .join(" ");
  }

  const yTicks = [0, 25, 50, 75, 100];
  const priceTicks = Array.from({ length: 6 }, (_, i) =>
    Math.round(xMin + (i / 5) * (xMax - xMin))
  );

  const LINES = [
    { pts: toPolyline(cdfTooCheap, true),     color: "#f59e0b", label: "Çok Ucuz",  dash: "4 2" },
    { pts: toPolyline(cdfCheap),               color: "#22c55e", label: "Makul",     dash: "" },
    { pts: toPolyline(cdfExpensive),            color: "#f97316", label: "Pahalı",   dash: "" },
    { pts: toPolyline(cdfTooExpensive, true),  color: "#ef4444", label: "Çok Pahalı", dash: "4 2" },
  ];

  const markers = [
    { x: data.pmc, label: "PMC", color: "#6366f1" },
    { x: data.opp, label: "OPP", color: "#0d9488" },
    { x: data.ipp, label: "IPP", color: "#0ea5e9" },
    { x: data.pme, label: "PME", color: "#ec4899" },
  ];

  return (
    <div className="w-full overflow-x-auto">
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full max-w-2xl" style={{ fontFamily: "inherit" }}>
        {/* Grid lines */}
        {yTicks.map(t => (
          <g key={t}>
            <line
              x1={PAD.left} y1={PAD.top + innerH * (1 - t / 100)}
              x2={PAD.left + innerW} y2={PAD.top + innerH * (1 - t / 100)}
              stroke="#e2e8f0" strokeWidth="1"
            />
            <text x={PAD.left - 6} y={PAD.top + innerH * (1 - t / 100) + 4} textAnchor="end"
              className="fill-[#93939f]" fontSize="10">{t}%</text>
          </g>
        ))}

        {/* X axis ticks */}
        {priceTicks.map(v => (
          <g key={v}>
            <line x1={xScale(v)} y1={PAD.top + innerH} x2={xScale(v)} y2={PAD.top + innerH + 4}
              stroke="#cbd5e1" strokeWidth="1" />
            <text x={xScale(v)} y={PAD.top + innerH + 16} textAnchor="middle"
              className="fill-[#93939f]" fontSize="10">{v.toLocaleString("tr-TR")} ₺</text>
          </g>
        ))}

        {/* Acceptable range band */}
        <rect
          x={xScale(data.pmc)} y={PAD.top}
          width={xScale(data.pme) - xScale(data.pmc)}
          height={innerH}
          fill="#6366f1" fillOpacity="0.06"
        />

        {/* PSM Curves */}
        {LINES.map(l => (
          <polyline key={l.label} points={l.pts}
            fill="none" stroke={l.color} strokeWidth="2"
            strokeDasharray={l.dash || undefined}
            strokeLinecap="round" strokeLinejoin="round" />
        ))}

        {/* Vertical markers */}
        {markers.map(m => (
          <g key={m.label}>
            <line x1={xScale(m.x)} y1={PAD.top} x2={xScale(m.x)} y2={PAD.top + innerH}
              stroke={m.color} strokeWidth="1.5" strokeDasharray="3 3" />
            <rect x={xScale(m.x) - 14} y={PAD.top} width={28} height={16} rx="3"
              fill={m.color} fillOpacity="0.9" />
            <text x={xScale(m.x)} y={PAD.top + 11} textAnchor="middle"
              fill="white" fontSize="9" fontWeight="bold">{m.label}</text>
          </g>
        ))}

        {/* Axes */}
        <line x1={PAD.left} y1={PAD.top} x2={PAD.left} y2={PAD.top + innerH}
          stroke="#94a3b8" strokeWidth="1" />
        <line x1={PAD.left} y1={PAD.top + innerH} x2={PAD.left + innerW} y2={PAD.top + innerH}
          stroke="#94a3b8" strokeWidth="1" />
      </svg>

      {/* Legend */}
      <div className="flex flex-wrap gap-4 mt-2 text-xs">
        {LINES.map(l => (
          <div key={l.label} className="flex items-center gap-1.5">
            <svg width="24" height="10">
              <line x1="0" y1="5" x2="24" y2="5" stroke={l.color} strokeWidth="2"
                strokeDasharray={l.dash || undefined} />
            </svg>
            <span className="text-[#616161] ">{l.label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
