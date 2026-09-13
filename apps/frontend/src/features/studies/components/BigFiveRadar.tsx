import { readTrait } from "../lib/normalize-study";

/** Büyük Beşli kişilik profili radar grafiği. */
export function BigFiveRadar({ bigFive }: { bigFive: Record<string, number> }) {
  const W = 240, H = 240, cx = W / 2, cy = H / 2, R = 82;
  const axes = [
    { label: "Açıklık", value: readTrait(bigFive, "Openness") },
    { label: "Sorumluluk", value: readTrait(bigFive, "Conscientiousness") },
    { label: "Dışadönüklük", value: readTrait(bigFive, "Extraversion") },
    { label: "Uyumluluk", value: readTrait(bigFive, "Agreeableness") },
    { label: "Denge", value: readTrait(bigFive, "Neuroticism") },
  ];
  const N = axes.length;
  const angle = (i: number) => (Math.PI * 2 * i) / N - Math.PI / 2;
  const pt = (i: number, r: number) => [cx + r * Math.cos(angle(i)), cy + r * Math.sin(angle(i))] as const;

  const rings = [0.34, 0.67, 1].map((f, ri) => {
    const pts = Array.from({ length: N }, (_, i) => pt(i, R * f).map(n => n.toFixed(1)).join(",")).join(" ");
    return <polygon key={ri} points={pts} fill="none" stroke="#d9d9dd" strokeWidth="1" />;
  });
  const spokes = Array.from({ length: N }, (_, i) => {
    const [x, y] = pt(i, R);
    return <line key={i} x1={cx} y1={cy} x2={x} y2={y} stroke="#d9d9dd" strokeWidth="1" />;
  });
  const valuePts = Array.from(
    { length: N },
    (_, i) => pt(i, (R * Math.min(100, axes[i].value)) / 100).map(n => n.toFixed(1)).join(",")
  ).join(" ");
  const labels = Array.from({ length: N }, (_, i) => {
    const [x, y] = pt(i, R + 20);
    return (
      <text key={i} x={x} y={y} textAnchor="middle" dominantBaseline="middle" fontSize="9" fill="#616161">
        {axes[i].label}
      </text>
    );
  });

  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full max-w-[220px] mx-auto" role="img" aria-label="Büyük Beşli kişilik radarı">
      {rings}{spokes}
      <polygon points={valuePts} fill="#003c33" fillOpacity="0.22" stroke="#003c33" strokeWidth="2" />
      {labels}
    </svg>
  );
}
