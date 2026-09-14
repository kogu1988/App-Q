"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { ResearchPlan } from "../types";

interface ScriptTabProps {
  plan?: ResearchPlan;
}

/** Mülakat senaryosu sekmesi (refactor R2-3). */
export function ScriptTab({ plan }: ScriptTabProps) {
  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-2 duration-300">
      <div>
        <h2 className="text-xl font-bold text-primary dark:text-white">Mülakat Senaryosu</h2>
        <p className="text-muted-foreground text-sm">Yapay zeka moderatörünün personalara yönelttiği ana sorular.</p>
      </div>

      {(!plan?.interview_questions || plan.interview_questions.length === 0) ? (
        <div className="text-center py-12 text-muted-foreground border border-dashed border-border rounded-xl">
          Bu araştırmaya ait senaryo kaydı bulunamadı.
        </div>
      ) : (
        <Card className="shadow-sm border-border-light dark:border-action-blue/15 overflow-hidden">
          <CardHeader className="bg-muted-surface/50 dark:bg-ink/50 border-b border-border">
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-base">Mülakat Akışı</CardTitle>
                <CardDescription>Toplam {plan.interview_questions.length} soru kalıbı kullanıldı.</CardDescription>
              </div>
              <Badge variant="outline" className="bg-white dark:bg-primary">
                Salt Okunur (Read-Only)
              </Badge>
            </div>
          </CardHeader>
          <CardContent className="p-0">
            <div className="divide-y divide-border/60">
              {plan.interview_questions.map((q: string, i: number) => (
                <div key={i} className="flex gap-4 p-5 hover:bg-muted-surface dark:hover:bg-ink/30 transition-colors">
                  <div className="h-6 w-6 rounded-full bg-pale-blue dark:bg-dark-navy text-action-blue dark:text-focus-blue flex items-center justify-center font-bold text-xs shrink-0 mt-0.5">
                    {i + 1}
                  </div>
                  <div className="space-y-2 flex-1">
                    <p className="text-sm font-medium text-ink dark:text-border-light leading-relaxed">{q}</p>
                    <div className="flex gap-2">
                      <Badge variant="secondary" className="text-[10px] bg-soft-stone dark:bg-surface-dark text-body-muted">Açık Uçlu Soru</Badge>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
