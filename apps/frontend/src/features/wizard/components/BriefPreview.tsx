"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { FileText, Target, Users, DollarSign, Layers, CheckCircle2 } from "lucide-react";
import { toArray } from "../types";
import type { Brief } from "../types";

/** Brief onizleme karti (refactor R4-3). */
export function renderBriefValue(value: unknown) {
  if (!value) return null;
  const strValue = Array.isArray(value) ? value.join(", ") : typeof value === "string" ? value : JSON.stringify(value);
  // Numbered list detection: "1. xxx 2. xxx" or newline-separated
  const numbered = strValue.split(/(?=\d+\.\s)/).map(s => s.replace(/^\d+\.\s*/, "").trim()).filter(Boolean);
  if (numbered.length > 1) {
    return (
      <ul className="space-y-1 mt-0.5">
        {numbered.map((item, i) => (
          <li key={i} className="flex gap-1.5 text-xs text-ink font-medium leading-relaxed">
            <span className="text-coral shrink-0 mt-px">·</span>
            <span className="break-words">{item}</span>
          </li>
        ))}
      </ul>
    );
  }
  return <div className="text-xs text-ink font-medium leading-relaxed break-words whitespace-pre-wrap">{strValue}</div>;
}

export function BriefPreview({ brief, mode, onToggleMobile }: { brief: Brief; mode: "research" | "ab_test"; onToggleMobile?: () => void }) {
  const fields = mode === "ab_test"
    ? [
      { icon: FileText, label: "Başlık", value: brief.title },
      { icon: Target, label: "Ürün Fikri", value: brief.idea },
      { icon: Layers, label: "Varyant A", value: brief.variant_a },
      { icon: Layers, label: "Varyant B", value: brief.variant_b },
      { icon: Users, label: "Hedef Kitle", value: toArray(brief.target_users).join(", ") || undefined },
      { icon: CheckCircle2, label: "Başarı Kriteri", value: brief.success_metric },
    ]
    : [
      { icon: FileText, label: "Başlık", value: brief.title },
      { icon: Target, label: "Ürün Fikri", value: brief.idea },
      { icon: Users, label: "Hedef Kitle", value: toArray(brief.target_users).join(", ") || undefined },
      { icon: DollarSign, label: "Fiyat Modeli", value: brief.expected_price },
      { icon: Layers, label: "Rakipler", value: toArray(brief.competitors).join(", ") || undefined },
      { icon: CheckCircle2, label: "Başarı Kriteri", value: brief.success_metric },
    ];

  const filled = fields.filter(f => f.value && f.value.length > 0).length;
  const total = fields.length;
  const pct = Math.round((filled / total) * 100);

  return (
    <Card className="sticky top-6 shadow-sm border-hairline ">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-bold text-deep-green flex items-center gap-2">
            <FileText size={14} />
            Canlı Brief Özeti
          </CardTitle>
          {onToggleMobile && (
            <button onClick={onToggleMobile} className="lg:hidden text-xs text-deep-green font-bold flex items-center gap-1 bg-pale-green px-2 py-1 rounded-md">
              Sohbete Dön
            </button>
          )}
        </div>
        <div className="flex items-center gap-2 mt-1">
          <div className="flex-1 h-1.5 bg-soft-stone  rounded-full overflow-hidden">
            <div
              className="h-full bg-deep-green rounded-full transition-all duration-500"
              style={{ width: `${pct}%` }}
            />
          </div>
          <span className="text-xs font-bold text-coral/80 tabular-nums">{pct}%</span>
        </div>
      </CardHeader>
      <CardContent className="space-y-2.5">
        {fields.map(({ icon: Icon, label, value }) => (
          <div key={label} className={`flex gap-2 p-2 rounded-lg transition-colors ${value ? "bg-pale-green/50 " : "bg-transparent grayscale"}`}>
            <Icon size={13} className={value ? "text-coral shrink-0 mt-0.5" : "text-muted-text shrink-0 mt-0.5"} />
            <div className="min-w-0 flex-1">
              <div className="text-[10px] font-bold text-muted-foreground uppercase tracking-wide">{label}</div>
              {value
                ? renderBriefValue(value)
                : <div className="text-xs text-muted-text italic">Henüz doldurulmadı</div>
              }
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────────

// ── Araştırma isteği: async job (tercih) → senkron fallback ──

