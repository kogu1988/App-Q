"use client";

import Link from "next/link";
import { toast } from "sonner";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { BarChart2, ChevronRight, FlaskConical, Lock } from "lucide-react";

interface ModeSelectionProps {
  researchMode: "research" | "ab_test";
  onModeChange: (mode: "research" | "ab_test") => void;
  abTestLocked: boolean;
  onUpgrade: () => void;
  onStart: () => void;
}

/** Arastirma modu secim ekrani (refactor R4-3). */
export function ModeSelection({
  researchMode,
  onModeChange,
  abTestLocked,
  onUpgrade,
  onStart,
}: ModeSelectionProps) {
  return (
  <div className="p-4 sm:p-8 max-w-2xl mx-auto space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-300">
    <div>
      <h1 className="text-3xl font-extrabold tracking-tight">Yeni Araştırma</h1>
      <p className="text-muted-foreground mt-1">Araştırma türünü seçin — Defne sizi yönlendirecek.</p>
    </div>

    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
      <button
        type="button"
        onClick={() => onModeChange("research")}
        className={`flex flex-col gap-3 p-6 rounded-2xl border-2 transition-all text-left ${
          researchMode === "research"
            ? "border-primary bg-pale-green/60  shadow-md"
            : "border-border hover:border-primary dark:hover:border-primary hover:shadow-sm"
        }`}
      >
        <div className={`p-2.5 rounded-xl w-fit ${researchMode === "research" ? "bg-pale-green " : "bg-soft-stone "}`}>
          <BarChart2 size={22} className={researchMode === "research" ? "text-coral" : "text-muted-foreground"} />
        </div>
        <div>
          <div className="font-bold text-base">Pazar Araştırması</div>
          <div className="text-sm text-muted-foreground mt-0.5">Ürün/hizmet fikri doğrulama, hedef kitle ve fiyat araştırması</div>
        </div>
        {researchMode === "research" && (
                        <Badge className="w-fit bg-primary hover:bg-primary text-white text-xs">Seçildi</Badge>
        )}
      </button>

      <button
        type="button"
        onClick={() => {
          if (abTestLocked) {
            toast.error(
              "A/B Test Modu Flex planında kullanılabilir.",
              { action: { label: "Planı Yükselt", onClick: () => onUpgrade() } }
            );
            return;
          }
          onModeChange("ab_test");
        }}
        className={`relative flex flex-col gap-3 p-6 rounded-2xl border-2 transition-all text-left ${
          abTestLocked
            ? "border-border opacity-60 cursor-not-allowed"
            : researchMode === "ab_test"
            ? "border-primary bg-pale-green/60  shadow-md"
            : "border-border hover:border-primary dark:hover:border-primary hover:shadow-sm"
        }`}
      >
        {abTestLocked && (
          <span className="absolute top-3 right-3 inline-flex items-center gap-1 text-[10px] font-bold tracking-wider uppercase bg-amber-100 text-amber-800 px-2 py-0.5 rounded-full">
            <Lock size={9} /> Flex
          </span>
        )}
        <div className={`p-2.5 rounded-xl w-fit ${researchMode === "ab_test" && !abTestLocked ? "bg-pale-green " : "bg-soft-stone "}`}>
          <FlaskConical size={22} className={researchMode === "ab_test" && !abTestLocked ? "text-coral" : "text-muted-foreground"} />
        </div>
        <div>
          <div className="font-bold text-base">A/B Test Simülasyonu</div>
          <div className="text-sm text-muted-foreground mt-0.5">İki farklı mesaj, fiyat veya özellik varyantını karşılaştır</div>
        </div>
        {researchMode === "ab_test" && !abTestLocked && (
                        <Badge className="w-fit bg-primary hover:bg-primary text-white text-xs">Seçildi</Badge>
        )}
      </button>
    </div>

    <Button
      size="lg"
      disabled={researchMode === "ab_test" && abTestLocked}
      onClick={onStart}
      className="w-full gap-2 bg-primary hover:opacity-85 text-white font-medium disabled:opacity-40 disabled:cursor-not-allowed"
    >
      Defne ile Başla
      <ChevronRight size={18} />
    </Button>

    {abTestLocked && researchMode === "ab_test" && (
      <p className="text-center text-xs text-muted-foreground">
        A/B Test modu{" "}
        <Link href="/client/upgrade" className="text-accent underline underline-offset-2 font-medium">Flex planında</Link>
        {" "}kullanılabilir.
      </p>
    )}
  </div>
  );
}
