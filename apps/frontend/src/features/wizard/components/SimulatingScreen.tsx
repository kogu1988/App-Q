"use client";

import { Loader2 } from "lucide-react";

/** Arastirma baslatma (bekleme) ekrani (refactor R4-3). */
export function SimulatingScreen() {
  return (
  <div className="p-4 sm:p-8 max-w-3xl mx-auto space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-300">
    <div>
      <h1 className="text-3xl font-extrabold tracking-tight">Araştırma Başlatılıyor</h1>
      <p className="text-muted-foreground mt-1">Sentetik personalar oluşturuluyor ve mülakatlar yapılıyor...</p>
    </div>
    <div className="flex flex-col items-center justify-center py-16 gap-4">
      <Loader2 size={40} className="animate-spin text-[#ff7759]" />
      <div className="text-[#003c33] font-medium text-lg">Araştırma devam ediyor</div>
      <div className="text-sm text-muted-foreground max-w-md text-center">
        Defne brief&apos;inizi analiz ediyor, personalar oluşturuluyor ve her biriyle mülakat yapılıyor. Bu işlem birkaç saniye sürebilir.
      </div>
    </div>
  </div>
  );
}
