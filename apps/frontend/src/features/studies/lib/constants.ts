import type { ComponentType } from "react";
import { Ship, GitBranch, AlertTriangle, Trash2 } from "lucide-react";

/** Karar sinyali (decision layer) görsel yapılandırması. */
export interface DecisionConfigEntry {
  icon: ComponentType<{ size?: number; className?: string }>;
  color: string;
  bg: string;
  label: string;
}

export const DECISION_CONFIG: Record<string, DecisionConfigEntry> = {
  SHIP: { icon: Ship, color: "text-emerald-700", bg: "bg-emerald-50 border-emerald-200", label: "Yayınla" },
  ITERATE: { icon: GitBranch, color: "text-amber-700", bg: "bg-amber-50 border-amber-200", label: "İyileştir" },
  INVESTIGATE: { icon: AlertTriangle, color: "text-sky-700", bg: "bg-sky-50 border-sky-200", label: "Araştır" },
  KILL: { icon: Trash2, color: "text-red-700", bg: "bg-red-50 border-red-200", label: "Vazgeç" },
};

/** Duruş (stance) etiketlerinin Türkçe karşılıkları. */
export const STANCE_TR: Record<string, string> = {
  "Champion": "Öncü",
  "Pragmatist": "Pragmatist",
  "Observer": "Gözlemci",
  "Skeptic": "Şüpheci",
  "Blocker": "Engelleyici",
  "Innovator": "Öncü",
  "EarlyAdopter": "Erken Benimseyen",
  "Mainstream": "Ana Akım",
  "Laggard": "Geciken",
};
