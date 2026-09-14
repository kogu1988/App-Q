import type { StudyDetail } from "../types";

/** Kanal keşif dağılımı bar grafiği. Çıktı R1 öncesiyle birebir aynıdır. */
export function ChannelBarChart({ data }: { data: NonNullable<StudyDetail["channel_map"]> }) {
  if (!data.length) return null;
  const maxCount = Math.max(...data.map(d => d.count));
  const COLORS = [
    "var(--color-series-1)", "var(--color-series-2)", "var(--color-series-3)",
    "var(--color-series-4)", "var(--color-series-5)", "var(--color-series-6)",
    "var(--color-series-7)",
  ];
  return (
    <div className="space-y-2.5">
      {data.map((row, i) => (
        <div key={row.channel} className="flex items-center gap-3">
          <span className="text-xs font-medium text-body-muted w-40 shrink-0 truncate">{row.channel}</span>
          <div className="flex-1 bg-soft-stone rounded-full h-2.5 overflow-hidden">
            <div
              className="h-full rounded-full transition-all duration-700"
              style={{ width: `${(row.count / maxCount) * 100}%`, backgroundColor: COLORS[i % COLORS.length] }}
            />
          </div>
          <span className="text-xs font-bold tabular-nums w-10 text-right" style={{ color: COLORS[i % COLORS.length] }}>
            %{row.pct}
          </span>
        </div>
      ))}
    </div>
  );
}
