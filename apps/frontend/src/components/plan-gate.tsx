"use client";

import { Lock } from "lucide-react";
import Link from "next/link";

interface PlanGateProps {
  /** Kullanıcının mevcut planı */
  currentPlan: string;
  /** Bu özellik için minimum gerekli plan */
  requiredPlan: string;
  /** Kilitli olduğunda gösterilecek içerik (placeholder) */
  children: React.ReactNode;
  /** Özelliğin adı (kullanıcıya gösterilir) */
  featureName?: string;
  /** Kompakt mod — tam overlay yerine küçük badge */
  compact?: boolean;
}

const PLAN_ORDER = ["Free", "Flex", "Starter", "Pro", "Enterprise"];

export function PlanGate({
  currentPlan,
  requiredPlan,
  children,
  featureName,
  compact = false,
}: PlanGateProps) {
  const currentIdx = PLAN_ORDER.indexOf(currentPlan);
  const requiredIdx = PLAN_ORDER.indexOf(requiredPlan);
  const isLocked = currentIdx < requiredIdx;

  if (!isLocked) return <>{children}</>;

  if (compact) {
    return (
      <div className="relative inline-flex items-center gap-1.5 opacity-60 cursor-not-allowed select-none">
        {children}
        <span className="inline-flex items-center gap-1 text-xs font-medium bg-amber-100 text-amber-800 px-1.5 py-0.5 rounded-full">
          <Lock size={10} />
          {requiredPlan}
        </span>
      </div>
    );
  }

  return (
    <div className="relative rounded-lg overflow-hidden">
      {/* Bulanık arka plan — gerçek içeriği gösterir ama erişilemez yapar */}
      <div className="opacity-30 pointer-events-none select-none blur-[2px]">
        {children}
      </div>

      {/* Overlay */}
      <div className="absolute inset-0 flex flex-col items-center justify-center gap-3 bg-background/60 backdrop-blur-sm rounded-lg border border-dashed border-border">
        <div className="flex items-center justify-center w-10 h-10 rounded-full bg-muted">
          <Lock size={18} className="text-muted-foreground" />
        </div>
        <div className="text-center px-4">
          <p className="text-sm font-semibold text-foreground">
            {featureName ? `"${featureName}" ${requiredPlan} planında` : `${requiredPlan} planı gerekiyor`}
          </p>
          <p className="text-xs text-muted-foreground mt-1">
            Mevcut planınız: <span className="font-medium">{currentPlan}</span>
          </p>
        </div>
        <Link
          href="/client/upgrade"
          className="inline-flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-md bg-accent text-accent-foreground hover:opacity-90 transition-opacity"
        >
          Planı Yükselt →
        </Link>
      </div>
    </div>
  );
}
