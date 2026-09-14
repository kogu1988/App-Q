"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { InterviewTranscriptDialog } from "./InterviewTranscriptDialog";
import type { PersonaInterview, StudyDetail } from "../types";

interface InterviewsTabProps {
  interviews: PersonaInterview[];
  study: StudyDetail;
  planType: string;
  followUpText: string;
  onFollowUpTextChange: (value: string) => void;
  sendingFollowUp: boolean;
  onFollowUp: (personaId: string) => void;
}

/** Mülakat kayıtları sekmesi (refactor R2-4). */
export function InterviewsTab({
  interviews,
  study,
  planType,
  followUpText,
  onFollowUpTextChange,
  sendingFollowUp,
  onFollowUp,
}: InterviewsTabProps) {
  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-2 duration-300">
      <div>
        <h2 className="text-xl font-bold text-primary dark:text-white">Mülakat Transkriptleri</h2>
        <p className="text-muted-foreground text-sm">Yapay zeka moderatörü ve sentetik personalar arasında geçen tüm diyaloglar.</p>
      </div>

      {interviews.length === 0 ? (
        <div className="text-center py-12 text-muted-foreground border border-dashed border-border rounded-xl">
          Bu araştırmaya ait mülakat kaydı bulunamadı.
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
          {interviews.map((item: PersonaInterview, idx: number) => (
            <Card key={idx} className="shadow-sm border hover:border-border-light dark:hover:border-action-blue/[0.175] hover:shadow-md transition-all duration-300">
              <CardHeader className="p-5 pb-3">
                <div className="flex justify-between items-start">
                  <div>
                    <CardTitle className="text-base">{item.persona?.name}</CardTitle>
                    <CardDescription className="text-xs">{item.persona?.role_title || "Sentetik Tüketici"} • {item.persona?.age} Yaş</CardDescription>
                  </div>
                  <Badge variant="outline" className="text-[10px] bg-muted-surface dark:bg-ink">{item.turns?.length} Soru</Badge>
                </div>
              </CardHeader>
              <CardContent className="p-5 pt-0 space-y-4">
                <div className="text-xs text-muted-foreground flex items-center justify-between">
                  <span>Durum:</span>
                  <Badge className="bg-emerald-50 text-emerald-700 dark:bg-emerald-950/20 dark:text-emerald-400">Mülakat Tamamlandı</Badge>
                </div>
                <InterviewTranscriptDialog
                  interview={item}
                  study={study}
                  planType={planType}
                  followUpText={followUpText}
                  onFollowUpTextChange={onFollowUpTextChange}
                  sendingFollowUp={sendingFollowUp}
                  onFollowUp={onFollowUp}
                />
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
